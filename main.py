import telebot
from telebot import types
import json
import os

# === НАСТРОЙКИ ===
BOT_TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"  # Замени на токен от @BotFather
ADMIN_CHAT_ID = 123456789  # Замени на свой Telegram ID (узнать у @userinfobot)

bot = telebot.TeleBot(BOT_TOKEN)

# Файл, куда сохраняются апелляции
APPEALS_FILE = "appeals.json"

# === СОСТОЯНИЯ ===
USER_STATE = {}  # {chat_id: "state"}
USER_DATA = {}   # {chat_id: {"nick": ..., "date": ..., ...}}


def save_appeal(data):
    """Сохраняет апелляцию в файл."""
    appeals = []
    if os.path.exists(APPEALS_FILE):
        with open(APPEALS_FILE, "r", encoding="utf-8") as f:
            appeals = json.load(f)
    appeals.append(data)
    with open(APPEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(appeals, f, ensure_ascii=False, indent=2)


@bot.message_handler(commands=["start"])
def start(message):
    """Приветствие и кнопка 'Апелляция бана'."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("📝 Апелляция бана")
    bot.send_message(
        message.chat.id,
        "👋 Привет! Это бот поддержки **NybikSmp**.\n\n"
        "Если ты хочешь обжаловать бан — нажми кнопку ниже.",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: m.text == "📝 Апелляция бана")
def appeal_start(message):
    """Начало апелляции — спрашиваем ник."""
    USER_STATE[message.chat.id] = "nick"
    USER_DATA[message.chat.id] = {}
    bot.send_message(
        message.chat.id,
        "✏️ Введи свой **никнейм** (как на сервере):",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id) == "nick")
def appeal_nick(message):
    USER_DATA[message.chat.id]["nick"] = message.text
    USER_STATE[message.chat.id] = "date"
    bot.send_message(
        message.chat.id,
        "📅 Введи **дату бана** (например: 12.10.2026):",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id) == "date")
def appeal_date(message):
    USER_DATA[message.chat.id]["date"] = message.text
    USER_STATE[message.chat.id] = "desc"
    bot.send_message(
        message.chat.id,
        "📄 Опиши **ситуацию** (что произошло, почему считаешь бан несправедливым):",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id) == "desc")
def appeal_desc(message):
    USER_DATA[message.chat.id]["desc"] = message.text
    USER_STATE[message.chat.id] = "proof"
    bot.send_message(
        message.chat.id,
        "📎 Есть ли у тебя **доказательства**? (ссылка на видео/скрин).\n"
        "Если нет — напиши «нет».",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id) == "proof")
def appeal_proof(message):
    data = USER_DATA[message.chat.id]
    data["proof"] = message.text
    data["username"] = message.from_user.username or "нет"
    data["user_id"] = message.from_user.id

    # Сохраняем апелляцию
    save_appeal(data)

    # Отправляем админу
    admin_text = (
        f"🔔 **Новая апелляция!**\n\n"
        f"👤 Ник: `{data['nick']}`\n"
        f"📅 Дата бана: `{data['date']}`\n"
        f"📄 Описание: {data['desc']}\n"
        f"📎 Доказательства: {data['proof']}\n"
        f"💬 TG: @{data['username']} (ID: {data['user_id']})"
    )
    try:
        bot.send_message(ADMIN_CHAT_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")

    # Подтверждение игроку
    bot.send_message(
        message.chat.id,
        "✅ **Вы успешно отправили обжалование бана.**\n\n"
        "⏳ Ожидайте ответа в этом боте.",
        parse_mode="Markdown"
    )

    # Сброс
    USER_STATE.pop(message.chat.id, None)
    USER_DATA.pop(message.chat.id, None)


@bot.message_handler(commands=["cancel"])
def cancel(message):
    """Отмена заполнения."""
    USER_STATE.pop(message.chat.id, None)
    USER_DATA.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "❌ Апелляция отменена.")


if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()