import os
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import arabic_reshaper
from bidi.algorithm import get_display
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

# ------------------- تنظیمات -------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8272361954:AAG8DeqJE1gl5jtINNWw4GMyL-hX_FvAgZ0")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003016016245"))  # آیدی کانال عددی
FONT_PATH = "Vazir.ttf"

logging.basicConfig(level=logging.INFO)

# ------------------- دریافت داده اوقات شرعی -------------------
cities = []
city_ids = [1, 13, 2, 9, 8, 6, 11]
for cid in city_ids:
    response = requests.get(f"https://prayer.aviny.com/api/prayertimes/{cid}")
    if response.status_code == 200:
        cities.append(response.json())

Oghat = {
    'نام شهر': [c['CityName'] for c in cities],
    'اذان صبح': [c['Imsaak'] for c in cities],
    'طلوع آفتاب': [c['Sunrise'] for c in cities],
    'اذان ظهر': [c['Noon'] for c in cities],
    'غروب خورشید': [c['Sunset'] for c in cities],
    'اذان مغرب': [c['Maghreb'] for c in cities],
    'نیمه شب شرعی': [c['Midnight'] for c in cities]
}

# ------------------- توابع کمکی -------------------
def to_persian_numbers(text):
    digits = "۰۱۲۳۴۵۶۷۸۹"
    return ''.join(digits[int(ch)] if ch.isdigit() else ch for ch in str(text))

def reshape_text(text):
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)

def make_table_image():
    df = pd.DataFrame(Oghat)
    df = df.astype(str).apply(lambda col: col.map(to_persian_numbers))
    df = df[df.columns[::-1]]  # راست‌چین ستون‌ها

    col_labels = [reshape_text(col) for col in df.columns]
    cell_text = [[reshape_text(v) for v in row] for row in df.values]

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")
    font_prop = FontProperties(fname=FONT_PATH)

    table = ax.table(cellText=cell_text,
                     colLabels=col_labels,
                     cellLoc='center',
                     loc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.5, 1.6)

    for (row, col), cell in table.get_celld().items():
        txt = cell.get_text()
        txt.set_fontproperties(font_prop)
        txt.set_va("center")
        txt.set_ha("center")
        if row == 0:
            cell.set_facecolor("#1c9c33")
            txt.set_color("white")
            txt.set_weight("bold")
        else:
            cell.set_facecolor("#f7f7f7" if row % 2 == 1 else "white")

    out_fname = "table_fa.png"
    plt.savefig(out_fname, bbox_inches='tight', dpi=300)
    plt.close(fig)
    return out_fname

# ------------------- هندلرها -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات روشن است ✅")

async def send_table_to_channel():
    bot = Bot(BOT_TOKEN)
    file_path = make_table_image()
    async with bot:
        with open(file_path, "rb") as photo:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
    logging.info("✅ جدول به کانال ارسال شد")

async def send_daily_message():
    bot = Bot(BOT_TOKEN)
    async with bot:
        await bot.send_message(chat_id=CHANNEL_ID, text="سلام! این پیام تست زمان‌بندی است ⏰")
    logging.info("✅ پیام زمان‌بندی‌شده ارسال شد")

# ------------------- Scheduler -------------------
async def start_scheduler(app):
    scheduler = AsyncIOScheduler()

    # 🔹 تست هر ۱ دقیقه یک پیام
    scheduler.add_job(send_table_to_channel, "interval", minutes=1)

    scheduler.start()
    logging.info("⏳ Scheduler فعال شد (هر ۱ دقیقه پیام تست ارسال می‌شود)")

# ------------------- اجرای ربات -------------------
app = ApplicationBuilder().token(BOT_TOKEN).post_init(start_scheduler).build()
app.add_handler(CommandHandler("start", start))

print("ربات در حال اجراست...")
app.run_polling()

