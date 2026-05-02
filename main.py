# =============================================================
#    🛒 MINI MARKET BOT - VS CODE VERSION
#    Kutubxona: aiogram 3.x
#    Muallif: Bahodir | @Bahodir_N14
# =============================================================

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InputMediaPhoto
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# =============================================================
#    ASOSIY SOZLAMALAR - MA'LUMOTLAR O'RNATILDI
# =============================================================

BOT_TOKEN = "8630792495:AAGEOyl7D_NeXdMBVNDHAt6REAfmrM5hMsM"
ADMIN_ID = 5913498357
SECRET_WORD = "Bahodirw"

# =============================================================
#    MAHSULOTLAR RO'YXATI
# =============================================================

PRODUCTS = {
    "ff_burger": {
        "name":  "🍔 Klassik Burger",
        "desc":  "Mol go'shtidan tayyorlangan, qo'shimcha sous va yangi sabzavotlar bilan",
        "price": 35000,
        "img":   "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800",
        "cat":   "fastfood",
    },
    "ff_pizza": {
        "name":  "🍕 Margherita Pizza",
        "desc":  "Italyan xamiri, pomidor sousi, mozarella pishlog'i — klassika!",
        "price": 55000,
        "img":   "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",
        "cat":   "fastfood",
    },
    "ff_hotdog": {
        "name":  "🌭 Hot-Dog Deluxe",
        "desc":  "Juicy sosiska, xantal, ketchup va crispy piyoz bilan",
        "price": 22000,
        "img":   "https://images.unsplash.com/photo-1612392062798-3a914e8e3a86?w=800",
        "cat":   "fastfood",
    },
    "dr_cola": {
        "name":  "🥤 Coca-Cola 0.5L",
        "desc":  "Muzlatilgan, yangilangan — klassik ta'm bilan",
        "price": 12000,
        "img":   "https://images.unsplash.com/photo-1553456558-aff63285bdd1?w=800",
        "cat":   "drinks",
    },
    "dr_coffee": {
        "name":  "☕ Kapuchino",
        "desc":  "Italyan qahvasi, ko'pikli sut va shokolad bilan",
        "price": 25000,
        "img":   "https://images.unsplash.com/photo-1541167760496-1628856ab772?w=800",
        "cat":   "drinks",
    },
    "sw_cake": {
        "name":  "🍰 Medovik Tort",
        "desc":  "Ko'p qavatli asal torti, smetana kremi bilan",
        "price": 45000,
        "img":   "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800",
        "cat":   "sweets",
    },
    "sw_icecream": {
        "name":  "🍦 Premium Muzqaymoq",
        "desc":  "3 ta ta'm: vanil, shokolad, qulupnay — bir stakanda",
        "price": 20000,
        "img":   "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=800",
        "cat":   "sweets",
    }
}

CATEGORIES = {
    "fastfood": ("🍔 Fast-food", "ff"),
    "drinks":   ("🥤 Ichimliklar", "dr"),
    "sweets":   ("🍰 Shirinliklar", "sw"),
}

# --- FSM VA XOTIRA ---
class OrderStates(StatesGroup):
    waiting_name    = State()
    waiting_phone   = State()
    waiting_address = State()

user_carts = {}

def get_user_cart(user_id: int) -> dict:
    if user_id not in user_carts:
        user_carts[user_id] = {}
    return user_carts[user_id]

# --- TUGMALAR ---
def kb_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Fast-food", callback_data="cat_fastfood"),
         InlineKeyboardButton(text="🥤 Ichimliklar", callback_data="cat_drinks")],
        [InlineKeyboardButton(text="🍰 Shirinliklar", callback_data="cat_sweets")],
        [InlineKeyboardButton(text="🛒 Savatcham", callback_data="cart_view")]
    ])

def kb_category(cat_key):
    rows = []
    for p_id, p_data in PRODUCTS.items():
        if p_data["cat"] == cat_key:
            rows.append([InlineKeyboardButton(text=f"{p_data['name']} - {p_data['price']:,} so'm", callback_data=f"product_{p_id}")])
    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="main_menu"),
                 InlineKeyboardButton(text="🛒 Savatcha", callback_data="cart_view")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_product(product_id):
    category = PRODUCTS[product_id]["cat"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Savatchaga qo'sh", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"cat_{category}"),
         InlineKeyboardButton(text="🏠 Menu", callback_data="main_menu")]
    ])

def kb_cart(has_items):
    rows = []
    if has_items:
        rows.append([InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="order_start")])
        rows.append([InlineKeyboardButton(text="🗑️ Tozalash", callback_data="cart_clear")])
    rows.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def kb_cancel():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True)

# --- MATNLAR ---
def format_money(n): return f"{n:,}".replace(",", " ") + " so'm"

