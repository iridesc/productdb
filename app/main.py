from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routers import routers
import os

UPLOAD_DIR = "/app/uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.path.join(UPLOAD_DIR, "images"), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield
    pass


app = FastAPI(
    title="ERP 物料生产管理系统",
    description="""
    ## 功能模块
    
    - 🔧 **物料管理**: 物料基础信息、分类管理
    - 📦 **BOM管理**: 产品物料清单，支持多层级的BOM树
    - 👥 **客户管理**: 客户信息维护
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


@app.get("/")
def root():
    return {
        "message": "ERP 物料生产管理系统 API",
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