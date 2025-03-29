from fastapi import FastAPI, Request
from pydantic import BaseModel
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from datetime import datetime

# Initialize
app = FastAPI()
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

# === PROMPT SETTINGS ===
SYSTEM_PROMPT = (
    "คุณคือ 'บัง' เป็นผู้ชายใจดี ฉลาด พูดเหมือน Lisa เวอร์ชันผู้ชาย แต่อ่านใจคนเก่งมาก "
    "บังจะช่วยตอบทุกคำถามอย่างสุภาพ เป็นกันเอง ถ้าเจอคำถามเกี่ยวกับสินค้า เช่น เสื้อผ้า เครื่องแต่งกาย แนะนำลิงก์ Affiliate ที่เกี่ยวข้องที่บันทึกไว้ได้เลย"
)

# === USER QUOTA TRACKING ===
user_quota = {}  # user_id: {"date": "YYYY-MM-DD", "count": int}
MAX_MESSAGES_PER_DAY = 5

# === AFFILIATE LINKS BY CATEGORY ===
affiliate_links = {
    "เสื้อ": "https://s.shopee.co.th/8zrT7bBLKl",
    "เสื้อผ้า": "https://s.shopee.co.th/8zrT7bBLKl",
    "เสื้อเชิ้ต": "https://s.shopee.co.th/8zrT7bBLKl",
    "เสื้อยืด": "https://s.shopee.co.th/8zrT7bBLKl",
    "เสื้อแขนยาว": "https://s.shopee.co.th/8zrT7bBLKl",
    "กางเกง": "https://s.shopee.co.th/8zrT7bBLKl",
    "แฟชั่นผู้ชาย": "https://s.shopee.co.th/8zrT7bBLKl",
    "ผู้ชาย": "https://s.shopee.co.th/8zrT7bBLKl",
    "แฟชั่นผู้หญิง": "https://s.shopee.co.th/AUgGuu4tJk",
    "ผู้หญิง": "https://s.shopee.co.th/AUgGuu4tJk",
    "กระโปรง": "https://s.shopee.co.th/AUgGuu4tJk",
    "เดรส": "https://s.shopee.co.th/AUgGuu4tJk",
    "เสื้อสายเดี่ยว": "https://s.shopee.co.th/AUgGuu4tJk",
    "เสื้อผ้าผู้หญิง": "https://s.shopee.co.th/AUgGuu4tJk"
}

def detect_category(text):
    for keyword in affiliate_links:
        if keyword in text:
            return keyword
    return None

def check_quota(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in user_quota or user_quota[user_id]["date"] != today:
        user_quota[user_id] = {"date": today, "count": 0}

    if user_quota[user_id]["count"] < MAX_MESSAGES_PER_DAY:
        user_quota[user_id]["count"] += 1
        return True
    return False

# === LINE WEBHOOK ===
@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    handler.handle(body.decode('utf-8'), signature)
    return "OK"

# === HANDLE MESSAGES ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text

    if not check_quota(user_id):
        reply = "วันนี้คุณใช้ครบ 5 ข้อความแล้วนะครับ พบกันใหม่พรุ่งนี้ครับ 😊"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]
        )
        reply_text = response.choices[0].message.content.strip()

        # แนบลิงก์ Affiliate ถ้ามีหมวดตรง
        category = detect_category(user_text)
        if category:
            reply_text += f"\n\n🛍 บังแนะนำลิงก์สำหรับ {category}: {affiliate_links[category]}"

    except Exception as e:
        reply_text = f"เกิดข้อผิดพลาดจาก GPT: {str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# === RUN FOR RENDER ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
