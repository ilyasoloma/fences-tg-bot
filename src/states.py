from aiogram.fsm.state import State, StatesGroup


class AdminState(StatesGroup):
    choosing_action = State()
    adding_username = State()
    adding_label = State()
    removing_user_type = State()
    removing_user = State()
    add_root = State()
    delete_root = State()
    set_datetime = State()
    bot_message_type = State()
    bot_message_recipient = State()
    bot_message_typing = State()


class Wall(StatesGroup):
    selecting_recipient = State()
    entering_alias = State()
    typing_message = State()
    choosing_recipient = State()
