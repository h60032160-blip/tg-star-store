from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline import sell_amounts, main_menu
from services.rates import calculate_sell
from database.db import create_order
from config import MIN_SELL, MAX_SELL

router = Router()

@router.callback_query(F.data == "sell_stars")
async def sell_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 Combien de Stars veux-tu vendre ?\n\nTu enverras d'abord les Stars au bot.",
        reply_markup=sell_amounts()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("sell_"))
async def sell_amount(callback: CallbackQuery):
    amount = int(callback.data.split("_")[1])
    if amount < MIN_SELL or amount > MAX_SELL:
        await callback.answer("Montant invalide", show_alert=True)
        return

    ton_to_receive = calculate_sell(amount)
    order_id = await create_order(callback.from_user.id, "sell", amount, ton_to_receive)

    text = (
        f"💰 **Vente #{order_id}**\n\n"
        f"⭐ Quantité : **{amount} Stars**\n"
        f"💎 Tu recevras : **{ton_to_receive} GRAM**\n\n"
        f"1. Envoie les {amount} Stars à @v1xq8 sur Telegram\n"
        f"2. Contacte un admin pour validation\n"
        f"3. Tu recevras les GRAM après vérification"
    )
    await callback.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await callback.answer()
