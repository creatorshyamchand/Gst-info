from flask import Flask, request, jsonify
import requests
import json
import re
import time
import base64
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
OWNER = "https://t.me/teamnexxon"
CREDIT_TEXT = "Developed by CREATOR SHYAMCHAND | @nexxonhackers"

# ---------------- GST HELPERS ----------------

def extract_pan_from_gst(gst_number):
    if len(gst_number) == 15:
        return gst_number[2:12]
    return None

def validate_gst_number(gst_number):
    gst_number = gst_number.upper().strip()
    if len(gst_number) != 15:
        return False, "GST number must be exactly 15 characters long"
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
    if not re.match(pattern, gst_number):
        return False, "Invalid GST number format"
    return True, "Valid GST number"

# ---------------- FETCH DATA ----------------

def fetch_gst_details(gst_number):
    # Base64 decoding for safety
    api_base_url = base64.b64decode("aHR0cHM6Ly9jbGVhcnRheC5pbi9mL2NvbXBsaWFuY2UtcmVwb3J0Lw==").decode('utf-8')
    search_page_url = base64.b64decode("aHR0cHM6Ly9jbGVhcnRheC5pbi9nc3QtbnVtYmVyLXNlYXJjaC8=").decode('utf-8')
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": search_page_url
    }

    session = requests.Session()

    try:
        # Step 1: Initial visit
        session.get(search_page_url, headers=headers, timeout=10)
        # Step 2: Fetch data
        api_url = f"{api_base_url}{gst_number}/"
        response = session.get(api_url, headers=headers, timeout=20)

        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# ---------------- API ROUTES ----------------

@app.route("/")
def home():
    return jsonify({
        "message": "GST Lookup API is Live",
        "usage": "/gst?number=GSTIN",
        "developer": CREDIT_TEXT,
        "meta": {"owner": OWNER}
    })

@app.route("/gst", methods=["GET"])
def gst_lookup():
    gst_number = request.args.get("number", "").upper().strip()

    if not gst_number:
        return jsonify({"success": False, "message": "GST number is required"}), 400

    is_valid, message = validate_gst_number(gst_number)
    if not is_valid:
        return jsonify({"success": False, "message": message}), 400

    data = fetch_gst_details(gst_number)
    if not data:
        return jsonify({"success": False, "message": "Failed to fetch GST details or Invalid GSTIN"}), 500

    # formatting response
    taxpayer_info = data.get('taxpayerInfo', {}) if data else {}
    
    formatted_data = {
        "gst_number": gst_number,
        "pan_number": extract_pan_from_gst(gst_number),
        "business_info": {
            "legal_name": taxpayer_info.get('lgnm'),
            "trade_name": taxpayer_info.get('tradeNam'),
            "constitution": taxpayer_info.get('ctb'),
            "taxpayer_type": taxpayer_info.get('dty'),
            "status": taxpayer_info.get('sts'),
            "registration_date": taxpayer_info.get('rgdt'),
            "cancellation_date": taxpayer_info.get('cxdt')
        },
        "nature_of_business": taxpayer_info.get('nba', []),
        "address": taxpayer_info.get('pradr', {}).get('addr', {}),
        "credits": CREDIT_TEXT
    }

    return jsonify({
        "success": True,
        "message": "Success",
        "data": formatted_data,
        "meta": {"owner": OWNER}
    })

# Vercel handler
app_handler = app
      
