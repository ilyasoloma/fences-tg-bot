from aiogram.fsm.state import State, StatesGroup


class Wall(StatesGroup):
    selecting_recipient = State()
    entering_alias = State()
    typing_message = State()
