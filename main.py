import telebot
import random
from telebot import types

# Твой токен
TOKEN = '8611896253:AAGerMCcsYZ45B-3rl24GPZXKko73E9Crxw'
bot = telebot.TeleBot(TOKEN)

user_states = {}
MAX_ATTEMPTS = 10  # Твой лимит попыток

def create_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("👤 Один игрок", "👥 На двоих")
    return markup

@bot.message_handler(commands=['start', 'reset'])
def welcome(message):
    user_states[message.chat.id] = {'phase': 'CHOOSING_MODE'}
    text = (
        "✨ *ДОБРО ПОЖАЛОВАТЬ* ✨\n"
        "В игру — *Угадай число*!\n\n"
        f"У тебя будет всего *{MAX_ATTEMPTS} попыток*.\n"
        "Предыдущие подсказки будут исчезать — тренируй память! 🧠"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('phase') == 'CHOOSING_MODE')
def set_mode(message):
    chat_id = message.chat.id
    if message.text == "👤 Один игрок":
        user_states[chat_id] = {
            'phase': 'PLAYING',
            'mode': 'SINGLE',
            'number': random.randint(1, 100),
            'attempts': 0,
            'last_msg_id': None  # Храним ID сообщения для удаления
        }
        bot.send_message(chat_id, "🤖 *РЕЖИМ: Один игрок*\nЗагадал от `1` до `100`.", parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
    
    elif message.text == "👥 На двоих":
        user_states[chat_id] = {'phase': 'WAITING_FOR_NUMBER', 'mode': 'MULTI'}
        bot.send_message(chat_id, "🤝 *РЕЖИМ: На двоих*\nПЕРВЫЙ игрок, введи секретное число:", parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('phase') == 'WAITING_FOR_NUMBER')
def set_secret_number(message):
    if not message.text.isdigit():
        bot.reply_to(message, "⚠️ Введи цифры!")
        return
    
    chat_id = message.chat.id
    user_states[chat_id].update({
        'phase': 'PLAYING',
        'number': int(message.text),
        'attempts': 0,
        'last_msg_id': None
    })
    bot.send_message(chat_id, ".\n" * 40 + "✅ *ЧИСЛО ЗАГАДАНО!*\nВТОРОЙ игрок, твой ход:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('phase') == 'PLAYING')
def game_process(message):
    chat_id = message.chat.id
    state = user_states[chat_id]
    
    # Пытаемся удалить предыдущую подсказку бота (эффект размытия/скрытия)
    if state.get('last_msg_id'):
        try:
            bot.delete_message(chat_id, state['last_msg_id'])
            bot.delete_message(chat_id, message.message_id) # Удаляем и сообщение игрока для чистоты
        except:
            pass

    if not message.text.isdigit():
        msg = bot.send_message(chat_id, "❌ Вводи только числа!")
        state['last_msg_id'] = msg.message_id
        return

    guess = int(message.text)
    state['attempts'] += 1

    if guess == state['number']:
        bot.send_message(chat_id, f"🎉 *ПОБЕДА!*\nУгадано за `{state['attempts']}` попыток!", parse_mode="Markdown")
        welcome(message)
    elif state['attempts'] >= MAX_ATTEMPTS:
        bot.send_message(chat_id, f"💀 *ПРОИГРЫШ!*\nПопытки закончились. Было загадано: `{state['number']}`", parse_mode="Markdown")
        welcome(message)
    else:
        hint = "⬆️ *БОЛЬШЕ*" if guess < state['number'] else "⬇️ *МЕНЬШЕ*"
        # Отправляем новую подсказку и запоминаем её ID
        msg = bot.send_message(
            chat_id, 
            f"{hint}\nОсталось попыток: `{MAX_ATTEMPTS - state['attempts']}`", 
            parse_mode="Markdown"
        )
        state['last_msg_id'] = msg.message_id

if __name__ == "__main__":
    bot.infinity_polling()