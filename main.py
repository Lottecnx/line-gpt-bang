from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from collections import defaultdict
from datetime import datetime, timedelta
import openai
import os
import random
import asyncio

# LINE / OpenAI config
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# ---- ตั้งค่า ----
MAX_MESSAGES_PER_DAY = 20
user_quota = {}
premium_users = {}
user_logs = defaultdict(list)

# หมวดสินค้า + ลิงก์ Affiliate
affiliate_links = {
    "เสื้อผ้าชาย": "https://s.shopee.co.th/8zrT7bBLKl",
    "เสื้อผ้าหญิง": "https://s.shopee.co.th/AUgGuu4tJk",
    "เครื่องประดับ": "https://s.shopee.co.th/5fb3PDunCb"
}
category_keywords = {
    "เสื้อผ้าชาย": ["เสื้อยืด", "เสื้อเชิ้ต", "แฟชั่นผู้ชาย", "กางเกง", "ชุดชาย"],
    "เสื้อผ้าหญิง": ["เสื้อครอป", "กระโปรง", "แฟชั่นผู้หญิง", "เดรส", "ชุดหญิง"],
    "เครื่องประดับ": ["กำไล", "แหวน", "สร้อย", "ต่างหู", "จิวเวลรี่"]
}

# System Prompt
system_prompt = """
คุณคือ 'บัง' (Bang) ผู้ช่วย AI ภาษาไทย ใจดี ฉลาด พูดแบบเพื่อน
ตอบคำถามทุกเรื่องแบบชัดเจน กระชับ และไม่แนะนำตัวซ้ำบ่อย

หากผู้ใช้ถามเรื่องสินค้า ไลฟ์สไตล์ ให้แนะนำอย่างเป็นกันเอง
พร้อมแนบลิงก์ Affiliate ถ้าเกี่ยวข้องกับหมวด เช่น เสื้อผ้า, เครื่องประดับ ฯลฯ
ห้ามพูดยัดเยียด ห้ามขายตรง ให้แนบลิงก์ท้ายคำตอบแบบสุภาพ

ถ้ามีคำว่า "ของเด็ด" ให้สุ่มแนะนำหมวดสินค้า พร้อมแนบลิงก์ Shopee
ถ้าผู้ใช้พิมพ์ว่า "สมัคร Premium", "แจ้งโอน" หรือ "โอนแล้ว" ให้เพิ่มเป็น Premium
Premium ใช้ได้ไม่จำกัด 30 วัน และแจ้งเตือนก่อนหมด 1 วัน
"""

# ฟังก์ชันตรวจข้อความต่อวัน
def check_quota(user_id):
    today = datetime.now().date()
    if user_id in premium_users:
        if premium_users[user_id] >= today:
            return True
        else:
            del premium_users[user_id]
    if user_id not in user_quota or user_quota[user_id]["date"] != today:
        user_quota[user_id] = {"date": today, "count": 0}
    if user_quota[user_id]["count"] < MAX_MESSAGES_PER_DAY:
        user_quota[user_id]["count"] += 1
        return True
    return False

# ฟังก์ชันแนบลิงก์ Affiliate แบบสุภาพ
def find_affiliate_link(text):
    for category, keywords in category_keywords.items():
        if any(k in text for k in keywords):
            return f"\n\nลองดูเพิ่มเติมได้ครับ 👉 {affiliate_links[category]}"
    return ""

# ฟังก์ชันหลักในการตอบ
async def chat_with_gpt(user_id, user_text):
    if user_id not in user_logs:
        user_logs[user_id] = []
    user_logs[user_id].append(user_text)

    # กรณีพิมพ์ว่า "ของเด็ด"
    if "ของเด็ด" in user_text:
        category = random.choice(list(affiliate_links.keys()))
        return f"ของเด็ดวันนี้ บังแนะนำหมวด: {category} 🔥\nดูเลย 👉 {affiliate_links[category]}"

    messages = [{"role": "system", "content": system_prompt}]
    for msg in user_logs[user_id][-5:]:
        messages.append({"role": "user", "content": msg})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.8
    )
    reply = response.choices[0].message.content.strip()
    reply += find_affiliate_link(user_text)
    return reply

# Webhook
@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    try:
        handler.handle(body.decode(), signature)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)
    return JSONResponse(content={"message": "OK"})

# ตอบกลับข้อความ
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text.strip()
    today = datetime.now().date()

    # Premium ระบบ
    if "สมัคร premium" in user_text.lower():
        reply_text = (
            "สมัคร Premium ได้เลยครับ 🎉\n"
            "โอน 59 บาท มาที่:\n"
            "🏦 ธ.กรุงเทพ 6130393776 (สุภาพ สิริวัฒร์)\n"
            "📱 พร้อมเพย์ 0803179007\n\n"
            "พอโอนแล้วพิมพ์ว่า 'แจ้งโอน' หรือ 'โอนแล้ว' ได้เลยครับ!"
        )
    elif "แจ้งโอน" in user_text or "โอนแล้ว" in user_text:
        premium_users[user_id] = today + timedelta(days=30)
        reply_text = f"ขอบคุณครับ! บังอัปเกรดคุณเป็น Premium แล้ว 🎉 ใช้ได้ถึง {premium_users[user_id]}"
    elif user_id in premium_users and premium_users[user_id] == today + timedelta(days=1):
        reply_text = "📌 พรุ่งนี้ Premium ของคุณจะหมดอายุแล้วนะครับ ถ้าอยากต่อ พิมพ์ว่า 'สมัคร Premium' ได้เลยครับ!"
    elif not check_quota(user_id):
        reply_text = (
            "วันนี้คุณใช้ครบ 20 ข้อความแล้วครับ 😢\n"
            "ถ้าต้องการใช้งานแบบไม่จำกัด พิมพ์ว่า 'สมัคร Premium' ได้เลยครับ!"
        )
    else:
        reply_text = asyncio.run(chat_with_gpt(user_id, user_text))

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
