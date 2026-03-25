import telebot
from telebot import types
from deep_translator import GoogleTranslator, constants
from gtts import gTTS
import sqlite3
import os
from flask import Flask # Yangi qo'shildi
import threading # Yangi qo'shildi

# --- RENDER UCHUN FLASK QISMI ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    # Render avtomatik ravishda PORT muhit o'zgaruvchisini beradi
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- SOZLAMALAR ---
API_TOKEN = '7971077723:AAGkdzg5hV9_fG8i1D80si1XAtxJvkZqncI' # O'z tokeningizni qo'ying
ADMIN_ID = 8213102743
CHANNELS = ["@jarvis_intellekt_kanal"]

bot = telebot.TeleBot(API_TOKEN)

# --- BAZA ---
conn = sqlite3.connect('translator_ultimate.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, src_lang TEXT, dest_lang TEXT)''')
conn.commit()

# --- BAYROQLAR ---
FLAGS = {
    'uz': '🇺🇿', 'en': '🇺🇸', 'ru': '🇷🇺', 'ko': '🇰🇷', 'tr': '🇹🇷', 'de': '🇩🇪',
    'fr': '🇫🇷', 'es': '🇪🇸', 'it': '🇮🇹', 'ja': '🇯🇵', 'zh-cn': '🇨🇳', 'ar': '🇸🇦',
    'kk': '🇰🇿', 'tg': '🇹🇯', 'ky': '🇰🇬', 'az': '🇦🇿', 'hi': '🇮🇳', 'pt': '🇵🇹',
    'nl': '🇳🇱', 'pl': '🇵🇱', 'uk': '🇺🇦', 'fa': '🇮🇷', 'iw': '🇮🇱', 'id': '🇮🇩',
    'be': '🇧🇾', 'bg': '🇧🇬', 'ca': '🇪🇸', 'cs': '🇨🇿', 'da': '🇩🇰', 'el': '🇬🇷',
    'et': '🇪🇪', 'fi': '🇫🇮', 'ga': '🇮🇪', 'gu': '🇮🇳', 'hr': '🇭🇷', 'hu': '🇭🇺',
    'hy': '🇦🇲', 'is': '🇮🇸', 'ka': '🇬🇪', 'lt': '🇱🇹', 'lv': '🇱🇻', 'mk': '🇲🇰',
    'mn': '🇲🇳', 'ms': '🇲🇾', 'mt': '🇲🇹', 'no': '🇳🇴', 'ro': '🇷🇴', 'sk': '🇸🇰',
    'sl': '🇸🇮', 'sq': '🇦🇱', 'sr': '🇷🇸', 'sv': '🇸🇪', 'sw': '🇰🇪', 'th': '🇹🇭',
    'tl': '🇵🇭', 'vi': '🇻🇳', 'af': '🇿🇦', 'am': '🇪🇹'
}

ALL_RAW = constants.GOOGLE_LANGUAGES_TO_CODES
TOP_FOUR = [('uzbek', 'uz'), ('english', 'en'), ('russian', 'ru'), ('korean', 'ko')]
OTHER_LANGS = [(k, v) for k, v in sorted(ALL_RAW.items()) if v not in ['uz', 'en', 'ru', 'ko']]
LANG_ENTRIES = TOP_FOUR + OTHER_LANGS

# --- MAJBURIY OBUNA TEKSHIRUVI ---
def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return True
    return True

def sub_keyboard():
    markup = types.InlineKeyboardMarkup()
    for channel in CHANNELS:
        btn = types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{channel[1:]}")
        markup.add(btn)
    markup.add(types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_subscription"))
    return markup

# --- KEYBOARDS ---
def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔄 Change Languages")
    if user_id == ADMIN_ID:
        markup.add("📊 Total Users", "📢 Broadcast Ad")
    return markup

def get_kb(prefix, page=0):
    markup = types.InlineKeyboardMarkup(row_width=2)
    start, end = page * 10, (page * 10) + 10
    current_page = LANG_ENTRIES[start:end]
    
    if prefix == "src" and page == 0:
        markup.add(types.InlineKeyboardButton(text="🔍 Auto Detect Language", callback_data="src_auto"))

    btns = [types.InlineKeyboardButton(text=f"{FLAGS.get(code, '🌐')} {name.capitalize()}", 
            callback_data=f"{prefix}_{code}") for name, code in current_page]
    markup.add(*btns)
    
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton(text="⬅️ Back", callback_data=f"p_{prefix}_{page-1}"))
    if end < len(LANG_ENTRIES):
        nav.append(types.InlineKeyboardButton(text="Next ➡️", callback_data=f"p_{prefix}_{page+1}"))
    markup.add(*nav)
    markup.add(types.InlineKeyboardButton(text="🔄 Restart Process", callback_data="restart"))
    return markup

