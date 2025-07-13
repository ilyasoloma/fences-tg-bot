from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, BufferedInputFile

from src.config import config
from src.keyboards import user_messages_keyboard, main_menu, back_to_board_keyboard
from src.services import FencesService
from src.utils.logger import logger
from src.utils.static import prepared_msg_file

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


@router.callback_query(F.data == "download_messages")
async def download_messages(callback: CallbackQuery, state: FSMContext, service: FencesService):
    username = callback.from_user.username
    board = await service.get_messages_by_username(username)
    if not board:
        await callback.message.answer(config.EMPTY_BOARD)
        await callback.message.answer(config.START_CMD, reply_markup=await main_menu(username, service=service))
        await state.clear()
        return

    file_content = prepared_msg_file(board)

    file_data = file_content.getvalue().encode('utf-8')
    file = BufferedInputFile(file_data, filename=f"messages_{username}.txt")

    await callback.message.answer_document(file, caption="Ваши сообщения")
    await callback.answer()
    file_content.close()
    logger.info("User %s downloaded messages file", username)

    await callback.message.answer(config.NO_EMPTY_BOARD, reply_markup=await user_messages_keyboard(board))
