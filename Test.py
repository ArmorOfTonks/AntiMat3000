import nest_asyncio
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes
import re
from collections import defaultdict

# Разрешаем повторное использование цикла событий
nest_asyncio.apply()

# Список матерных слов с учётом вариаций
BAD_WORDS = [
    "хуй", "пизда", "ебать", "ебан", "ебло", "еблан", "ебак", "ёб", "ебуч", "ёбан", "бля", "бляд", "блять",
    "сука", "мразь", "гандон", "пидор", "пидр", "пидорас", "пидрила", "даун", "дебил", "идиот", "шлюха",
    "тварь", "чмо", "урод", "соси", "нахуй", "нах", "пох", "похуй", "охуел", "охуев", "охуен", "охуит",
    "охуяч", "жопа", "срака", "срать", "обосрал", "говно", "мудак", "мудила", "сучка", "ебись", "дроч",
    "дрочить", "залуп", "петух", "уеб", "уебище", "уёб", "уёбище", "выблядок", "выеб", "выебать",
    "наеб", "наебать", "разъеб", "разъебать", "доеб", "доебать", "хуесос", "хуила", "ебырь", "ебырьё",
    "ср@ть", "ср@ка", "срать", "п@зда", "ху@ло", "шлюxа", "сучк@"
]

# Функция для создания регулярного выражения для матов, учитывая символы и их замены
def create_bad_words_regex():
    escaped_bad_words = [re.escape(word) for word in BAD_WORDS]
    pattern = r'\b(?:' + '|'.join(escaped_bad_words) + r')\b'
    return re.compile(pattern, re.IGNORECASE)

# Создаем регулярное выражение для поиска матерных слов
BAD_WORDS_REGEX = create_bad_words_regex()

# База данных нарушителей
violations = defaultdict(int)

# Приветственное сообщение с инструкциями
async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Неизвестный"
    
    # Отправляем приветственное сообщение только один раз
    if user_id not in violations:
        violations[user_id] = 0
    
    welcome_text = (
        "Привет! Я бот для контроля соблюдения правил в группе.\n"
        "Я отслеживаю мат и нарушителей. Если кто-то использует мат, я удаляю сообщение и отправляю предупреждение.\n"
        "Я также могу вести статистику нарушений.\n\n"
        "Чтобы добавить меня в группу, нужно сделать следующее:\n"
        "1. Откройте свою группу в Telegram.\n"
        "2. Нажмите на имя группы в верхней части экрана.\n"
        "3. Выберите 'Добавить участника'.\n"
        "4. Найдите меня в списке и добавьте в группу.\n"
        "5. Важно: ⚠️СДЕЛАТЬ БОТА АДМИНИСТРАТОМ⚠️.\n\n"
        "После добавления в группу я смогу следить за соблюдением правил и предотвращать нарушения."
    )
    
    await update.message.reply_text(welcome_text)

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_welcome_message(update, context)

# Функция для проверки сообщения на мат
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    if BAD_WORDS_REGEX.search(message_text):  # Если найдены матерные слова
        try:
            # Удаляем сообщение
            await update.message.delete()

            # Добавляем нарушение для пользователя
            user_id = update.message.from_user.id
            username = update.message.from_user.username or "Неизвестный"
            violations[username] += 1
            violation_count = violations[username]

            # Уведомление о нарушении
            violation_message = f"⚠️ {username} нарушил(а) правила, использовав мат: {message_text}\n"
            violation_message += f"Общее количество нарушений: {violation_count}"

            # Отправляем уведомление в группу
            chat_id = update.message.chat.id  # ID чата, в котором произошло нарушение
            await context.bot.send_message(chat_id=chat_id, text=violation_message)
            print(f"Удалено сообщение: {message_text} от {username}")
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")

# Команда для вывода статистики нарушений (только для админов)
async def badword_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка на админа
    chat = update.message.chat
    user_id = update.message.from_user.id
    admins = await chat.get_administrators()
    admin_ids = [admin.user.id for admin in admins]

    if user_id not in admin_ids:
        await update.message.reply_text("❌ У вас нет прав для использования этой команды.")
        return

    # Сортируем нарушения по количеству и берем топ 5
    sorted_violations = sorted(violations.items(), key=lambda x: x[1], reverse=True)[:5]
    stats_message = "Топ 5 нарушителей по количеству матов:\n"

    for username, count in sorted_violations:
        stats_message += f"{username} - {count} нарушений\n"
    
    # Отправляем статистику
    await update.message.reply_text(stats_message)

# Главная функция для запуска бота
async def main():
    bot_token = "7816342999:AAFMV1-X-Phn0FJj80OkjniehFKOaruwD74"
    app = ApplicationBuilder().token(bot_token).build()

    # Обрабатываем команду /start
    app.add_handler(CommandHandler("start", start))
    # Обрабатываем текстовые сообщения (по типу матов)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_message))
    # Обрабатываем команду /badword (только для админов)
    app.add_handler(CommandHandler("badword", badword_stats))

    print("Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    # Заменяем старый цикл событий на новый, используя nest_asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
