from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json, os, re
from datetime import datetime

import os
from telegram.ext import ApplicationBuilder

TOKEN = os.getenv("8773128337:AAGND9r34kPdfb-kNibYUbP31vorwXJdkfg")
DB = "data.json"

# ================= DB =================
def load():
    if not os.path.exists(DB):
        return {}
    with open(DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ================= TIME =================
def now():
    return datetime.now()

def this_month():
    n = now()
    return n.year, n.month

# ================= WORDS =================
INCOME_WORDS = ["maosh","oylik","daromad","tushdi","keldi","oldim","bonus","foyda"]
EXPENSE_WORDS = ["xarajat","ketdi","sarfladim","ovqat","osh","choy","taxi","yo‘lkira","toladim","to‘ladim"]

# ================= PARSER =================
def extract_amount(text):
    text = text.lower()
    total = 0

    mln = re.findall(r'(\d+)\s*mln', text)
    for m in mln:
        total += int(m) * 1000000

    ming = re.findall(r'(\d+)\s*ming', text)
    for m in ming:
        total += int(m) * 1000

    if total == 0:
        nums = re.findall(r'\d+', text)
        if nums:
            total = int(nums[0])

    return total if total > 0 else None

def detect_type(text):
    text = text.lower()

    for w in INCOME_WORDS:
        if w in text:
            return "income"

    for w in EXPENSE_WORDS:
        if w in text:
            return "expense"

    if "+" in text:
        return "income"
    if "-" in text:
        return "expense"

    return None

# ================= HISOB =================
def balance(data):
    b = 0
    for i in data:
        if i.get("type") == "income":
            b += i.get("amount", 0)
        else:
            b -= i.get("amount", 0)
    return b

# ================= START (RESET) =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.message.from_user.id)

    data = load()

    # 🔥 TO‘LIQ RESET
    data[user] = []

    save(data)

    kb = [
        ["💰 Oylik maosh","💸 Xarajat"],
        ["📊 Balans","📋 Hisobot"],
        ["✏️ Tahrirlash"]
    ]

    await update.message.reply_text(
        "🧹 Barcha ma'lumotlar tozalandi!\n\nYangi boshlang 👇",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

# ================= MESSAGE =================
async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.message.from_user.id)
    text = update.message.text

    data = load()
    if user not in data:
        data[user] = []

    # BALANS
    if text == "📊 Balans":
        await update.message.reply_text(f"💰 Balans: {balance(data[user])}")
        return

    # HISOBOT
    if text == "📋 Hisobot":
        inc = sum(i.get("amount",0) for i in data[user] if i.get("type")=="income")
        exp = sum(i.get("amount",0) for i in data[user] if i.get("type")=="expense")

        await update.message.reply_text(
            f"📊 Hisobot\n\n💵 {inc}\n💸 {exp}\n💰 {inc-exp}"
        )
        return

    # OYLIK MAOSH
    if text == "💰 Oylik maosh":
        y,m = this_month()
        lst = [i for i in data[user] if i.get("type")=="income" and i.get("y")==y and i.get("m")==m]

        txt = "\n".join([f"{i+1}. {x.get('amount')} - {x.get('desc','izoh yo‘q')}" for i,x in enumerate(lst)]) or "yo‘q"
        await update.message.reply_text(f"📅 {len(lst)} ta\n{txt}")
        return

    # XARAJAT
    if text == "💸 Xarajat":
        y,m = this_month()
        lst = [i for i in data[user] if i.get("type")=="expense" and i.get("y")==y and i.get("m")==m]

        txt = "\n".join([f"{i+1}. {x.get('amount')} - {x.get('desc','izoh yo‘q')}" for i,x in enumerate(lst)]) or "yo‘q"
        await update.message.reply_text(f"📅 {len(lst)} ta\n{txt}")
        return

    # TAHRIR
    if text == "✏️ Tahrirlash":
        context.user_data["edit"] = True

        txt = "\n".join([f"{i+1}. {x.get('amount')} - {x.get('desc','izoh yo‘q')}" for i,x in enumerate(data[user])]) or "yo‘q"
        await update.message.reply_text(f"Tanlang:\n{txt}")
        return

    if context.user_data.get("edit") and text.isdigit():
        idx = int(text)-1
        if 0 <= idx < len(data[user]):
            context.user_data["edit_index"] = idx
            await update.message.reply_text("Yangi qiymatni yozing:")
            return

    if "edit_index" in context.user_data:
        idx = context.user_data["edit_index"]

        amount = extract_amount(text)
        if amount:
            data[user][idx]["amount"] = amount
            data[user][idx]["desc"] = text
            save(data)

            context.user_data.clear()
            await update.message.reply_text("✅ Yangilandi")
            return

    # YOZIB KIRITISH
    amount = extract_amount(text)
    t = detect_type(text)

    if amount and t:
        n = now()

        data[user].append({
            "type": t,
            "amount": amount,
            "desc": text,
            "y": n.year,
            "m": n.month
        })

        save(data)

        await update.message.reply_text(f"✅ Qo‘shildi\n💰 {balance(data[user])}")
        return

    await update.message.reply_text("❌ Tushunmadim")

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))

print("🚀 FINAL BOT")
app.run_polling()
