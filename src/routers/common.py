from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.config import config
from src.keyboards import main_menu
from src.services import FencesService

router = Router()


@router.message(F.text == "/start")
async def start_cmd(msg: Message, service: FencesService):
    await msg.answer(config.START_CMD, reply_markup=await main_menu(msg.from_user.username, service=service))


@router.callback_query(F.data == "back")
async def back_main_menu(callback: CallbackQuery, state: FSMContext, service: FencesService):
    await state.clear()
    await callback.message.edit_text(config.START_CMD, reply_markup=await main_menu(callback.from_user.username,
                                                                                    service=service))
