import json
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import os
TOKEN = os.getenv("TOKEN")

bad_words = ["زب","نيك","قعك","بزازل","نكمك","قحبة","نيكمك"]

# ملف حفظ الإنذارات
DATA_FILE = "warnings.json"

# تحميل البيانات
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# حفظ البيانات
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

warnings = load_data()

# 🔹 فلترة الكلمات
async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return

    user = message.from_user
    chat = message.chat
    text = message.text.lower()

    # تجاهل الأدمن
    member = await chat.get_member(user.id)
    if member.status in ["administrator", "creator"]:
        return

    # فحص الكلام
    if any(word in text for word in bad_words):

        await message.delete()

        user_id = str(user.id)
        warnings[user_id] = warnings.get(user_id, 0) + 1
        save_data(warnings)

        count = warnings[user_id]

        if count == 1:
            await chat.send_message(f"⚠️ {user.first_name} إنذار أول")

        elif count == 2:
            await chat.send_message(f"⚠️ {user.first_name} إنذار ثاني")

        elif count >= 3:
            await chat.restrict_member(
                user.id,
                permissions=ChatPermissions(can_send_messages=False)
            )

            await chat.send_message(
                f"🚫 {user.first_name} تم كتمه دائمًا بسبب تكرار المخالفة"
            )

# 🔹 عرض عدد الإنذارات
async def warnings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    count = warnings.get(user_id, 0)

    await update.message.reply_text(f"📊 لديك {count} إنذارات")

# 🔹 إعادة تعيين إنذارات شخص (للأدمن فقط)
async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        return await update.message.reply_text("❌ هذا الأمر للأدمن فقط")

    if not context.args:
        return await update.message.reply_text("❗ استعمل: /reset user_id")

    target_id = context.args[0]

    if target_id in warnings:
        warnings[target_id] = 0
        save_data(warnings)
        await update.message.reply_text("✅ تم تصفير الإنذارات")

# 🔹 فك الكتم
async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    member = await chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        return await update.message.reply_text("❌ هذا الأمر للأدمن فقط")

    if not context.args:
        return await update.message.reply_text("❗ استعمل: /unmute user_id")

    target_id = int(context.args[0])

    await chat.restrict_member(
        target_id,
        permissions=ChatPermissions(can_send_messages=True)
    )

    await update.message.reply_text("✅ تم فك الكتم")

# 🔹 تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, moderate))
app.add_handler(CommandHandler("warnings", warnings_cmd))
app.add_handler(CommandHandler("reset", reset_cmd))
app.add_handler(CommandHandler("unmute", unmute_cmd))

app.run_polling()
