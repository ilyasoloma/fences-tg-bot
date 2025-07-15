from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import config
from src.keyboards.general_keyboards import main_menu, message_keyboard, cancel_sending_keyboard
from src.keyboards.write_keyboards import recipient_keyboard, entry_alias_keyboard, back_keyboard
from src.services import FencesService
from src.states import Wall
from src.utils.logger import logger
from src.utils.static import validate_alias

router = Router()


@router.callback_query(F.data == "write")
async def select_recipient(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        if service.is_expired():
            logger.info("User %s attempted to write, but bot is expired", callback.from_user.username)
            await callback.message.edit_text(config.MSG_EOL_DATETIME,
                                             reply_markup=await main_menu(callback.from_user.username, service=service))
            await callback.answer()
            return
        logger.info("User %s started writing process", callback.from_user.username)
        await callback.message.edit_text(config.MSG_SELECT_RECIPIENT,
                                         reply_markup=await recipient_keyboard(service, callback.from_user.username))
        await state.set_state(Wall.choosing_recipient)
        await callback.answer()
    except Exception as e:
        logger.error("Error in select_recipient for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(Wall.choosing_recipient)
async def enter_alias(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        await state.update_data(recipient=callback.data)
        await state.set_state(Wall.entering_alias)
        await callback.message.edit_text(config.MSG_WRITE_ALIAS, reply_markup=entry_alias_keyboard())
        await callback.answer()
    except Exception as e:
        logger.error("Error in enter_alias for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(Wall.entering_alias, F.data == "use_label")
async def use_label_as_alias(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        username = callback.from_user.username
        recipient_label = (await state.get_data()).get("recipient")

        label, error = await service.get_user_label(username)
        if error:
            logger.warning("Error retrieving label for user %s: %s", username, error)
            await callback.message.edit_text(f"⚠️ {error}\n\nПожалуйста, введите псевдоним вручную.",
                                             reply_markup=entry_alias_keyboard())
            await callback.answer()
            return

        is_unique, unique_error = await service.check_alias_unique(recipient_label, label)
        if not is_unique:
            logger.warning("Duplicate alias: %s for recipient %s", label, recipient_label)
            await callback.message.edit_text(f"⚠️ {unique_error}\n\nПожалуйста, введите другой псевдоним.",
                                             reply_markup=entry_alias_keyboard())
            await callback.answer()
            return

        await state.update_data(alias=label)
        await state.set_state(Wall.typing_message)
        await callback.message.edit_text(config.MSG_ENTER_MESSAGE, reply_markup=back_keyboard())
        logger.info("User %s used label '%s' as alias for recipient %s", username, label, recipient_label)
        await callback.answer()
    except Exception as e:
        logger.error("Error in use_label_as_alias for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.message(Wall.entering_alias)
async def enter_message(msg: Message, state: FSMContext, service: FencesService):
    try:
        if msg.text is None:
            await msg.answer(config.MSG_ERROR_EMPTY_TEXT)
            await msg.answer(config.MSG_WRITE_ALIAS, reply_markup=entry_alias_keyboard())
            logger.warning("Invalid alias content from user %s", msg.from_user.username)
            return

        slug = msg.text.strip()
        valid, error = validate_alias(slug)
        if not valid:
            await msg.answer(f"⚠️ {error}")
            await msg.answer(config.MSG_WRITE_ALIAS, reply_markup=entry_alias_keyboard())
            logger.warning("Invalid slug: %s from user %s", error, msg.from_user.username)
            return

        data = await state.get_data()
        recipient_label = data.get("recipient")
        is_unique, unique_error = await service.check_alias_unique(recipient_label, slug)
        if not is_unique:
            await msg.answer(f"⚠️ {unique_error}\n\nПожалуйста, введите другой псевдоним.")
            await msg.answer(config.MSG_WRITE_ALIAS, reply_markup=entry_alias_keyboard())
            logger.warning("Duplicate alias: %s for recipient %s", slug, recipient_label)
            return

        await state.update_data(alias=msg.text)
        await state.set_state(Wall.typing_message)
        await msg.answer(config.MSG_ENTER_MESSAGE, reply_markup=back_keyboard())
    except Exception as e:
        logger.error("Error in enter_message for user %s: %s", msg.from_user.username, str(e))
        await state.clear()
        await msg.answer(config.MSG_UNKNOWING_ERROR,
                         reply_markup=await main_menu(msg.from_user.username, service=service))


@router.message(Wall.typing_message)
async def collect_text(msg: Message, state: FSMContext, service: FencesService):
    try:
        if msg.text is None:
            await msg.answer(config.MSG_ERROR_EMPTY_TEXT)
            await msg.answer(config.MSG_ENTER_MESSAGE, reply_markup=message_keyboard())
            logger.warning("Invalid message content from user %s", msg.from_user.username)
            return

        data = await state.get_data()
        messages = data.get("messages", [])
        messages.append(msg.text)
        await state.update_data(messages=messages)
        await msg.answer(config.MSG_ADDED_CHUNK, reply_markup=message_keyboard())
    except Exception as e:
        logger.error("Error in collect_text for user %s: %s", msg.from_user.username, str(e))
        await state.clear()
        await msg.answer(config.MSG_UNKNOWING_ERROR,
                         reply_markup=await main_menu(msg.from_user.username, service=service))


@router.callback_query(Wall.typing_message, F.data == "save")
async def save_messages(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        data = await state.get_data()
        parts = data.get("messages", [])

        if not parts:
            await callback.message.answer(config.MSG_EMPTY_MESSAGE)
            await callback.answer()
            return

        success, error = await service.save_board(recipient_label=data["recipient"],
                                                  chunks=parts,
                                                  sender_alias=data["alias"],
                                                  sender_username=callback.from_user.username)
        if not success:
            logger.error("Error saving message for user %s: %s", callback.from_user.username, error)
            await state.clear()
            await callback.message.answer(f"⚠️ {error}",
                                          reply_markup=await main_menu(callback.from_user.username, service=service))
            await callback.answer()
            return

        logger.info("Sent full message to %s from %s", data["recipient"], callback.from_user.username)
        label, _ = await service.get_user_label(username=callback.from_user.username)
        await callback.message.edit_text(config.MSG_MESSAGE_SENT)
        await state.clear()
        await callback.message.answer(f'{label}, {config.MSG_START}',
                                      reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()
    except Exception as e:
        logger.error("Error in save_messages for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.answer(config.MSG_UNKNOWING_ERROR,
                                      reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(Wall.typing_message, F.data == "cancel")
async def cancel_sending_messages(callback: CallbackQuery):
    await callback.message.answer(config.MSG_WARNING_LEAVE, reply_markup=cancel_sending_keyboard())
    await callback.answer()


@router.callback_query(Wall.typing_message, F.data == "collect_msg")
async def back_to_typing(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(config.MSG_ENTER_MESSAGE, reply_markup=message_keyboard())
    await state.set_state(Wall.typing_message)
    await callback.answer()


@router.callback_query(Wall.typing_message, F.data == "try_cancel")
async def cancel_sending_messages_confirm(callback: CallbackQuery, state: FSMContext, service: FencesService):
    await state.clear()
    label, _ = await service.get_user_label(username=callback.from_user.username)
    await callback.message.edit_text(f'{label}, {config.MSG_START}',
                                     reply_markup=await main_menu(callback.from_user.username, service=service))
    await callback.answer()
