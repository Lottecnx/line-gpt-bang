from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import openai
import os
import json
from datetime import datetime
from collections import defaultdict
import random

app = FastAPI()

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

user_logs = defaultdict(list)
user_quota = {}
MAX_MESSAGES_PER_DAY = 20

affiliate_links = {
    "เสื้อผ้าชาย": "https://s.shopee.co.th/8zrT7bBLKl",
    "เสื้อผ้าหญิง": "https://s.shopee.co.th/AUgGuu4tJk",
    # ... (ตัดออกเพื่อความกระชับ)
}

category_keywords = {
    "เสื้อผ้าชาย": ["เสื้อยืด", "เสื้อเชิ้ต"],
    "เสื้อผ้าหญิง": ["เสื้อครอป", "กระโปรง"],
    # ... (ตัดออกเพื่อความกระชับ)
}

def find_affiliate_link(text):
    for category, keywords in category_keywords.items():
        if any(k in text for k in keywords):
            return affiliate_links[category]
    return affiliate_links["เสื้อผ้าชาย"]

def check_quota(user_id):
    today = datetime.now().date()
    if user_id not in user_quota or user_quota[user_id]["date"] != today:
        user_quota[user_id] = {"date": today, "count": 0}
    if user_quota[user_id]["count"] < MAX_MESSAGES_PER_DAY:
        user_quota[user_id]["count"] += 1
        return True
    return False

def generate_image(prompt):
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response["data"][0]["url"]
    except Exception as e:
        print("Image gen error:", e)
        return None

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
def handle_message(event):
    user_text = event.message.text.strip()
    user_id = event.source.user_id

    if not check_quota(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="วันนี้คุณใช้ครบ 20 ข้อความแล้วครับ 😢")
        )
        return

    if user_text.startswith("สร้างภาพ") or user_text.startswith("วาด"):
        prompt = user_text.replace("สร้างภาพ", "").replace("วาด", "").strip()
        image_url = generate_image(prompt)
        if image_url:
            aff_link = find_affiliate_link(prompt)
            full_url = f"https://sparkling-bienenstitch-535530.netlify.app/?img={image_url}&aff={aff_link}"

            flex_message = {
                "type": "flex",
                "altText": "ดูภาพเต็มพร้อมของเด็ด",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": image_url,
                        "size": "full",
                        "aspectRatio": "1:1",
                        "aspectMode": "cover"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "ดูภาพเต็มพร้อมของเด็ด", "weight": "bold", "size": "md"},
                            {"type": "button", "action": {"type": "uri", "label": "กดดูเลย", "uri": full_url}, "style": "primary"}
                        ]
                    }
                }
            }
            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text="ภาพจากบัง", contents=flex_message)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ขออภัยครับ บังสร้างภาพไม่สำเร็จ ลองใหม่อีกครั้งนะ")
            )
        return

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ส่ง 'สร้างภาพ แมวใส่หมวก' มาลองได้เลย!")
    )
