from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
import random
import asyncio

app = FastAPI()

# ดึง KEY จาก Environment
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# -------------------------------
# ระบบเก็บข้อมูล
user_logs = defaultdict(list)
user_quota = {}
premium_users = {}
MAX_MESSAGES_PER_DAY = 20

# -------------------------------
# ลิงก์ Affiliate + คำค้น
affiliate_links = {
    "เสื้อผ้าชาย": "https://s.shopee.co.th/8zrT7bBLKl",
    "เสื้อผ้าหญิง": "https://s.shopee.co.th/AUgGuu4tJk",
    "ความงามและของใช้ส่วนตัว": "https://s.shopee.co.th/6pn0mo0IPC",
    "ผลิตภัณฑ์เพื่อสุขภาพ": "https://s.shopee.co.th/9pQcMPzJ5S",
    "กระเป๋า": "https://s.shopee.co.th/VsxFNIoNU",
    "รองเท้าหญิง": "https://s.shopee.co.th/LZX3IMFKa",
    "รองเท้าชาย": "https://s.shopee.co.th/3fpz1UdQUH",
    "เครื่องประดับ": "https://s.shopee.co.th/5fb3PDunCb",
    "นาฬิกาและแว่นตา": "https://s.shopee.co.th/1qOKqFpHn6",
    "ของใช้ในบ้าน": "https://s.shopee.co.th/7pfXzLIvHW",
    "อุปกรณ์อิเล็กทรอนิกส์": "https://s.shopee.co.th/3AtiQoUBQY",
    "มือถือและแท็บแล็ต": "https://s.shopee.co.th/10pDqtS14q",
    "เครื่องใช้ไฟฟ้าภายในบ้าน": "https://s.shopee.co.th/6fTabPLcRN",
    "คอมพิวเตอร์และแล็ปท็อป": "https://s.shopee.co.th/3LD8dL6IKX",
    "กล้องและอุปกรณ์ถ่ายภาพ": "https://s.shopee.co.th/4fiWDtLTtI",
    "อาหารและเครื่องดื่ม": "https://s.shopee.co.th/2qGs2a53J2",
    "ของเล่น สินค้าแม่และเด็ก": "https://s.shopee.co.th/40SpQnXIc4",
    "กีฬาและกิจกรรมกลางแจ้ง": "https://s.shopee.co.th/VsxGQacXn",
    "สัตว์เลี้ยง": "https://s.shopee.co.th/4L5fpXcHlQ",
    "เกมและอุปกรณ์เสริม": "https://s.shopee.co.th/2LKbRvUjzF",
    "ยานยนต์": "https://s.shopee.co.th/10pDrXCCbA",
    "เครื่องเขียน หนังสือ และงานอดิเรก": "https://s.shopee.co.th/5VHdDqybQb",
    "ตั๋วและบัตรกำนัล": "https://s.shopee.co.th/60DtoqH5Au"
}
category_keywords = {
    "เสื้อผ้าชาย": ["เสื้อยืด", "เสื้อเชิ้ต", "แฟชั่นผู้ชาย", "กางเกง"],
    "เสื้อผ้าหญิง": ["เสื้อครอป", "กระโปรง", "แฟชั่นผู้หญิง", "เดรส"],
    "ความงามและของใช้ส่วนตัว": ["ครีม", "สกินแคร์", "ลิปสติก"],
    "ผลิตภัณฑ์เพื่อสุขภาพ": ["วิตามิน", "อาหารเสริม", "สุขภาพ"],
    "กระเป๋า": ["กระเป๋าสะพาย", "กระเป๋าเงิน"],
    "รองเท้าหญิง": ["รองเท้าผู้หญิง", "ส้นสูง"],
    "รองเท้าชาย": ["รองเท้าผู้ชาย", "รองเท้าหนัง"],
    "เครื่องประดับ": ["กำไล", "แหวน", "ต่างหู", "จิวเวลรี่"],
    "นาฬิกาและแว่นตา": ["นาฬิกา", "แว่นตา"],
    "ของใช้ในบ้าน": ["หมอน", "ที่นอน", "ของแต่งบ้าน"],
    "อุปกรณ์อิเล็กทรอนิกส์": ["หูฟัง", "ลำโพง", "อิเล็กทรอนิกส์"],
    "มือถือและแท็บแล็ต": ["มือถือ", "โทรศัพท์", "ไอโฟน"],
    "เครื่องใช้ไฟฟ้าภายในบ้าน": ["พัดลม", "ไมโครเวฟ", "หม้อทอด"],
    "คอมพิวเตอร์และแล็ปท็อป": ["โน้ตบุ๊ก", "แล็ปท็อป", "PC"],
    "กล้องและอุปกรณ์ถ่ายภาพ": ["กล้อง", "เลนส์", "ขาตั้งกล้อง"],
    "อาหารและเครื่องดื่ม": ["ขนม", "เครื่องดื่ม", "กาแฟ"],
    "ของเล่น สินค้าแม่และเด็ก": ["ของเล่น", "ผ้าอ้อม", "แม่และเด็ก"],
    "กีฬาและกิจกรรมกลางแจ้ง": ["ออกกำลังกาย", "ฟิตเนส", "จักรยาน"],
    "สัตว์เลี้ยง": ["อาหารแมว", "อาหารหมา", "ของสัตว์เลี้ยง"],
    "เกมและอุปกรณ์เสริม": ["เกม", "จอย", "เพลย์"],
    "ยานยนต์": ["ยางรถ", "ของแต่งรถ", "รถยนต์"],
    "เครื่องเขียน หนังสือ และงานอดิเรก": ["ปากกา", "หนังสือ", "งานอดิเรก"],
    "ตั๋วและบัตรกำนัล": ["บัตรของขวัญ", "คูปอง"]
}

