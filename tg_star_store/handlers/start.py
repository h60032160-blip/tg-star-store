from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from keyboards.inline import main_menu
from database.db import get_or_create_user
from config import STAR_BUY_RATE, STAR_SELL_RATE, SUPPORT_USERNAME

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    text = (
        f"👋 Bienvenue sur **Star Store**\n\n"
        f"⭐ Acheter → **{STAR_BUY_RATE} GRAM** / Star\n"
        f"💰 Vendre → **{STAR_SELL_RATE} GRAM** / Star\n\n"
        f"Choisis une option :"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):
    await callback.message.edit_text("Menu principal :", reply_markup=main_menu())
    await callback.answer()

@router.callback_query(F.data == "info")
async def info(callback: CallbackQuery):
    text = (
        f"ℹ️ **Infos**\n\n"
        f"• Paiement en GRAM uniquement\n"
        f"• Support : {SUPPORT_USERNAME}\n"
        f"• Les taux peuvent changer"
    )
    await callback.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await callback.answer()