# --- HANDLERLAR ---
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer_photo(photo="https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200", 
                         caption="🛒 <b>MINI MARKET</b>\n\n<b>Bahodir</b> tomonidan yaratilgan botga xush kelibsiz!\n\n👇 Xarid qilishni boshlang:", 
                         parse_mode="HTML", reply_markup=kb_main_menu())

@dp.message(F.text == SECRET_WORD)
async def secret(m: Message):
    await m.answer(f"🔐 <b>Muallif:</b> Bahodir\n📬 Aloqa: https://t.me/Bahodir_N14", parse_mode="HTML")

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_caption(caption="🛒 <b>MINI MARKET</b>\n\nBo'limni tanlang:", 
                                   parse_mode="HTML", reply_markup=kb_main_menu())

@dp.callback_query(F.data.startswith("cat_"))
async def show_cat(call: CallbackQuery):
    cat_key = call.data.split("_")[1]
    await call.message.edit_caption(caption=f"📂 <b>{CATEGORIES[cat_key][0]}</b> bo'limi:", 
                                   parse_mode="HTML", reply_markup=kb_category(cat_key))

@dp.callback_query(F.data.startswith("product_"))
async def show_prod(call: CallbackQuery):
    p_id = call.data.split("_")[1]
    p = PRODUCTS[p_id]
    text = f"<b>{p['name']}</b>\n\n{p['desc']}\n\n💰 Narxi: {format_money(p['price'])}"
    await call.message.edit_media(media=InputMediaPhoto(media=p["img"], caption=text, parse_mode="HTML"), 
                                  reply_markup=kb_product(p_id))

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):
    p_id = call.data.split("_")[1]
    cart = get_user_cart(call.from_user.id)
    cart[p_id] = cart.get(p_id, 0) + 1
    await call.answer(f"✅ Savatga qo'shildi!")

@dp.callback_query(F.data == "cart_view")
async def view_cart(call: CallbackQuery):
    cart = get_user_cart(call.from_user.id)
    if not cart:
        await call.message.edit_caption(caption="🛒 Savatchangiz bo'sh", reply_markup=kb_cart(False))
        return
    
    text = "🛒 <b>Savatchangiz:</b>\n\n"
    total = 0
    for p_id, q in cart.items():
        p = PRODUCTS[p_id]
        total += p['price'] * q
        text += f"• {p['name']} ({q} dona) = {format_money(p['price']*q)}\n"
    text += f"\n💰 <b>Jami: {format_money(total)}</b>"
    await call.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb_cart(True))

@dp.callback_query(F.data == "cart_clear")
async def cart_clear(call: CallbackQuery):
    user_carts[call.from_user.id] = {}
    await call.answer("🗑️ Savatcha tozalandi!")
    await view_cart(call)

@dp.callback_query(F.data == "order_start")
async def order_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.waiting_name)
    await call.message.answer("👤 <b>Ismingizni kiriting:</b>", parse_mode="HTML", reply_markup=kb_cancel())
    await call.answer()

@dp.message(OrderStates.waiting_name)
async def get_name(m: Message, state: FSMContext):
    if m.text == "❌ Bekor qilish":
        await state.clear()
        await m.answer("❌ Buyurtma bekor qilindi.", reply_markup=ReplyKeyboardRemove())
        return
    await state.update_data(name=m.text)
    await state.set_state(OrderStates.waiting_phone)
    await m.answer("📞 <b>Telefon raqamingizni yuboring:</b>", parse_mode="HTML")

@dp.message(OrderStates.waiting_phone)
async def get_phone(m: Message, state: FSMContext):
    await state.update_data(phone=m.text)
    await state.set_state(OrderStates.waiting_address)
    await m.answer("📍 <b>Yetkazib berish manzilini kiriting:</b>", parse_mode="HTML")

@dp.message(OrderStates.waiting_address)
async def get_address(m: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    cart = get_user_cart(m.from_user.id)
    
    order_text = f"🆕 <b>YANGI BUYURTMA!</b>\n\n👤 <b>Ism:</b> {data['name']}\n📞 <b>Tel:</b> {data['phone']}\n📍 <b>Manzil:</b> {m.text}\n\n🛒 <b>Tarkib:</b>\n"
    total = 0
    for p_id, q in cart.items():
        p = PRODUCTS[p_id]
        order_text += f"- {p['name']} ({q} dona)\n"
        total += p['price'] * q
    order_text += f"\n💰 <b>Jami: {format_money(total)}</b>"
    
    await bot.send_message(ADMIN_ID, order_text, parse_mode="HTML")
    await m.answer("✅ <b>Rahmat! Buyurtmangiz qabul qilindi.</b>\nTez orada aloqaga chiqamiz.", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    user_carts[m.from_user.id] = {}
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    print("🚀 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())