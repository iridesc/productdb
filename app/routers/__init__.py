from . import auth, material, bom, sales_order, production_order, inventory, image, users, system_tokens

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
    system_tokens.router,
]

__all__ = ["routers"]
