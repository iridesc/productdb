from app.routers import auth, material, bom, customer, sales_order, production_order, inventory

routers = [
    auth.router,
    material.router,
    material.category_router,
    bom.router,
    customer.router,
    sales_order.router,
    production_order.router,
    inventory.router,
]

__all__ = ["routers"]