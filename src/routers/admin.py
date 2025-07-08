from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import config
from src.keyboards import admin_panel_keyboad, admin_ask_user_type_keyboard, choose_user_to_remove_keyboard
from src.services import is_admin, get_users_by_role, remove_user, add_user
from src.states import AdminState
from src.utils.static import validate_alias

router = Router()


@router.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.username):
        await callback.message.answer("❌ У вас нет прав администратора.")
        return

    await callback.message.edit_text(config.MAIN_CONTROL_PANEL, reply_markup=admin_panel_keyboad())
    await state.set_state(AdminState.choosing_action)


@router.callback_query(AdminState.choosing_action, F.data == "admin_add")
async def ask_user_type(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(config.ADD_USER_ROLE, reply_markup=admin_ask_user_type_keyboard())
    await state.set_state(AdminState.adding_user_type)


@router.callback_query(AdminState.adding_user_type, F.data.startswith("add_"))
async def ask_username(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[-1]
    await state.update_data(role=role)
    await callback.message.edit_text(config.ENTER_ADD_USERNAME)
    await state.set_state(AdminState.adding_username)


@router.message(AdminState.adding_username)
async def ask_alias(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text.strip())
    await msg.answer(config.ENTER_ADD_ALIAS)
    await state.set_state(AdminState.adding_label)


@router.message(AdminState.adding_label)
async def save_new_user(msg: Message, state: FSMContext):
    await msg.answer(config.ADDING_USER)
    data = await state.get_data()
    username = data["username"]
    role = data["role"]
    label = msg.text.strip()

    valid, error = validate_alias(label)
    if not valid:
        await msg.answer(f"⚠️ {error}")
        return

    success, err = await add_user(username, label, role)
    if not success:
        await msg.answer(err)
        return

    await msg.answer(f"✅ Пользователь @{username} добавлен как {role}.", reply_markup=admin_panel_keyboad())
    await state.set_state(AdminState.choosing_action)


@router.callback_query(AdminState.choosing_action, F.data == "admin_remove_member")
async def choose_removal_type(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Кого вы хотите удалить?", reply_markup=admin_ask_user_type_keyboard())
    await state.set_state(AdminState.removing_user_type)


@router.callback_query(AdminState.removing_user_type, F.data.in_({"rm_member", "rm_admin"}))
async def list_users_to_remove(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[1]
    await state.update_data(role=role)
    usernames = await get_users_by_role(role)

    if not usernames:
        await callback.message.edit_text(f"❌ Нет {role}ов для удаления.")
        await state.set_state(AdminState.choosing_action)
        return

    await callback.message.edit_text("Выберите пользователя для удаления:",
                                     reply_markup=await choose_user_to_remove_keyboard(usernames))
    await state.set_state(AdminState.removing_user)


@router.callback_query(AdminState.removing_user, F.data.startswith("rm_user:"))
async def confirm_user_removal(callback: CallbackQuery, state: FSMContext):
    username = callback.data.split(":", 1)[1]
    await remove_user(username)
    await callback.message.answer(f"✅ Пользователь @{username} удалён.", reply_markup=admin_panel_keyboad())
    await state.set_state(AdminState.choosing_action)
