import random
import string
import smtplib
import sqlite3
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
import base64
import json

app = Flask(__name__)

# Email Settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sadettinofficial2@gmail.com"
SENDER_PASSWORD = "vvxx ufbf spui asgu"  # Google App Password

# Initialize Database
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
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4)]
    return f"AURIEL-{'-'.join(parts)}"

def send_license_email(to_email, license_key):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Auriel - Your License Key"

        body = f"Hello,\n\nThank you for your purchase!\nYour License Key: {license_key}\n\nNote: This key can only be used once.\n\nBest regards!"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.form.to_dict() or request.json
        print("Incoming Request Data:", data)

        res_encoded = data.get('res')
        if not res_encoded:
            return jsonify({"status": "error", "message": "Missing res parameter"}), 400

        # Decode Base64 payload
        decoded_bytes = base64.b64decode(res_encoded)
        decrypted_data = json.loads(decoded_bytes.decode('utf-8'))

        # Get the customer's actual email address
        customer_email = decrypted_data.get('email') or data.get('email')

        if not customer_email:
            print("[ERROR] Customer email address not found!")
            return jsonify({"status": "error", "message": "Email not found"}), 400

        # Generate license key and save to database (is_used = 0)
        license_key = generate_license_key()
        
        conn = sqlite3.connect('licenses.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO licenses (key, email, is_used) VALUES (?, ?, 0)", (license_key, customer_email))
        conn.commit()
        conn.close()

        # Send email to the customer
        if send_license_email(customer_email, license_key):
            print(f"[SUCCESS] License sent: {customer_email} -> {license_key}")
        else:
            print(f"[ERROR] License generated but failed to send email: {customer_email}")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"[ERROR] Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Endpoint for users to activate/check their license key (One-time use)
@app.route('/activate', methods=['POST'])
def activate_license():
    try:
        data = request.form.to_dict() or request.json
        license_key = data.get('key')

        if not license_key:
            return jsonify({"status": "error", "message": "License key is required"}), 400

        conn = sqlite3.connect('licenses.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Check if key exists
        cursor.execute("SELECT is_used FROM licenses WHERE key = ?", (license_key,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({"status": "error", "message": "Invalid license key"}), 404

        is_used = row[0]

        if is_used == 1:
            conn.close()
            return jsonify({"status": "error", "message": "This license key has already been used!"}), 400

        # Mark key as used (1) so it can never be used again
        cursor.execute("UPDATE licenses SET is_used = 1 WHERE key = ?", (license_key,))
        conn.commit()
        conn.close()

        print(f"[SUCCESS] License key activated successfully: {license_key}")
        return jsonify({"status": "success", "message": "License activated successfully!"}), 200

    except Exception as e:
        print(f"[ERROR] Error during activation: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
