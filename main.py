from flask import Flask, request, jsonify
import requests
import hashlib
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import logging

# --- Configuration & Styling ---
SECRET_SEED = "APIMPDS$9712Q"
IV_STR = "AP4123IMPDS@12768F"
API_URL = 'http://impds.nic.in/impdsmobileapi/api/getrationcard'
TOKEN = "91f01a0a96c526d28e4d0c1189e80459"
USER_AGENT = 'Dalvik/2.1.0 (Linux; U; Android 14; 22101320I Build/UKQ1.240624.001)'

# ✅ API Access Key (এটি সিক্রেট রাখুন)
ACCESS_KEY = "subh"

app = Flask(__name__)

# Logging setup for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Premium Utility Functions ---
def get_md5_hex(input_string: str) -> str:
    return hashlib.md5(input_string.encode('iso-8859-1')).hexdigest()

def generate_session_id() -> str:
    return "28" + datetime.now().strftime("%Y%m%d%H%M%S")

def encrypt_payload(plaintext_id: str, session_id: str) -> str:
    key_material = get_md5_hex(get_md5_hex(SECRET_SEED) + session_id)
    aes_key = hashlib.sha256(key_material.encode('utf-8')).digest()[:16]
    iv = IV_STR.encode('utf-8')[:16]
    
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    padded_data = pad(plaintext_id.encode('utf-8'), AES.block_size, style='pkcs7')
    ciphertext = cipher.encrypt(padded_data)
    
    return base64.b64encode(base64.b64encode(ciphertext)).decode('utf-8')

# --- Routes ---
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Premium Aadhaar Fetcher API is running",
        "developer": "SB Sakib"
    })

@app.route('/fetch', methods=['GET'])
def fetch():
    try:
        # 🛡️ Key Validation
        key = request.args.get("key", "").strip()
        if key != ACCESS_KEY:
            return jsonify({"status": "error", "message": "Unauthorized: Invalid API Key"}), 401

        # 🔍 Input Validation
        aadhaar_input = request.args.get("aadhaar", "").strip()
        if not aadhaar_input or not aadhaar_input.isdigit() or len(aadhaar_input) != 12:
            return jsonify({"status": "error", "message": "Invalid Aadhaar. Must be 12 digits."}), 400

        # ⚙️ Processing
        session_id = generate_session_id()
        encrypted_id = encrypt_payload(aadhaar_input, session_id)

        headers = {
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept-Encoding': 'gzip'
        }
        
        payload = {
            "id": encrypted_id,
            "idType": "U",
            "userName": "IMPDS",
            "token": TOKEN,
            "sessionId": session_id
        }

        # 🚀 External Request
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "data": response.json(),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "failed", 
                "message": f"Source server returned error {response.status_code}"
            }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": "Source server timed out"}), 504
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

# For local testing
if __name__ == '__main__':
    app.run(debug=True)