import random
import string
import smtplib
import sqlite3
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify

app = Flask(__name__)

# E-posta Ayarları
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sadettinofficial2@gmail.com"
SENDER_PASSWORD = "vvxx ufbf spui asgu"  # Google Uygulama Şifren

# Veritabanını Hazırla
def init_db():
    conn = sqlite3.connect('licenses.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            email TEXT,
            is_used INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def generate_license_key():
    parts = ["".join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4)]
    return f"AURIEL-{'-'.join(parts)}"

def send_license_email(to_email, license_key):
    try:
        subject = "Auriel Translation - Lisans Anahtarınız"
        body = (
            "Merhaba,\n\n"
            "Shopier üzerinden yapmış olduğunuz alışveriş için teşekkür ederiz!\n\n"
            f"Lisans Anahtarınız: {license_key}\n\n"
            "Bu kod size özeldir ve tek kullanımlıktır. Program içerisindeki aktivasyon bölümüne yazarak kullanmaya başlayabilirsiniz.\n\n"
            "İyi günler dileriz."
        )
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"[BAŞARILI] Lisans gönderildi: {to_email} -> {license_key}")
    except Exception as e:
        print(f"[HATA] E-posta gönderilemedi: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    # 1. İstek ister JSON gelsin ister form verisi, hepsini güvenle yakala
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict()
        if not data and request.data:
            try:
                import json
                data = json.loads(request.data.decode('utf-8'))
            except:
                parsed_form = urllib.parse.parse_qs(request.data.decode('utf-8'))
                data = {k: v[0] for k, v in parsed_form.items()}

    print(f"Gelen İstek Verisi: {data}")
    
    # 2. Müşteri e-postasını al
    customer_email = data.get('email') or data.get('buyer_email') or data.get('client_email')
    
    # 3. TEST VE MÜŞTERİ BİR ARADA:
    # Eğer test yaparken e-posta gönderilmediyse sistem hata vermez,
    # testi kendi mailinde (SENDER_EMAIL) görebilmen için sana yönlendirir.
    if not customer_email:
        customer_email = SENDER_EMAIL
        print("[BİLGİ] E-posta bulunamadı, test amacıyla kendi mailinize yönlendirildi.")

    # Benzersiz lisans anahtarı üret
    license_key = generate_license_key()
    
    # Veritabanına kaydet (is_used = 0, henüz kullanılmadı)
    conn = sqlite3.connect('licenses.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO licenses (key, email, is_used) VALUES (?, ?, 0)", (license_key, customer_email))
    conn.commit()
    conn.close()

    # E-postayı e-posta adresine gönder (Testse sana, müşteriyse müşteriye)
    send_license_email(customer_email, license_key)
    
    return jsonify({
        "status": "success", 
        "message": "Lisans oluşturuldu ve gönderildi.",
        "generated_key": license_key,
        "sent_to": customer_email
    }), 200

@app.route('/verify', methods=['POST'])
def verify_license():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict()

    key = data.get('key', '').strip()
    
    if not key:
        return jsonify({"status": "error", "message": "Lisans anahtarı boş olamaz."}), 400
        
    conn = sqlite3.connect('licenses.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT is_used FROM licenses WHERE key = ?", (key,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"status": "error", "message": "Geçersiz lisans anahtarı!"}), 404
        
    is_used = row[0]
    if is_used == 1:
        conn.close()
        return jsonify({"status": "error", "message": "Bu lisans anahtarı daha önce başka bir cihazda kullanılmış!"}), 400
        
    # Kod geçerli ve ilk kez kullanılıyor, hemen kilitliyoruz (1 yapıyoruz)
    cursor.execute("UPDATE licenses SET is_used = 1 WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Lisans başarıyla etkinleştirildi!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
