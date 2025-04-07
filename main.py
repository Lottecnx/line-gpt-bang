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
import requests

app = FastAPI()

# API Key
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

# ระบบจำข้อมูล
user_logs = defaultdict(list)
user_quota = {}
MAX_MESSAGES_PER_DAY = 20

# ลิงก์ Affiliate Shopee
affiliate_links = {
    "เสื้อผ้าชาย": "https://s.shopee.co.th/8zrT7bBLKl",
    ... # (คงไว้เหมือนเดิม)
}

category_keywords = {
    ... # (คงไว้เหมือนเดิม)
}

def find_affiliate_link(text):
    for category, keywords in category_keywords.items():
        if any(k in text for k in keywords):
            return affiliate_links[category]
    return affiliate_links["เสื้อผ้าชาย"]

def upload_to_imgur(image_url):
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    data = {"image": image_url}
    try:
        res = requests.post("https://api.imgur.com/3/image", headers=headers, data=data)
        if res.status_code == 200:
            return res.json()["data"]["link"]
        else:
            print(">>> Imgur upload failed:", res.text)
    except Exception as e:
        print(">>> Imgur Exception:", e)
    return None

def generate_image(prompt):
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        original_url = response["data"][0]["url"]
        print(">>> สร้างภาพ DALL·E สำเร็จ:", original_url)

        imgur_url = upload_to_imgur(original_url)
        if imgur_url:
            return imgur_url
        else:
            print(">>> ไม่ได้ imgur URL")
            return None

    except Exception as e:
        print(">>> ERROR สร้างภาพ:", e)
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
