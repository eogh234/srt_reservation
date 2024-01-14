import datetime
import requests

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1196005952135122982/YGu19gWuI2SAYRwQC2xfCBChiQV_nkJP8YMqWhtVMiY7mtW_8VO1widJ2SNt8L81VY-u"

def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)

def get_message():
    message = requests.get(DISCORD_WEBHOOK_URL)