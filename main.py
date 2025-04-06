from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import openai
import os
import json
from datetime import datetime
from collections import defaultdict
import random
import requests
from io import BytesIO  # << สำคัญ

app = FastAPI()

# API Key
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

# ระบบจำข้อมูล
user_logs = defaultdict(list)
user_quota = {}
user_latest_image = {}
MAX_MESSAGES_PER_DAY = 20

# ตรวจสอบโควต้า
def check_quota(user_id):
    today = datetime.now().date()
    if user_id not in user_quota or user_quota[user_id]["date"] != today:
        user_quota[user_id] = {"date": today, "count": 0}
    if user_quota[user_id]["count"] < MAX_MESSAGES_PER_DAY:
        user_quota[user_id]["count"] += 1
        return True
    return False

# อัปโหลดภาพขึ้น Imgur
def upload_to_imgur(image_bytes):
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    files = {"image": image_bytes}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()["data"]["link"]
    return None

# ตอบกลับข้อความทั่วไป
def get_response(user_id, user_text):
    user_logs[user_id].append(user_text)

    if "ของเด็ด" in user_text:
        return "ของเด็ดวันนี้ บังขอแนะนำหมวดหมู่ยอดฮิต ลองดูใน Shopee ได้เลย!"

    # ถ้าผู้ใช้พิมพ์คำว่า “สร้างภาพการ์ตูน”
    if "สร้างภาพ" in user_text and user_id in user_latest_image:
        return f"ภาพของคุณพร้อมแล้วครับ 🎨\n👉 {user_latest_image[user_id]}"

    messages = [{"role": "system", "content": '''
คุณคือ 'บัง' ผู้ช่วย AI ภาษาไทยที่ฉลาด เป็นกันเอง และใช้ภาษาง่าย ๆ เหมือนเพื่อนคุยกัน
- ตอบให้เข้าใจง่าย กระชับ ชัดเจน
- ไม่ต้องแนะนำตัว
- ใช้ภาษาคนไทยทั่วไป ไม่ใช้คำยาก
'''}]
    for msg in user_logs[user_id][-5:]:
        messages.append({"role": "user", "content": msg})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = response["choices"][0]["message"]["content"].strip()
        return reply
    except:
        return "ขออภัยครับ บังยังตอบไม่ได้ตอนนี้ 🧠"

@app.post("/webhook")
async def callback(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    try:
        handler.handle(body.decode(), signature)
    except Exception as e:
        print(">>> Error:", e)
    return JSONResponse(content={"status": "ok"})

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    user_text = event.message.text.strip()
    print(f">>> {user_id}: {user_text}")

    if not check_quota(user_id):
        reply_text = "วันนี้คุณใช้ครบ 20 ข้อความแล้วครับ 😢\nกลับมาใหม่พรุ่งนี้นะครับ!"
    else:
        reply_text = get_response(user_id, user_text)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image_bytes = BytesIO(message_content.content).read()

    imgur_url = upload_to_imgur(image_bytes)
    if imgur_url:
        user_latest_image[user_id] = imgur_url
        reply_text = "รับภาพแล้วครับ! 📷\nพิมพ์ว่า 'สร้างภาพการ์ตูน' เพื่อดูภาพที่อัปโหลด"
    else:
        reply_text = "อัปโหลดภาพไม่สำเร็จครับ ลองใหม่อีกครั้งนะครับ"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