# -------------------------------
# SYSTEM PROMPT
system_prompt = """
คุณคือ 'บัง' ผู้ช่วย AI ภาษาไทยที่สุภาพ ตอบทุกคำถามให้ฉลาด เข้าใจง่าย
ห้ามแนะนำตัวซ้ำ ห้ามขายของตรง ๆ แต่ถ้ามีคำเกี่ยวข้อง ให้แนบลิงก์ Shopee แบบสุภาพ

ถ้าผู้ใช้พิมพ์ว่า "ของเด็ด" หรือ "ของเด็ดวันนี้" ให้สุ่มแนะนำหมวดและแนบลิงก์
ถ้าพิมพ์ว่า "สมัคร Premium", "โอนแล้ว", "แจ้งโอน" → ให้เพิ่มเป็น Premium 30 วัน
"""

# -------------------------------
def find_affiliate_link(text):
    for category, keywords in category_keywords.items():
        if any(k in text for k in keywords):
            return f"\n\nลองดูเพิ่มเติมได้ที่นี่ 👉 {affiliate_links[category]}"
    return ""

def check_quota(user_id):
    today = datetime.now().date()
    if user_id in premium_users and premium_users[user_id] >= today:
        return True
    if user_id not in user_quota or user_quota[user_id]["date"] != today:
        user_quota[user_id] = {"date": today, "count": 0}
    if user_quota[user_id]["count"] < MAX_MESSAGES_PER_DAY:
        user_quota[user_id]["count"] += 1
        return True
    return False

async def chat_with_gpt(user_id, user_text):
    if user_id not in user_logs:
        user_logs[user_id] = []

    user_logs[user_id].append(user_text)

    if "ของเด็ด" in user_text:
        category = random.choice(list(affiliate_links.keys()))
        return f"ของเด็ดวันนี้ บังแนะนำหมวด: {category} 🔥\n👉 {affiliate_links[category]}"

    messages = [{"role": "system", "content": system_prompt}]
    for msg in user_logs[user_id][-5:]:
        messages.append({"role": "user", "content": msg})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.8
    )
    reply = response["choices"][0]["message"]["content"].strip()
    reply += find_affiliate_link(user_text)
    return reply

# -------------------------------
@app.post("/webhook")
async def callback(request: Request):
    body = await request.body()
    body_str = body.decode("utf-8")
    json_body = json.loads(body_str)
    print("\n>>> Webhook Received:", json.dumps(json_body, indent=2, ensure_ascii=False))

    signature = request.headers.get("X-Line-Signature")
    try:
        handler.handle(body_str, signature)
    except Exception as e:
        print(">>> Error in handler:", e)
    return JSONResponse(content={"status": "ok"})

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    user_id = event.source.user_id
    today = datetime.now().date()
    print(f"\n>>> Message from {user_id}: {user_text}")

    # Premium
    if "สมัคร premium" in user_text.lower():
        reply_text = (
            "สมัคร Premium ได้เลยครับ 🎉\n"
            "โอน 59 บาท มาที่:\n"
            "🏦 ธ.กรุงเทพ 6130393776 (สุภาพ สิริวัฒร์)\n"
            "📱 พร้อมเพย์ 0803179007\n\n"
            "พอโอนแล้วพิมพ์ว่า 'แจ้งโอน' หรือ 'โอนแล้ว' ได้เลยครับ!"
        )
    elif "โอนแล้ว" in user_text or "แจ้งโอน" in user_text:
        premium_users[user_id] = today + timedelta(days=30)
        reply_text = f"ขอบคุณครับ! บังอัปเกรดคุณเป็น Premium แล้ว 🎉 ใช้ได้ถึง {premium_users[user_id]}"
    elif user_id in premium_users and premium_users[user_id] == today + timedelta(days=1):
        reply_text = "📌 Premium ของคุณจะหมดอายุพรุ่งนี้นะครับ"
    elif not check_quota(user_id):
        reply_text = "วันนี้คุณใช้ครบ 20 ข้อความแล้วครับ 😢\nหากต้องการไม่จำกัด พิมพ์ว่า 'สมัคร Premium'"
    else:
        reply_text = asyncio.run(chat_with_gpt(user_id, user_text))

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
