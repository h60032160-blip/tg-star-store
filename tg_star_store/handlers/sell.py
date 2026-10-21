# language: Python, file: handlers/sell.py
# Flow : sélection montant → demande adresse TON → invoice Stars (XTR) → paiement → envoi TON auto

import re
import logging

from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, Message,
    LabeledPrice, PreCheckoutQuery,
    ContentType,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

from config import ADMIN_IDS, MIN_SELL, MAX_SELL
from database.db import create_order, update_order_status
from keyboards.inline import sell_amounts, main_menu
from services.rates import calculate_sell
from services.ton_send import send_ton

router = Router()
log    = logging.getLogger(__name__)


class SellStates(StatesGroup):
    waiting_wallet  = State()
    waiting_payment = State()


@router.callback_query(F.data == "sell_stars")
async def sell_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 <b>Combien de Stars veux-tu vendre ?</b>",
        reply_markup=sell_amounts(),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(re.compile(r"^sellamt_(\d+)$")))
async def sell_amount(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split("_")[1])
    if not (MIN_SELL <= amount <= MAX_SELL):
        await callback.answer("Montant invalide.", show_alert=True)
        return

    ton_to_receive = calculate_sell(amount)
    await state.update_data(amount=amount, ton=ton_to_receive)
    await state.set_state(SellStates.waiting_wallet)

    await callback.message.edit_text(
        f"💰 <b>Vente de {amount} ⭐</b>\n\n"
        f"Tu recevras : <b>{ton_to_receive} TON</b>\n\n"
        f"Envoie-moi ton <b>adresse wallet TON</b> (commence par UQ ou EQ) :"
    )
    await callback.answer()


@router.message(StateFilter(SellStates.waiting_wallet))
async def receive_wallet(message: Message, state: FSMContext, bot: Bot):
    address = message.text.strip()

    if not re.match(r"^(UQ|EQ|0:)[A-Za-z0-9_\-]{46,}$", address):
        await message.answer(
            "❌ Adresse TON invalide.\n"
            "Elle doit commencer par <b>UQ</b> ou <b>EQ</b>.\n"
            "Réessaie :"
        )
        return

    data        = await state.get_data()
    amount: int = data["amount"]
    ton: float  = data["ton"]

    order_id = await create_order(message.from_user.id, "sell", amount, ton)
    await state.update_data(order_id=order_id, wallet=address)
    await state.set_state(SellStates.waiting_payment)

    await bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Vente de {amount} Stars",
        description=f"Tu envoies {amount} ⭐ → tu reçois {ton} TON sur {address[:10]}...",
        payload=f"sell_{order_id}_{address}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=amount)],
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: Message, state: FSMContext, bot: Bot):
    payment    = message.successful_payment
    payload    = payment.invoice_payload
    parts      = payload.split("_", 2)

    if len(parts) < 3 or parts[0] != "sell":
        return

    order_id   = int(parts[1])
    to_wallet  = parts[2]
    stars_paid = payment.total_amount
    ton_amount = calculate_sell(stars_paid)

    await message.answer(
        f"✅ Paiement de <b>{stars_paid} Stars</b> reçu !\n"
        f"Envoi de <b>{ton_amount} TON</b> en cours..."
    )

    try:
        ok = await send_ton(to_wallet, ton_amount, comment=f"sell_{order_id}")
        if ok:
            await update_order_status(order_id, "completed")
            await message.answer(
                f"💎 <b>{ton_amount} TON envoyés</b> sur ton wallet !\n"
                f"Transaction confirmée.",
                reply_markup=main_menu(),
            )
            user = message.from_user
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"✅ Vente automatique #{order_id}\n"
                        f"@{user.username or '?'} ({user.id})\n"
                        f"{stars_paid}⭐ → {ton_amount} TON → {to_wallet}",
                    )
                except Exception:
                    pass
        else:
            await update_order_status(order_id, "pending_review")
            await message.answer(
                f"⚠️ Stars reçues mais l'envoi TON a échoué.\n"
                f"Un admin va régler ça manuellement. Référence : #{order_id}",
                reply_markup=main_menu(),
            )
    except Exception as e:
        log.exception("Erreur envoi TON : %s", e)
        await update_order_status(order_id, "pending_review")
        await message.answer(
            f"⚠️ Erreur lors de l'envoi TON.\n"
            f"Contacte le support avec la référence : #{order_id}",
            reply_markup=main_menu(),
        )

    await state.clear()
