from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.config import config
from src.keyboards.general_keyboards import main_menu, main_menu_reply_keyboard
from src.services import FencesService
from src.utils.logger import logger

router = Router()


@router.message(F.text.in_({"/start", "🏠 Главное меню"}))
async def start_cmd(msg: Message, service: FencesService, state: FSMContext):
    username = msg.from_user.username
    chat_id = msg.chat.id
    label = await service.get_user_label(username=username)
    # Обновляем chat_id для существующего пользователя
    success = await service.repo.update_user_chat_id(username, chat_id)
    if not success:
        await msg.answer("⚠️ Не удалось обновить chat_id. Попробуйте снова или обратитесь к администратору.")
        logger.warning("Failed to update chat_id for user %s", username)
        return

    # Очищаем состояние и показываем главное меню
    await state.clear()
    logger.info("User %s accessed main menu, chat_id %s", username, chat_id)
    await msg.answer("Привет!", reply_markup=main_menu_reply_keyboard())
    await msg.answer(f"{label}, {config.START_CMD}", reply_markup=await main_menu(username, service=service))


@router.callback_query(F.data == "back")
async def back_main_menu(callback: CallbackQuery, state: FSMContext, service: FencesService):
    await state.clear()
    await callback.message.edit_text(config.START_CMD,
                                     reply_markup=await main_menu(callback.from_user.username, service=service))
    await callback.answer()
