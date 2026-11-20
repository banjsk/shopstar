import os
import sqlite3
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or "0")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "").strip().lstrip("@")
DB_PATH = os.getenv("DB_PATH", "starheartshop.db")

# Fictional demo prices. This bot does not sell or deliver real Telegram Stars.
PRODUCTS = {
    "50": ("50 ⭐", "49 demo points"),
    "100": ("100 ⭐", "89 demo points"),
    "250": ("250 ⭐", "199 demo points"),
    "500": ("500 ⭐", "379 demo points"),
    "1000": ("1000 ⭐", "699 demo points"),
}


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL DEFAULT '',
                product_key TEXT NOT NULL,
                product_name TEXT NOT NULL,
                demo_price TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'DEMO'
            )
        """)


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Выбрать пакет", callback_data="catalog")],
        [
            InlineKeyboardButton("📦 Мои заказы", callback_data="orders"),
            InlineKeyboardButton("ℹ️ О магазине", callback_data="about"),
        ],
        [InlineKeyboardButton("💬 Поддержка", callback_data="support")],
    ])


def back_keyboard(destination="home"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data=destination)]
    ])


def catalog_keyboard():
    rows = [
        [InlineKeyboardButton(f"{name} — {price}", callback_data=f"product:{key}")]
        for key, (name, price) in PRODUCTS.items()
    ]
    rows.append([InlineKeyboardButton("🏠 В меню", callback_data="home")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💛 Добро пожаловать в starheartshop!\n\n"
        "Это демонстрационный магазин: здесь можно посмотреть каталог "
        "и создать тестовый заказ. Реальной оплаты и отправки Telegram Stars нет.\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard(),
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Твой Telegram user ID: {update.effective_user.id}\n"
        "Для настройки администратора добавь это число в переменную ADMIN_ID на хостинге."
    )


async def send_orders(message, user_id: int, edit=False):
    with connect_db() as conn:
        orders = conn.execute(
            "SELECT id, product_name, demo_price, status FROM orders "
            "WHERE user_id = ? ORDER BY id DESC LIMIT 10",
            (user_id,),
        ).fetchall()

    if not orders:
        text = "📦 У тебя пока нет тестовых заказов."
    else:
        lines = ["📦 Твои последние тестовые заказы:", ""]
        for order in orders:
            lines.append(
                f"№{order['id']} — {order['product_name']} "
                f"({order['demo_price']}) · {order['status']}"
            )
        text = "\n".join(lines)

    keyboard = back_keyboard()
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.reply_text(text, reply_markup=keyboard)


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_orders(update.message, update.effective_user.id)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_ID or update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Команда доступна только администратору.")
        return

    with connect_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"]
        latest = conn.execute(
            "SELECT id, user_id, product_name, demo_price, created_at "
            "FROM orders ORDER BY id DESC LIMIT 10"
        ).fetchall()

    lines = [f"🛠 Админ-панель starheartshop\nВсего тестовых заказов: {total}", ""]
    for item in latest:
        lines.append(
            f"#{item['id']} | user {item['user_id']} | "
            f"{item['product_name']} | {item['demo_price']}"
        )
    if not latest:
        lines.append("Заказов пока нет.")
    await update.message.reply_text("\n".join(lines))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — открыть магазин\n"
        "/orders — мои тестовые заказы\n"
        "/id — показать твой Telegram ID\n"
        "/admin — сводка администратора"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    user = query.from_user

    if data == "home":
        await query.edit_message_text(
            "💛 starheartshop\n\nДемонстрационный магазин ⭐\nВыбери действие:",
            reply_markup=main_keyboard(),
        )
    elif data == "catalog":
        await query.edit_message_text(
            "⭐ Каталог пакетов\n\nЦены условные и нужны только для демонстрации:",
            reply_markup=catalog_keyboard(),
        )
    elif data.startswith("product:"):
        key = data.split(":", 1)[1]
        if key not in PRODUCTS:
            await query.edit_message_text("Пакет не найден.", reply_markup=back_keyboard("catalog"))
            return
        name, price = PRODUCTS[key]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Создать тестовый заказ", callback_data=f"order:{key}")],
            [InlineKeyboardButton("⬅️ К каталогу", callback_data="catalog")],
        ])
        await query.edit_message_text(
            f"⭐ {name}\nЦена: {price}\n\n"
            "Это демонстрационная карточка. Реальная оплата и отправка Stars отключены.",
            reply_markup=keyboard,
        )
    elif data.startswith("order:"):
        key = data.split(":", 1)[1]
        if key not in PRODUCTS:
            await query.edit_message_text("Пакет не найден.", reply_markup=back_keyboard("catalog"))
            return
        name, price = PRODUCTS[key]
        with connect_db() as conn:
            cursor = conn.execute(
                "INSERT INTO orders "
                "(user_id, username, product_key, product_name, demo_price, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user.id,
                    user.username or "",
                    key,
                    name,
                    price,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )
            order_id = cursor.lastrowid

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Мои заказы", callback_data="orders")],
            [InlineKeyboardButton("🏠 В меню", callback_data="home")],
        ])
        await query.edit_message_text(
            f"🎉 Тестовый заказ создан!\n\n"
            f"Номер: #{order_id}\n"
            f"Пакет: {name}\n"
            f"Стоимость: {price}\n\n"
            "Оплата не проводилась. Реальные Telegram Stars не отправлялись.",
            reply_markup=keyboard,
        )
    elif data == "orders":
        await send_orders(query.message, user.id, edit=True)
    elif data == "about":
        await query.edit_message_text(
            "ℹ️ О магазине starheartshop\n\n"
            "Демонстрационный проект Telegram-бота. Каталог, цены и заказы учебные. "
            "Платежей и доставки Telegram Stars нет.",
            reply_markup=back_keyboard(),
        )
    elif data == "support":
        text = (
            f"💬 Поддержка: @{SUPPORT_USERNAME}"
            if SUPPORT_USERNAME
            else "💬 Контакт поддержки пока не настроен."
        )
        await query.edit_message_text(text, reply_markup=back_keyboard())


def main():
    if not BOT_TOKEN:
        raise SystemExit("Не задан BOT_TOKEN. Добавь его в Environment на хостинге.")

    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("starheartshop запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()
