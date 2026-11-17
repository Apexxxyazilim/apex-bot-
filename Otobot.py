import telebot
from telebot import types
import sqlite3

TOKEN = "8883592434:AAHLka1PP2w652CxapnaKIwUNPXDuJLhFp4"
ADMIN_ID = 8851630088  # Senin yönetici ID'n

bot = telebot.TeleBot(TOKEN)

# Veritabanı Kurulumu
conn = sqlite3.connect('apex_bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    total_images INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0
)''')
conn.commit()

# /start Komutu
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Bilinmiyor"
    
    # Kullanıcıyı kaydet
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    
    # Engelli kontrolü
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    banned = cursor.fetchone()
    if banned and banned[0] == 1:
        bot.reply_to(message, "⚠️ Üzgünüm, bu botu kullanmanız engellenmiştir.")
        return

    text = (
        "🤖 Merhaba ben ApexKod!\n\n"
        "Amacım şu an sizin attığınız görsellerin içindeki kodları "
        "size fotoğrafla birlikte düzenli bir şekilde verebilmek."
    )
    bot.send_message(message.chat.id, text)

# Yönetici Paneli (/yönetici giriş)
@bot.message_handler(commands=['yönetici'])
def yonetici_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Bu paneli görüntüleme yetkiniz yok!")
        return
    
    # İstatistikleri çek
    cursor.execute("SELECT COUNT(*), SUM(total_images) FROM users")
    stats = cursor.fetchone()
    total_users = stats[0] or 0
    total_imgs = stats[1] or 0
    
    cursor.execute("SELECT user_id, username, total_images, is_banned FROM users")
    all_users = cursor.fetchall()
    
    report = f"📊 **ApexKod Yönetim Paneli**\n\n" \
             f"👤 Toplam Kullanıcı: {total_users}\n" \
             f"📸 Toplam İşlenen Görsel: {total_imgs}\n\n" \
             f"📋 **Kullanıcı Listesi:**\n"
             
    for u in all_users:
        u_id, u_name, u_count, u_ban = u
        status = "🔴 Engelli" if u_ban == 1 else "🟢 Aktif"
        report += f"• ID: `{u_id}` | İşlem: {u_count} | {status}\n"
        
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

# Görsel Yakalama ve Kod Eşleme Simülasyonu
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    
    # Engelli kontrolü
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    banned = cursor.fetchone()
    if banned and banned[0] == 1:
        return

    # Kullanıcının görsel sayısını artır
    cursor.execute("UPDATE users SET total_images = total_images + 1 WHERE user_id = ?", (user_id,))
    conn.commit()

    # Kullanıcının attığı fotoğrafı al
    file_id = message.photo[-1].file_id
    
    # Örnek simüle edilmiş kod
    ornek_kod = "23UJKR390P" 
    
    caption_text = f"✅ Kod: {ornek_kod}"
    
    # Fotoğrafı aynen geri gönderip altına kodu yazıyoruz
    bot.send_photo(message.chat.id, file_id, caption=caption_text)

print("Bot aktif ve çalışıyor...")
bot.infinity_polling()
  
