from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import config
from src.keyboards import recipient_keyboard, message_keyboard, back_keyboard, main_menu, cancel_sending_keyboard
from src.services import FencesService
from src.states import Wall
from src.utils.logger import logger
from src.utils.static import validate_alias

router = Router()


@router.callback_query(F.data == "write")
async def select_recipient(callback: CallbackQuery, state: FSMContext, service: FencesService):
    await callback.message.edit_text(config.SELECT_RECIPIENT, reply_markup=await recipient_keyboard(service=service))
    await state.set_state(Wall.choosing_recipient)


@router.callback_query(Wall.choosing_recipient)
async def enter_alias(callback: CallbackQuery, state: FSMContext):
    await state.update_data(recipient=callback.data)
    await state.set_state(Wall.entering_alias)
    await callback.message.edit_text(config.WRITE_ALIAS, reply_markup=back_keyboard())


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
        logger.warning("Invalid slug: %s", error)
        return

    await state.update_data(alias=msg.text)
    await state.set_state(Wall.typing_message)
    await msg.answer(config.ENTER_MESSAGE, reply_markup=back_keyboard())


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
async def save_messages(callback: CallbackQuery, state: FSMContext, service: FencesService):
    data = await state.get_data()
    parts = data.get("messages", [])

    if not parts:
        await callback.message.answer(config.EMPTY_MSG)
        return

    await service.save_board(data["recipient"], data["alias"], parts)
    logger.info("User %s sent full message to %s", callback.from_user.username, data["recipient"])
    await callback.message.answer(config.MESSAGE_SENT)
    await state.clear()
    await callback.message.answer(config.START_CMD, reply_markup=await main_menu(callback.from_user.username,
                                                                                 service=service))


@router.callback_query(Wall.typing_message, F.data == "cancel")
async def cancel_sending_messages(callback: CallbackQuery):
    await callback.message.answer(config.WARNING_LEAVE_MSG, reply_markup=cancel_sending_keyboard())
    await callback.answer()


@router.callback_query(Wall.typing_message, F.data == "collect_msg")
async def back_to_typing(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(config.ENTER_MESSAGE, reply_markup=message_keyboard())
    await state.set_state(Wall.typing_message)
    await callback.answer()


@router.callback_query(Wall.typing_message, F.data == "try_cancel")
async def cancel_sending_messages(callback: CallbackQuery, state: FSMContext, service: FencesService):
    await state.clear()
    await callback.message.edit_text(config.START_CMD, reply_markup=await main_menu(callback.from_user.username,
                                                                                    service=service))
