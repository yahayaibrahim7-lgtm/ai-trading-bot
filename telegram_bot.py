import requests
import time

API_URL = "http://127.0.0.1:5000/signal"
ADMIN_TOKEN = "my-admin-token"  # same as env


def get_users():
    res = requests.get(
        "http://127.0.0.1:5000/admin/users",
        headers={"Authorization": ADMIN_TOKEN}
    )
    return res.json()


def send_message(chat_id, message):
    BOT_TOKEN = "YOUR_BOT_TOKEN"

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": message
        }
    )


def run_bot():
    users = get_users()

    for user in users:
        if user["vip"] and user["chat_id"]:
            try:
                res = requests.get(API_URL, headers={
                    "Authorization": "USER_TOKEN_HERE"
                })

                signals = res.json()

                msg = "📊 VIP AI SIGNALS\n\n"

                for s in signals:
                    msg += f"{s['pair']} → {s['signal']} ({s['confidence']})\n"

                send_message(user["chat_id"], msg)

            except Exception as e:
                print("Error:", e)


while True:
    run_bot()
    time.sleep(300)