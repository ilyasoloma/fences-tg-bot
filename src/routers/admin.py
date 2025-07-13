from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import config
from src.keyboards import admin_panel_keyboad, choose_user_to_remove_keyboard
from src.services import FencesService
from src.states import AdminState
from src.utils.static import validate_alias

router = Router()


@router.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery, state: FSMContext, service: FencesService):
    if not await service.is_admin(callback.from_user.username):
        await callback.message.answer("❌ У вас нет прав администратора.")
        return

    await callback.message.edit_text(config.MAIN_CONTROL_PANEL, reply_markup=admin_panel_keyboad())
    await state.set_state(AdminState.choosing_action)


@router.callback_query(AdminState.choosing_action, F.data == "admin_add")
async def ask_username(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(config.ENTER_ADD_USERNAME)
    await state.set_state(AdminState.adding_username)


@router.message(AdminState.adding_username)
async def ask_alias(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text.strip())
    await msg.answer(config.ENTER_ADD_ALIAS)
    await state.set_state(AdminState.adding_label)


@router.message(AdminState.adding_label)
async def save_new_user(msg: Message, state: FSMContext, service: FencesService):
    await msg.answer(config.ADDING_USER)
    data = await state.get_data()
    username = data["username"]
    label = msg.text.strip()

    valid, error = validate_alias(label)
    if not valid:
        await msg.answer(f"⚠️ {error}")
        return

    success, err = await service.add_user(username, label, role='member')
    if not success:
        await msg.answer(err)
        return

    await msg.answer(f"✅ Пользователь @{username} добавлен", reply_markup=admin_panel_keyboad())
    await state.set_state(AdminState.choosing_action)


@router.callback_query(AdminState.choosing_action, F.data == "admin_remove_member")
async def list_users_to_remove(callback: CallbackQuery, state: FSMContext, service: FencesService):
    usernames = await service.get_users_by_role('all')

    if not usernames:
        await callback.message.edit_text(f"❌ Нет участников для удаления")
        await state.clear()
        return

    await callback.message.edit_text("Выберите пользователя для удаления:",
                                     reply_markup=await choose_user_to_remove_keyboard(usernames))
    await state.set_state(AdminState.removing_user)


@router.callback_query(AdminState.removing_user, F.data.startswith("rm_user:"))
async def confirm_user_removal(callback: CallbackQuery, state: FSMContext, service: FencesService):
    username = callback.data.split(":", 1)[1]
    await service.remove_user(username)
    await callback.message.answer(f"✅ Пользователь @{username} удалён.", reply_markup=admin_panel_keyboad())
    await state.set_state(AdminState.choosing_action)


@router.callback_query(AdminState.choosing_action, F.data == "add_root")
async def list_users_to_add_root(callback: CallbackQuery, state: FSMContext, service: FencesService):
    usernames = await service.get_users_by_role('member')

    if not usernames:
        await callback.message.edit_text(f"❌ У тебя все админы")
        await state.clear()
        await callback.message.answer(config.MAIN_CONTROL_PANEL, reply_markup=admin_panel_keyboad())
        return

    await callback.message.edit_text("Выберите будущего админа",
                                     reply_markup=await choose_user_to_remove_keyboard(usernames))
    await state.set_state(AdminState.add_root)


@router.callback_query(AdminState.choosing_action, F.data == "delete_root")
async def list_users_to_remove_root(callback: CallbackQuery, state: FSMContext, service: FencesService):
    usernames = await service.get_users_by_role('admin')

    if not usernames:
        await callback.message.edit_text(f"❌ У тебя все участники")
        await state.clear()
        return

    await callback.message.edit_text("Выберите бывшего админа",
                                     reply_markup=await choose_user_to_remove_keyboard(usernames))
    await state.set_state(AdminState.delete_root)


@router.callback_query(AdminState.add_root, F.data.startswith("rm_user:"))
async def confirm_user_root(callback: CallbackQuery, state: FSMContext, service: FencesService):
    alias = callback.data.split(":", 1)[1]
    await service.set_admin_flag(alias=alias, admin_flag=True)
    await callback.message.answer(f"✅ {alias} теперь админ.", reply_markup=admin_panel_keyboad())
    await state.set_state(AdminState.choosing_action)


@router.callback_query(AdminState.delete_root, F.data.startswith("rm_user:"))
async def delete_user_root(callback: CallbackQuery, state: FSMContext, service: FencesService):
    alias = callback.data.split(":", 1)[1]
    await service.set_admin_flag(alias=alias, admin_flag=False)
    await callback.message.answer(f"✅ {alias} теперь обычный участник.", reply_markup=admin_panel_keyboad())
    await state.set_state(AdminState.choosing_action)


@router.callback_query(F.data == 'set_datetime')
async def set_datetime_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(config.SET_DATETIME_MSG)
    await state.set_state(AdminState.set_datetime)


@router.message(AdminState.set_datetime)
async def success_set_datetime(msg: Message, state: FSMContext, service: FencesService):
    await msg.answer('Применение...')
    success = await service.set_datetime(msg.text)
    if not success:
        await msg.answer('❌ Некорректный формат. Ожидается: ДД.ММ.ГГГГ ЧЧ:ММ:СС')
        return

    await msg.answer(f'Время действия бота изменено на: {msg.text}', reply_markup=admin_panel_keyboad())
    await state.clear()
