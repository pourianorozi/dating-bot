# Dating Bot 🤖❤️

یک ربات تلگرام دوستیابی با قابلیت ساخت پروفایل، جستجوی کاربران، لایک، مچ و چت.

## ویژگی‌ها

- ساخت پروفایل کامل (نام، سن، جنسیت، مکان، علایق، بیو و نوع رابطه)
- جستجوی کاربران و سیستم لایک
- مچ دوطرفه و امکان چت
- سیستم امتیاز و بج
- ذخیره‌سازی با SQLite

## تکنولوژی‌ها

- Python 3
- `python-telegram-bot`
- SQLite
- Ruff (linting & formatting)

## راه‌اندازی

1. ریپازیتوری را کلون کنید:
```bash
git clone https://github.com/pourianorozi/dating-bot.git
cd dating-bot
```

2. وابستگی‌ها را نصب کنید:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # برای linting
```

3. یک ربات در [@BotFather](https://t.me/BotFather) بسازید و توکن را بگیرید.

4. توکن را تنظیم کنید:
```bash
cp .env.example .env
# سپس BOT_TOKEN را داخل .env پر کنید
# یا:
export BOT_TOKEN="your_bot_token_here"
```

5. ربات را اجرا کنید:
```bash
python main.py
```

## Linting با Ruff

```bash
# بررسی کد
ruff check .

# اصلاح خودکار
ruff check . --fix

# فرمت کردن کد
ruff format .
```

## نکات امنیتی مهم

- **هرگز توکن ربات را در کد هاردکد نکنید.**
- از متغیر محیطی `BOT_TOKEN` یا فایل `.env` استفاده کنید.
- فایل `.env` را در گیت پوش نکنید.

## لایسنس

MIT
