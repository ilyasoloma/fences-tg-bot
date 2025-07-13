from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.config import config
from src.keyboards import user_messages_keyboard, main_menu, back_to_board_keyboard
from src.services import FencesService

router = Router()


@router.callback_query(F.data == "view")
async def view_messages(callback: CallbackQuery, state: FSMContext, service: FencesService):
    username = callback.from_user.username
    board = await service.get_messages_by_username(username)
    if not board:
        await callback.message.answer(config.EMPTY_BOARD)
        await callback.message.answer(config.START_CMD, reply_markup=await main_menu(username, service=service))
        await state.clear()
        return

    await callback.message.edit_text(config.NO_EMPTY_BOARD, reply_markup=await user_messages_keyboard(board))


@router.callback_query(F.data.startswith("view:"))
async def show_board_message(callback: CallbackQuery, state: FSMContext, service: FencesService):
    username = callback.from_user.username
    board = await service.get_messages_by_username(username)
    alias = callback.data.split("view:", 1)[1]

    if alias not in board:
        await callback.message.answer("❌ Сообщение не найдено.")
        await state.clear()
        return

    for chunk in board[alias]:
        await callback.message.answer(chunk)

    await callback.message.answer(f"{config.EOL_BOARD} {alias}", reply_markup=back_to_board_keyboard())
    await callback.answer()
