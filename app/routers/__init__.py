from . import auth, material, bom, sales_order, production_order, inventory, image, users

routers = [
    auth.router,
    material.router,
    material.category_router,
    bom.router,
    sales_order.router,
    production_order.router,
    inventory.router,
    image.router,
    users.router,
]

__all__ = ["routers"]