# --- HANDLERLAR ---
@bot.message_handler(commands=['start'])
def start_msg(message):
    uid = message.chat.id
    if not check_sub(uid):
        bot.send_message(uid, "❌ Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz kerak:", 
                         reply_markup=sub_keyboard())
        return

    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (uid,))
    conn.commit()
    bot.send_message(uid, "👋 Ultimate Translator & Voice Bot\n\n1️⃣ Select Source (From):", 
                     reply_markup=main_keyboard(uid), parse_mode="Markdown")
    bot.send_message(uid, "Choose language:", reply_markup=get_kb("src"))

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def verify_sub(call):
    if check_sub(call.message.chat.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_msg(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali a'zo bo'lmadingiz!", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "📊 Total Users" and m.chat.id == ADMIN_ID)
def show_stats(message):
    cursor.execute("SELECT COUNT(*) FROM users")
    bot.send_message(message.chat.id, f"👥 Total users: {cursor.fetchone()[0]}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast Ad" and m.chat.id == ADMIN_ID)
def request_ad(message):
    msg = bot.send_message(message.chat.id, "Send your advertisement (text/photo/video):")
    bot.register_next_step_handler(msg, send_ad_to_all)

def send_ad_to_all(message):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    count = 0
    for user in users:
        try:
            bot.copy_message(user[0], message.chat.id, message.message_id)
            count += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Ad sent to {count} users.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('p_'))
def paginate(call):
    _, prefix, page = call.data.split('_')
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_kb(prefix, int(page)))

@bot.callback_query_handler(func=lambda call: call.data.startswith('src_'))
def set_src(call):
    code = call.data.split('_')[1]
    cursor.execute('UPDATE users SET src_lang = ? WHERE user_id = ?', (code, call.message.chat.id))
    conn.commit()
    bot.edit_message_text("2️⃣ Select Target (To):", call.message.chat.id, call.message.message_id, 
                          reply_markup=get_kb("dest"), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dest_'))
def set_dest(call):
    code = call.data.split('_')[1]
    cursor.execute('UPDATE users SET dest_lang = ? WHERE user_id = ?', (code, call.message.chat.id))
    conn.commit()
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "✅ Setup Done! Now send me text to translate and hear.")

@bot.message_handler(func=lambda m: m.text == "🔄 Change Languages")
def manual_reset(message):
    start_msg(message)

@bot.callback_query_handler(func=lambda call: call.data == "restart")
def restart_cb(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    start_msg(call.message)

@bot.message_handler(func=lambda m: True)
def translate_and_voice(message):
    uid = message.chat.id
    if not check_sub(uid):
        bot.send_message(uid, "❌ Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz kerak:", 
                         reply_markup=sub_keyboard())
        return

    cursor.execute('SELECT src_lang, dest_lang FROM users WHERE user_id = ?', (uid,))
    res = cursor.fetchone()
    if not res or not res[0] or not res[1]:
        start_msg(message)
        return

    try:
        wait = bot.reply_to(message, "⏳ Processing...")
        trans_text = GoogleTranslator(source=res[0], target=res[1]).translate(message.text)
        
        voice_file = f"voice_{uid}.mp3"
        tts = gTTS(text=trans_text, lang=res[1] if res[1] != 'auto' else 'en')
        tts.save(voice_file)
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔄 Change Settings", callback_data="restart"))
        
        bot.delete_message(uid, wait.message_id)
        bot.send_message(uid, f"✅ Result ({res[1].upper()}):\n\n{trans_text}", 
                         parse_mode="Markdown", reply_markup=kb)
        
        with open(voice_file, 'rb') as voice:
            bot.send_voice(uid, voice)
        
        os.remove(voice_file)
        
    except Exception as e:
        bot.send_message(uid, "❌ Xatolik yuz berdi. Bu til ovozli formatni qo'llab-quvvatlamasligi mumkin.")

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    # Flaskni alohida thread'da ishga tushiramiz
    threading.Thread(target=run_flask).start()
    print("Ultimate Bot is running...")
    bot.infinity_polling()

