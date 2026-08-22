from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import routers
from app.models import Role, User, UserRole
from app.utils.auth import get_password_hash
import os

UPLOAD_DIR = "/app/uploads"


def init_roles():
    """初始化系统角色"""
    db = SessionLocal()
    try:
        default_roles = [
            ("admin", "管理员", "拥有系统所有权限"),
            ("operator", "运营", "负责物料管理、库存调整、生产订单的创建和发布"),
            ("worker", "工人", "负责领取生产订单、开工、报工"),
            ("sales", "销售", "负责销售订单相关操作"),
            ("shipping", "发货", "负责发货相关操作"),
        ]
        created_any = False
        for code, name, desc in default_roles:
            existing = db.query(Role).filter(Role.code == code).first()
            if not existing:
                db.add(Role(code=code, name=name, description=desc))
                created_any = True

        # 如果是首次初始化（roles 表原本为空），给现有用户分配 admin 角色
        if created_any and not db.query(Role).count() > len(default_roles):
            users = db.query(User).all()
            for user in users:
                existing_role = (
                    db.query(UserRole)
                    .filter(UserRole.user_id == user.id, UserRole.role_code == "admin")
                    .first()
                )
                if not existing_role:
                    db.add(UserRole(user_id=user.id, role_code="admin"))

        db.commit()
    finally:
        db.close()


def init_default_admin():
    """首次启动时检查系统中是否有超级管理员，没有则创建默认 admin / passwd"""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.is_superuser == True).first()
        if existing:
            return
        admin = User(
            username="admin",
            hashed_password=get_password_hash("passwd"),
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


def migrate_customer_info():
    """迁移：将 customer_name + customer_address 合并到 customer_info，并清理旧结构"""
    db = SessionLocal()
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(engine)

        # 检查 sales_orders 表是否有 customer_name 列（需要迁移的旧结构标志）
        cols = [c["name"] for c in inspector.get_columns("sales_orders")]

        if "customer_name" in cols:
            # 1. 添加 customer_info 列
            if "customer_info" not in cols:
                db.execute(text("ALTER TABLE sales_orders ADD COLUMN customer_info TEXT"))

            # 2. 迁移数据
            db.execute(text(
                "UPDATE sales_orders SET customer_info = TRIM(COALESCE(customer_name, '') || ' ' || COALESCE(customer_address, ''))"
            ))

            # 3. 删除旧列
            db.execute(text("ALTER TABLE sales_orders DROP COLUMN IF EXISTS customer_id"))
            db.execute(text("ALTER TABLE sales_orders DROP COLUMN IF EXISTS customer_name"))
            db.execute(text("ALTER TABLE sales_orders DROP COLUMN IF EXISTS customer_address"))

        # 4. 删除 customers 表（如果存在）
        if "customers" in inspector.get_table_names():
            db.execute(text("DROP TABLE IF EXISTS customers CASCADE"))

        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.path.join(UPLOAD_DIR, "images"), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    init_roles()
    init_default_admin()
    migrate_customer_info()
    yield
    pass


app = FastAPI(
    title="ProductDB",
    description="""
    ## 功能模块
    
    - 🔧 **物料管理**: 物料基础信息、分类管理
    - 📦 **BOM管理**: 产品物料清单，支持多层级的BOM树

    - 📝 **销售订单**: 销售订单的全流程管理
    - 🏭 **生产订单**: 生产订单及物料需求计算
    - 📊 **库存管理**: 实时库存、库存流水、低库存预警
    
    ## 认证
    
    所有接口（除登录外）都需要在Header中添加:
    ```
    Authorization: Bearer <token>
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
if os.path.exists(UPLOAD_DIR):
    app.mount("/api/v1/uploads", StaticFiles(directory=os.path.join(UPLOAD_DIR, "images")), name="uploads")

# 注册路由
for router in routers:
    app.include_router(router, prefix="/api/v1")


# 前端静态文件（合并 web 容器到 api 容器）
WEB_DIST = "/app/web/dist"
if os.path.exists(WEB_DIST):
    # 静态资源（带 hash 的 js/css）
    if os.path.exists(os.path.join(WEB_DIST, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(WEB_DIST, "assets")), name="web_assets")

    # SPA 所有非 API 路径返回 index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(WEB_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(WEB_DIST, "index.html"))

    # 根路径
    @app.get("/")
    async def root_spa():
        return FileResponse(os.path.join(WEB_DIST, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "message": "ProductDB API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)