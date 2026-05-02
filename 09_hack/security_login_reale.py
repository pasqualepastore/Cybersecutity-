from flask import Flask, request, jsonify
from flask_limiter import Limiter
import logging
import bcrypt
import time

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_real_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

limiter = Limiter(
    key_func=get_real_ip,
    app=app,
    storage_uri="redis://localhost:6379",
    strategy="fixed-window"
)

# 🔐 “DB simulato”
stored_username = "admin"
stored_password_hash = bcrypt.hashpw(b"cyber_secure_2024", bcrypt.gensalt())

# 🚨 memoria temporanea tentativi falliti
failed_attempts = {}
BLOCK_TIME = 60  # secondi di blocco dopo troppi errori

def is_blocked(ip):
    if ip in failed_attempts:
        attempts, last_time = failed_attempts[ip]

        if attempts >= 5 and time.time() - last_time < BLOCK_TIME:
            return True

        # reset dopo tempo
        if time.time() - last_time >= BLOCK_TIME:
            failed_attempts[ip] = [0, time.time()]

    return False

def register_fail(ip):
    if ip not in failed_attempts:
        failed_attempts[ip] = [1, time.time()]
    else:
        failed_attempts[ip][0] += 1
        failed_attempts[ip][1] = time.time()


@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute; 20 per hour")
def login():
    ip = get_real_ip()

    # 🚫 blocco temporaneo IP
    if is_blocked(ip):
        return jsonify({"errore": "IP temporaneamente bloccato"}), 429

    data = request.get_json()

    if not data:
        return jsonify({"errore": "JSON richiesto"}), 400

    username = data.get('username')
    password = data.get('password')

    logging.info(f"Login attempt - user={username} ip={ip}")

    if username == stored_username and bcrypt.checkpw(password.encode(), stored_password_hash):
        # reset tentativi su successo
        failed_attempts.pop(ip, None)

        return jsonify({"stato": "successo"}), 200

    # ❌ fallito
    register_fail(ip)

    # 🔥 piccolo delay anti brute force
    time.sleep(1.5)

    return jsonify({"stato": "errore", "msg": "Credenziali errate"}), 401


if __name__ == '__main__':
    print("🔥 Server Sicuro Attivo su http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)

#Cosa hai aggiunto davvero (importante)
# 1. Block temporaneo IP
#dopo 5 tentativi → blocco 60s
#non solo rate limit → difesa doppia

# 2. Slow down attack
#time.sleep(1.5)

 #questo distrugge:
#brute force veloce
#script curl aggressivi
#bot semplici

# 3. Tracking tentativi
#memoria per IP
#reset automatico dopo tempo

# 4. Reset su login corretto

#Se entri giusto:
#pulisce storico tentativi