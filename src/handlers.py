from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.config import config
from src.keyboards import cancel_sending_keyboard, back_recipient, board_keyboard, back_to_board_keyboard
from src.keyboards import main_menu, recipient_keyboard, back_keyboard, message_keyboard
from src.services import is_allowed, save_board, load_board, validate_alias
from src.states import Wall
from src.utils.logger import logger

router = Router()


@router.message(F.text == "/start")
async def start_cmd(msg: Message):
    await msg.answer(config.START_CMD, reply_markup=main_menu())


@router.callback_query(F.data == "write")
async def write_entry(callback: CallbackQuery, state: FSMContext):
    if not await is_allowed(callback.from_user.username):
        await callback.message.edit_text(config.ACCESS_DENIED)
        return
    await state.set_state(Wall.selecting_recipient)
    await callback.message.edit_text(config.SELECT_RECIPIENT, reply_markup=await recipient_keyboard())


@router.callback_query(Wall.selecting_recipient)
async def select_recipient(callback: CallbackQuery, state: FSMContext):
    if callback.data == "back":
        await callback.message.edit_text(config.START_CMD, reply_markup=main_menu())
        await state.clear()
        return
    await state.update_data(recipient=callback.data)
    await state.set_state(Wall.entering_alias)
    await callback.message.edit_text(config.WRITE_ALIAS, reply_markup=back_keyboard())


@router.callback_query(Wall.entering_alias, F.data == "back")
async def back_to_recipient(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Wall.selecting_recipient)
    await callback.message.edit_text(config.SELECT_RECIPIENT, reply_markup=await recipient_keyboard())


@router.message(Wall.entering_alias)
async def enter_message(msg: Message, state: FSMContext):
    if msg.text is None:
        await msg.answer(config.ERROR_EMPTY_TEXT)
        await msg.answer(config.WRITE_ALIAS, reply_markup=back_keyboard())
        logger.warning("Invalid alias content")
        return

    slug = msg.text.strip()
    valid, error = validate_alias(slug)
    if not valid:
        await msg.answer(f"⚠️ {error}", reply_markup=back_keyboard())
        await msg.answer(config.WRITE_ALIAS, reply_markup=back_keyboard())
        logger.warning("Invalid slug: %s", error)
        return

    await state.update_data(alias=msg.text)
    await state.set_state(Wall.typing_message)
    await msg.answer(config.ENTER_MESSAGE, reply_markup=back_keyboard())


@router.callback_query(Wall.typing_message, F.data == "back")
async def back_to_alias(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Wall.entering_alias)
    await callback.message.edit_text(config.WRITE_ALIAS, reply_markup=back_keyboard())


@router.message(Wall.typing_message)
async def collect_text(msg: Message, state: FSMContext):
    if msg.text is None:
        await msg.answer(config.ERROR_EMPTY_TEXT)
        await msg.answer(config.ENTER_MESSAGE, reply_markup=back_keyboard())
        logger.warning("Invalid message content")
        return
    data = await state.get_data()
    messages = data.get("messages", [])
    messages.append(msg.text)
    await state.update_data(messages=messages)
    await msg.answer(config.ADDED_CHUNK, reply_markup=message_keyboard())


@router.callback_query(Wall.typing_message, F.data == "save")
async def save_messages(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    parts = data.get("messages", [])

    if not parts:
        await callback.message.answer(config.EMPTY_MSG)
        return

    await save_board(data["recipient"], data["alias"], parts)
    logger.info("User %s sent full message to %s", callback.from_user.username, data["recipient"])
    await callback.message.answer(config.MESSAGE_SENT)
    await callback.message.answer(config.START_CMD, reply_markup=main_menu())
    await state.clear()


@router.callback_query(Wall.typing_message, F.data == "cancel")
async def cancel_sending_messages(callback: CallbackQuery):
    await callback.message.answer(config.WARNING_LEAVE_MSG, reply_markup=cancel_sending_keyboard())
    await callback.answer()


@router.callback_query(Wall.typing_message, F.data == "collect_msg")
async def back_to_typing(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(config.ENTER_MESSAGE, reply_markup=message_keyboard())
    await state.set_state(Wall.typing_message)
    await callback.answer()


@router.callback_query(F.data == "view")
async def view_entries(callback: CallbackQuery):
    username = callback.from_user.username
    board = await load_board(username)
    if not board:
        await callback.message.answer(config.EMPTY_BOARD)
        await callback.message.answer(config.START_CMD, reply_markup=main_menu())
        return

    markup = await board_keyboard(board)
    await callback.message.edit_text(config.NO_EMPTY_BOARD, reply_markup=markup)


@router.callback_query(Wall.typing_message, F.data == "main")
async def exit_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(config.START_CMD, reply_markup=main_menu())
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("view:"))
async def show_board_message(callback: CallbackQuery):
    username = callback.from_user.username
    board = await load_board(username)
    alias = callback.data.split("view:", 1)[1]

    if alias not in board:
        await callback.message.answer("❌ Сообщение не найдено.")
        return

    chunks = board[alias]
    if not isinstance(chunks, list):
        chunks = [str(chunks)]

    for chunk in chunks:
        await callback.message.answer(chunk)

    await callback.message.answer(
        f"{config.EOL_BOARD} {alias}",
        reply_markup=back_to_board_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(config.START_CMD, reply_markup=main_menu())


@router.callback_query()
async def show_message(callback: CallbackQuery):
    username = callback.from_user.username
    board = load_board(username)
    if callback.data in board.keys():
        for chunk in board[callback.data]:
            await callback.message.answer(chunk)
        await callback.message.answer(f"{config.EOL_BOARD} {callback.data}", reply_markup=back_recipient())


@router.message()
async def fallback_handler(msg: Message):
    await msg.answer(config.UNKNOWING_ERROR)
    await msg.answer(config.START_CMD, reply_markup=main_menu())
    logger.warning("Unknown message from %s: %s", msg.from_user.username, msg.text)
