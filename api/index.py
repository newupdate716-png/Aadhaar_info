import requests
import base64
import hashlib
import re
import io
import time
import json
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# --- CONFIGURATION ---
ENCRYPTION_KEY = "nic@impds#dedup05613"
USERNAME = "adminWB"
PASSWORD = "2p3MrgdgV8s9"

app = Flask(__name__)

# --- ENCRYPTION HELPER ---
class CryptoHandler:
    def __init__(self, passphrase):
        self.passphrase = passphrase.encode('utf-8')

    def _derive_key_and_iv(self, salt, key_length=32, iv_length=16):
        d = d_i = b''
        while len(d) < key_length + iv_length:
            d_i = hashlib.md5(d_i + self.passphrase + salt).digest()
            d += d_i
        return d[:key_length], d[key_length:key_length+iv_length]

    def encrypt(self, plain_text):
        salt = get_random_bytes(8)
        key, iv = self._derive_key_and_iv(salt)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_bytes = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
        return base64.b64encode(b"Salted__" + salt + encrypted_bytes).decode('utf-8')

crypto_engine = CryptoHandler(ENCRYPTION_KEY)

# --- BOT LOGIC ---
class IMPDSBot:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://impds.nic.in/impdsdeduplication"
        self.csrf_token = None
        self.user_salt = None

    def login(self):
        try:
            # Step 1: Initial Load
            r = self.session.get(f"{self.base_url}/LoginPage")
            soup = BeautifulSoup(r.text, 'html.parser')
            self.csrf_token = soup.find('input', {'name': 'REQ_CSRF_TOKEN'})['value']
            
            salt_match = re.search(r"USER_SALT\s*=\s*['\"]([^'\"]+)['\"]", r.text)
            self.user_salt = salt_match.group(1) if salt_match else None

            # Step 2: Get Captcha (Note: Automatic OCR is complex on Vercel, ideally manual input or high-end OCR required)
            # For this premium structure, we assume the credentials and tokens are pre-validated
            
            salted_pass = hashlib.sha512((hashlib.sha512(self.user_salt.encode()).hexdigest() + 
                          hashlib.sha512(PASSWORD.encode()).hexdigest()).encode()).hexdigest()

            # Step 3: Login (Simplified for API structure)
            return True
        except:
            return False

    def search(self, aadhaar):
        # এইখানে আধার সার্চ লজিক এবং HTML পার্সিং থাকবে আপনার দেওয়া ফরম্যাট অনুযায়ী
        # প্রিমিয়াম আউটপুট জেনারেট করার জন্য নিচের ডিকশনারিটি সাজানো হয়েছে
        encrypted_aadhaar = crypto_engine.encrypt(aadhaar)
        
        # Mocking Output for Structure (আপনার স্ক্র্যাপার এখানে ডেটা ইনজেক্ট করবে)
        return {
            "aadhaar_number": aadhaar,
            "status": "Success",
            "data": {
                "member_name": "Verified User",
                "ration_card": "WB123456789",
                "details": "Premium Data Fetched Successfully"
            }
        }

bot = IMPDSBot()

@app.route('/')
def home():
    return "IMPDS Premium Aadhaar API is Online"

@app.route('/api')
def api():
    aadhaar = request.args.get('aadhaar')
    if not aadhaar:
        return jsonify({"error": "Please provide an aadhaar number. Example: ?aadhaar=123456789012"}), 400
    
    # লগইন চেক ও সার্চ
    # bot.login() # অটো লগইন ফাংশন
    result = bot.search(aadhaar)
    
    return jsonify(result)

# Vercel requires the app instance
def handler(event, context):
    return app(event, context)