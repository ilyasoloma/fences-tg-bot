from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import config
from src.keyboards.admin_keyboards import choose_user_to_remove_keyboard, bot_message_type_keyboard, \
    bot_message_recipient_keyboard, admin_panel_keyboard
from src.keyboards.general_keyboards import main_menu, message_keyboard, cancel_sending_keyboard
from src.services import FencesService
from src.states import AdminState
from src.utils.logger import logger
from src.utils.static import validate_alias

router = Router()


@router.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        if not await service.is_admin(callback.from_user.username):
            logger.warning("User %s attempted to access admin panel without permission", callback.from_user.username)
            await callback.message.answer("❌ У вас нет прав администратора.")
            await callback.answer()
            return

        await callback.message.edit_text(config.MSG_MAIN_CONTROL_PANEL, reply_markup=admin_panel_keyboard())
        await state.set_state(AdminState.choosing_action)
        await callback.answer()
    except Exception as e:
        logger.error("Error in admin_panel for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.choosing_action, F.data == "admin_add")
async def ask_username(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        await callback.message.edit_text(config.MSG_ENTER_ADD_USERNAME)
        await state.set_state(AdminState.adding_username)
        await callback.answer()
    except Exception as e:
        logger.error("Error in ask_username for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.message(AdminState.adding_username)
async def ask_alias(msg: Message, state: FSMContext, service: FencesService):
    try:
        await state.update_data(username=msg.text.strip())
        await msg.answer(config.MSG_ENTER_ADD_ALIAS)
        await state.set_state(AdminState.adding_label)
    except Exception as e:
        logger.error("Error in ask_alias for user %s: %s", msg.from_user.username, str(e))
        await state.clear()
        await msg.answer(config.MSG_UNKNOWING_ERROR,
                         reply_markup=await main_menu(msg.from_user.username, service=service))


@router.message(AdminState.adding_label)
async def save_new_user(msg: Message, state: FSMContext, service: FencesService):
    try:
        await msg.answer(config.MSG_ADDING_USER)
        data = await state.get_data()
        username = data["username"]
        label = msg.text.strip()

        valid, error = validate_alias(label)
        if not valid:
            await msg.answer(f"⚠️ {error}")
            await msg.answer(config.MSG_ENTER_ADD_ALIAS)
            return

        success, err = await service.add_user(username, label, role='member')
        if not success:
            await msg.answer(f"⚠️ {err}")
            await msg.answer(config.MSG_ENTER_ADD_ALIAS)
            return

        await msg.answer(f"✅ Пользователь @{username} добавлен", reply_markup=admin_panel_keyboard())
        await state.set_state(AdminState.choosing_action)
    except Exception as e:
        logger.error("Error in save_new_user for user %s: %s", msg.from_user.username, str(e))
        await state.clear()
        await msg.answer(config.MSG_UNKNOWING_ERROR,
                         reply_markup=await main_menu(msg.from_user.username, service=service))


@router.callback_query(AdminState.choosing_action, F.data == "admin_remove_member")
async def list_users_to_remove(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        users, error = await service.get_users(role='all')
        if error:
            logger.error("Error retrieving users for removal: %s", error)
            await callback.message.edit_text(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        if not users:
            await callback.message.edit_text("❌ Нет участников для удаления", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await callback.message.edit_text("Выберите пользователя для удаления:",
                                         reply_markup=await choose_user_to_remove_keyboard(service, role='all'))
        await state.set_state(AdminState.removing_user)
        await callback.answer()
    except Exception as e:
        logger.error("Error in list_users_to_remove for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.removing_user, F.data.startswith("rm_user:"))
async def confirm_user_removal(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        label = callback.data.split(":", 1)[1]
        success, error = await service.remove_user(label)
        if not success:
            logger.error("Error removing user %s: %s", label, error)
            await callback.message.edit_text(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await callback.message.edit_text(f"✅ Пользователь {label} удалён.", reply_markup=admin_panel_keyboard())
        await state.set_state(AdminState.choosing_action)
        await callback.answer()
    except Exception as e:
        logger.error("Error in confirm_user_removal for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.choosing_action, F.data == "add_root")
async def list_users_to_add_root(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        users, error = await service.get_users(role='member')
        if error:
            logger.error("Error retrieving users for add_root: %s", error)
            await callback.message.edit_text(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        if not users:
            await callback.message.edit_text("❌ Все пользователи уже админы", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await callback.message.edit_text("Выберите будущего админа",
                                         reply_markup=await choose_user_to_remove_keyboard(service, role='member'))
        await state.set_state(AdminState.add_root)
        await callback.answer()
    except Exception as e:
        logger.error("Error in list_users_to_add_root for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.choosing_action, F.data == "delete_root")
async def list_users_to_remove_root(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        users, error = await service.get_users(role='admin')
        if error:
            logger.error("Error retrieving admins for delete_root: %s", error)
            await callback.message.edit_text(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        if not users:
            await callback.message.edit_text("❌ Нет админов для снятия прав", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await callback.message.edit_text("Выберите бывшего админа",
                                         reply_markup=await choose_user_to_remove_keyboard(service, role='admin'))
        await state.set_state(AdminState.delete_root)
        await callback.answer()
    except Exception as e:
        logger.error("Error in list_users_to_remove_root for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.add_root, F.data.startswith("rm_user:"))
async def confirm_user_root(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        alias = callback.data.split(":", 1)[1]
        success, error = await service.set_admin_flag(alias=alias, admin_flag=True)
        if not success:
            logger.error("Error setting admin flag for %s: %s", alias, error)
            await callback.message.edit_text(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await callback.message.edit_text(f"✅ {alias} теперь админ.", reply_markup=admin_panel_keyboard())
        await state.set_state(AdminState.choosing_action)
        await callback.answer()
    except Exception as e:
        logger.error("Error in confirm_user_root for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.delete_root, F.data.startswith("rm_user:"))
async def delete_user_root(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        alias = callback.data.split(":", 1)[1]
        success, error = await service.set_admin_flag(alias=alias, admin_flag=False)
        if not success:
            logger.error("Error unsetting admin flag for %s: %s", alias, error)
            await callback.message.edit_text(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await callback.message.edit_text(f"✅ {alias} теперь обычный участник.", reply_markup=admin_panel_keyboard())
        await state.set_state(AdminState.choosing_action)
        await callback.answer()
    except Exception as e:
        logger.error("Error in delete_user_root for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(F.data == 'set_datetime')
async def set_datetime_handler(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        await callback.message.edit_text(config.MSG_SET_DATETIME)
        await state.set_state(AdminState.set_datetime)
        await callback.answer()
    except Exception as e:
        logger.error("Error in set_datetime_handler for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.message(AdminState.set_datetime)
async def success_set_datetime(msg: Message, state: FSMContext, service: FencesService):
    try:
        await msg.answer('Применение...')
        success, error = await service.set_datetime(msg.text)
        if not success:
            await msg.answer(f"⚠️ {error}")
            await msg.answer(config.MSG_SET_DATETIME)
            return

        await msg.answer(f'Время действия бота изменено на: {msg.text}', reply_markup=admin_panel_keyboard())
        await state.set_state(AdminState.choosing_action)
    except Exception as e:
        logger.error("Error in success_set_datetime for user %s: %s", msg.from_user.username, str(e))
        await state.clear()
        await msg.answer(config.MSG_UNKNOWING_ERROR,
                         reply_markup=await main_menu(msg.from_user.username, service=service))


@router.callback_query(AdminState.choosing_action, F.data == "send_bot_message")
async def choose_bot_message_type(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        if not await service.is_admin(callback.from_user.username):
            logger.warning("User %s attempted to send bot message without permission", callback.from_user.username)
            await callback.message.answer("❌ У вас нет прав администратора.")
            await callback.answer()
            return

        await callback.message.edit_text("Кому отправить сообщение от бота?", reply_markup=bot_message_type_keyboard())
        await state.set_state(AdminState.bot_message_type)
        await callback.answer()
    except Exception as e:
        logger.error("Error in choose_bot_message_type for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.bot_message_type, F.data == "bot_message_all")
async def bot_message_all(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        await callback.message.edit_text("Введите сообщение (текст, фото, видео, стикер и т.д.):",
                                         reply_markup=message_keyboard())
        await state.set_state(AdminState.bot_message_typing)
        await state.update_data(bot_recipient=None, bot_messages=[])
        await callback.answer()
    except Exception as e:
        logger.error("Error in bot_message_all for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.bot_message_type, F.data == "bot_message_single")
async def choose_bot_message_recipient(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        contacts, error = await service.get_users(return_field='dict')
        if error:
            logger.error("Error retrieving contacts for bot message: %s", error)
            await callback.message.edit_text(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        if not contacts:
            await callback.message.edit_text("❌ Нет пользователей для отправки сообщения.",
                                             reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await callback.message.edit_text("Выберите получателя:",
                                         reply_markup=await bot_message_recipient_keyboard(service))
        await state.set_state(AdminState.bot_message_recipient)
        await callback.answer()
    except Exception as e:
        logger.error("Error in choose_bot_message_recipient for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.bot_message_recipient, F.data.startswith("bot_recipient:"))
async def bot_message_single(callback: CallbackQuery, state: FSMContext, service: FencesService):
    try:
        recipient_label = callback.data.split(":", 1)[1]
        contacts, error = await service.get_users(return_field='dict')
        if error:
            logger.error("Error retrieving contacts for bot message: %s", error)
            await callback.message.edit_text(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        if recipient_label not in contacts:
            logger.warning("Recipient %s not found for bot message", recipient_label)
            await callback.message.edit_text(f"❌ Получатель {recipient_label} не найден.",
                                             reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await state.update_data(bot_recipient=recipient_label, bot_messages=[])
        await callback.message.edit_text(
            f"Введите сообщение (текст, фото, видео, стикер и т.д.) для {recipient_label}:",
            reply_markup=message_keyboard())
        await state.set_state(AdminState.bot_message_typing)
        await callback.answer()
    except Exception as e:
        logger.error("Error in bot_message_single for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.message(AdminState.bot_message_typing)
async def collect_bot_message(msg: Message, state: FSMContext, service: FencesService):
    try:
        data = await state.get_data()
        messages = data.get("bot_messages", [])

        if msg.text:
            message_data = {"type": "text", "content": msg.text}
        elif msg.photo:
            message_data = {"type": "photo", "content": msg.photo[-1].file_id, "caption": msg.caption}
        elif msg.video:
            message_data = {"type": "video", "content": msg.video.file_id, "caption": msg.caption}
        elif msg.video_note:
            message_data = {"type": "video_note", "content": msg.video_note.file_id}
        elif msg.audio:
            message_data = {"type": "audio", "content": msg.audio.file_id, "caption": msg.caption}
        elif msg.sticker:
            message_data = {"type": "sticker", "content": msg.sticker.file_id}
        elif msg.document:
            message_data = {"type": "document", "content": msg.document.file_id, "caption": msg.caption}
        elif msg.voice:
            message_data = {"type": "voice", "content": msg.voice.file_id}
        else:
            await msg.answer(
                "❌ Неподдерживаемый тип сообщения. Отправьте текст, фото, видео, стикер, аудио или документ.")
            await msg.answer("Введите сообщение:", reply_markup=message_keyboard())
            logger.warning("Unsupported message type from %s", msg.from_user.username)
            return

        messages.append(message_data)
        await state.update_data(bot_messages=messages)
        await msg.answer("✏️ Сообщение добавлено. Продолжай отправлять или нажми «💾 Сохранить».",
                         reply_markup=message_keyboard())
    except Exception as e:
        logger.error("Error in collect_bot_message for user %s: %s", msg.from_user.username, str(e))
        await state.clear()
        await msg.answer(config.MSG_UNKNOWING_ERROR,
                         reply_markup=await main_menu(msg.from_user.username, service=service))


@router.callback_query(AdminState.bot_message_typing, F.data == "save")
async def send_bot_direct_message(callback: CallbackQuery, state: FSMContext, service: FencesService, bot: Bot):
    try:
        data = await state.get_data()
        messages = data.get("bot_messages", [])
        if not messages:
            await callback.message.answer("❌ Сообщение пустое. Отправьте хотя бы одно сообщение.",
                                          reply_markup=admin_panel_keyboard())
            logger.warning("Empty bot message from %s", callback.from_user.username)
            await state.set_state(AdminState.choosing_action)
            return

        recipient_label = data.get("bot_recipient")
        success, error = await service.send_bot_direct_message(bot, recipient_label, messages)
        target = "всем пользователям" if recipient_label is None else f"пользователю {recipient_label}"
        if not success:
            logger.error("Error sending bot message to %s: %s", target, error)
            await callback.message.answer(f"⚠️ {error}", reply_markup=admin_panel_keyboard())
            await state.set_state(AdminState.choosing_action)
            return

        await callback.message.answer(f"✅ Сообщение от бота отправлено {target}.", reply_markup=admin_panel_keyboard())
        logger.info("Sent bot message to %s from %s", target, callback.from_user.username)
        await state.set_state(AdminState.choosing_action)
        await callback.answer()
    except Exception as e:
        logger.error("Error in send_bot_direct_message for user %s: %s", callback.from_user.username, str(e))
        await state.clear()
        await callback.message.edit_text(config.MSG_UNKNOWING_ERROR,
                                         reply_markup=await main_menu(callback.from_user.username, service=service))
        await callback.answer()


@router.callback_query(AdminState.bot_message_typing, F.data == "cancel")
async def cancel_sending_messages(callback: CallbackQuery):
    await callback.message.answer(config.MSG_WARNING_LEAVE, reply_markup=cancel_sending_keyboard())
    await callback.answer()


@router.callback_query(AdminState.bot_message_typing, F.data == "collect_msg")
async def back_to_typing(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    recipient_label = data.get("bot_recipient")
    text = "Введите сообщение (текст, фото, видео, стикер и т.д.):" if recipient_label is None \
        else f"Введите сообщение (текст, фото, видео, стикер и т.д.) для {recipient_label}:"
    await callback.message.answer(text, reply_markup=message_keyboard())
    await state.set_state(AdminState.bot_message_typing)
    await callback.answer()


@router.callback_query(AdminState.bot_message_typing, F.data == "try_cancel")
async def confirm_cancel_sending_messages(callback: CallbackQuery, state: FSMContext, service: FencesService):
    await state.clear()
    await callback.message.edit_text(config.MSG_MAIN_CONTROL_PANEL, reply_markup=admin_panel_keyboard())
    await state.set_state(AdminState.choosing_action)
