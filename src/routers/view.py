from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, BufferedInputFile

from src.config import config
from src.keyboards.general_keyboards import main_menu
from src.keyboards.view_keyboards import user_messages_keyboard, back_to_board_keyboard
from src.services import FencesService
from src.utils.logger import logger
from src.utils.static import prepared_msg_file

router = Router()


@router.callback_query(F.data == "view")
async def view_messages(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        username = callback.from_user.username
        label, _ = await service.get_user_label(username=username)
        board = await service.get_messages_by_username(username)
        if not board:
            logger.info("User %s has no messages on their board", username)
            await callback.message.answer(config.MSG_EMPTY_BOARD)
            await callback.message.answer(f"{label}, {config.START_CMD}", reply_markup=await main_menu(username, service=service))
            await state.clear()
            return

        logger.info("User %s viewed their message board", username)
        await callback.message.edit_text(config.MSG_NO_EMPTY_BOARD, reply_markup=await user_messages_keyboard(board))
        await callback.answer()
    except Exception as e:
        logger.error("Error in view_messages for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(F.data.startswith("view:"))
async def show_board_message(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        username = callback.from_user.username
        board = await service.get_messages_by_username(username)
        alias = callback.data.split("view:", 1)[1]

        if alias not in board:
            logger.warning("Message not found for alias %s by user %s", alias, username)
            await callback.message.answer("❌ Сообщение не найдено.")
            await state.clear()
            await callback.message.answer(config.MSG_START, reply_markup=await main_menu(username, service=service))
            return

        for chunk in board[alias]:
            await callback.message.answer(chunk)

        await callback.message.answer(f"{config.MSG_EOL_BOARD} {alias}", reply_markup=back_to_board_keyboard())
        await callback.answer()
    except Exception as e:
        logger.error("Error in show_board_message for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(F.data == "download_messages")
async def download_messages(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        username = callback.from_user.username
        label, _ = await service.get_user_label(username=username)
        board = await service.get_messages_by_username(username)
        if not board:
            logger.info("User %s has no messages to download", username)
            await callback.message.answer(config.MSG_EMPTY_BOARD)
            await callback.message.answer(f'{label}, {config.MSG_START}',
                                          reply_markup=await main_menu(username, service=service))
            await state.clear()
            return

        file_content = prepared_msg_file(board)
        file_data = file_content.getvalue().encode('utf-8')
        file = BufferedInputFile(file_data, filename=f"messages_{username}.txt")

        await callback.message.answer_document(file, caption="Ваши сообщения")
        await callback.answer()
        file_content.close()
        logger.info("User %s downloaded messages file", username)

        await callback.message.answer(config.MSG_NO_EMPTY_BOARD, reply_markup=await user_messages_keyboard(board))
        await callback.answer()
    except Exception as e:
        logger.error("Error in download_messages for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.answer(config.MSG_UNKNOWING_ERROR,
                                      reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()
