from aiogram import Router
from src.routers.common import router as common_router
from src.routers.write import router as write_router
from src.routers.view import router as view_router
from src.routers.admin import router as admin_router

router = Router()
router.include_router(common_router)
router.include_router(write_router)
router.include_router(view_router)
router.include_router(admin_router)
