from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.config import config
from src.keyboards import main_menu
from src.states import Wall

router = Router()


@router.message(F.text == "/start")
async def start_cmd(msg: Message):
    await msg.answer(config.START_CMD, reply_markup=await main_menu(msg.from_user.username))


@router.callback_query(F.data == "back")
async def back_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(config.START_CMD, reply_markup=await main_menu(callback.from_user.username))


# @router.message()
# async def fallback_handler(msg: Message):
#     await msg.answer(config.UNKNOWING_ERROR)
#     await msg.answer(config.START_CMD, reply_markup=await main_menu(msg.from_user.username))
#     logger.warning("Unknown message from %s: %s", msg.from_user.username, msg.text)
