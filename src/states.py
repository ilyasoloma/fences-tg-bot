from aiogram.fsm.state import State, StatesGroup


class AdminState(StatesGroup):
    choosing_action = State()
    adding_user_type = State()
    adding_username = State()
    adding_label = State()
    removing_user_type = State()
    removing_user = State()


class Wall(StatesGroup):
    selecting_recipient = State()
    entering_alias = State()
    typing_message = State()
    choosing_recipient = State()
    order = [selecting_recipient, entering_alias, typing_message, choosing_recipient]
