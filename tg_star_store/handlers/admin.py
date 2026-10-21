from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_IDS
from database.db import get_pending_orders, update_order_status

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("pending"))
async def cmd_pending(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = await get_pending_orders()
    if not orders:
        await message.answer("Aucune commande en attente.")
        return
    text = "📋 **Commandes en attente :**\n\n"
    for o in orders:
        text += f"#{o[0]} | {o[2]} | {o[3]}⭐ → {o[4]} GRAM | user {o[1]}\n"
    await message.answer(text)

@router.message(Command("complete"))
async def cmd_complete(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        order_id = int(message.text.split()[1])
        await update_order_status(order_id, "completed")
        await message.answer(f"✅ Commande #{order_id} terminée.")
    except:
        await message.answer("Usage : /complete <order_id>")
