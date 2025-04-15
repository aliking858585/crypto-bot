from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
from datetime import datetime, timedelta

# توکن ربات
TOKEN = "7774123854:AAF8ZdgLmvlnNVzRNp8vrnHBANNxUhyH0Js"

# کانال تلگرام
CHANNEL_ID = "@aataatee"

# نرخ بازار آزاد دلار به تومان (از صرافی ایرانی - Alanchand - 14 آوریل 2025)
USD_TO_IRR = 89800  # 89,800 تومان برای هر دلار

# کش برای قیمت‌ها
price_cache = {}  # کش قیمت‌ها
cache_timeout = timedelta(minutes=5)  # کش قیمت برای 5 دقیقه

# گرفتن قیمت از CoinGecko
def get_crypto_price(coin_id):
    global price_cache
    now = datetime.now()

    # چک کردن کش
    if coin_id in price_cache:
        price, timestamp = price_cache[coin_id]
        if now - timestamp < cache_timeout:
            return price

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        response = requests.get(url, timeout=3)  # تایم‌اوت 3 ثانیه
        data = response.json()
        price = data.get(coin_id, {}).get("usd")
        if price:
            price_cache[coin_id] = (price, now)
        return price
    except:
        return None

# مپ ارزها (شبکه TON)
COIN_MAP = {
    "ton": "the-open-network",
    "dogs": "dogs-2",
    "not": "notcoin",
    "px": "not-pixel",
}

# منوی اینلاین
def get_coin_menu():
    keyboard = [
        [InlineKeyboardButton("TON", callback_data="the-open-network"),
         InlineKeyboardButton("DOGS", callback_data="dogs-2")],
        [InlineKeyboardButton("NOT", callback_data="notcoin"),
         InlineKeyboardButton("PX", callback_data="not-pixel")],
    ]
    return InlineKeyboardMarkup(keyboard)

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"سلام! من ربات قیمت ارزهای شبکه TON هستم! 😎\n"
        f"اسم ارز رو بنویس (مثل ton یا dogs) یا از دکمه‌ها انتخاب کن.\n"
        f"برای اخبار و تحلیل بیشتر، به کانالم سر بزن: {CHANNEL_ID}\n"
        f"دستورات:\n/help - راهنما\n/chart - لینک نمودار",
        reply_markup=get_coin_menu()
    )

# دستور /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"دستورات من:\n"
        f"/start - شروع و منوی ارزها\n"
        f"/help - راهنما\n"
        f"/chart [ارز] - لینک نمودار قیمت (مثل: /chart ton)\n"
        f"یا اسم ارز رو بنویس (مثل dogs) برای قیمت لحظه‌ای.\n"
        f"برای اخبار و تحلیل بیشتر، به کانالم سر بزن: {CHANNEL_ID}",
        reply_markup=get_coin_menu()
    )

# دستور /chart
async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("لطفاً اسم ارز رو بنویس. مثال: /chart ton")
        return
    coin = args[0].lower()
    coin_id = COIN_MAP.get(coin)
    if coin_id:
        chart_url = f"https://www.coingecko.com/en/coins/{coin_id}"
        await update.message.reply_text(f"نمودار {coin.upper()}: {chart_url}")
    else:
        await update.message.reply_text("ارز پیدا نشد! اسم درست بنویس (مثل ton یا dogs).")

# هندل کردن پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = update.message.text.lower().strip()
    coin_id = COIN_MAP.get(coin)
    if coin_id:
        price_usd = get_crypto_price(coin_id)
        if price_usd is not None:
            price_irr = price_usd * USD_TO_IRR
            await update.message.reply_text(
                f"قیمت {coin.upper()}:\n"
                f"💵 دلار: ${price_usd:,.2f}\n"
                f"💸 تومان: {price_irr:,.0f} تومان",
                reply_markup=get_coin_menu()
            )
        else:
            await update.message.reply_text("نمی‌تونم قیمت رو پیدا کنم! 😔 دوباره امتحان کن.")
    else:
        await update.message.reply_text(
            "اسم ارز رو درست بنویس (مثل ton یا dogs).\n"
            "یا از دکمه‌ها انتخاب کن:", reply_markup=get_coin_menu()
        )

# هندل کردن دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    coin_id = query.data
    coin = [k for k, v in COIN_MAP.items() if v == coin_id][0]  # پیدا کردن اسم ارز
    price_usd = get_crypto_price(coin_id)
    if price_usd is not None:
        price_irr = price_usd * USD_TO_IRR
        await query.message.reply_text(
            f"قیمت {coin.upper()}:\n"
            f"💵 دلار: ${price_usd:,.2f}\n"
            f"💸 تومان: {price_irr:,.0f} تومان",
            reply_markup=get_coin_menu()
        )
    else:
        await query.message.reply_text("نمی‌تونم قیمت رو پیدا کنم! 😔 دوباره امتحان کن.")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("ربات داره اجرا می‌شه...")
    app.run_polling()

if __name__ == "__main__":
    main()
