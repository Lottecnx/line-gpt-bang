from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import json
from datetime import datetime
from collections import defaultdict
import random

app = FastAPI()

# API Key
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

# ระบบจำข้อมูล
user_logs = defaultdict(list)
user_quota = {}
MAX_MESSAGES_PER_DAY = 20

# ลิงก์ Affiliate Shopee
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
    "เกมและอุปกรณ์เสริม": ["เกม", "จอย", "เพลย์"]
}

def find_affiliate_link(text):
    for category, keywords in category_keywords.items():
        if any(k in text for k in keywords):
            return f"\n\nลองดูเพิ่มเติมได้ที่นี่ 👉 {affiliate_links[category]}"
    return ""

def check_quota(user_id):
    today = datetime.now().date()
    if user_id not in user_quota or user_quota[user_id]["date"] != today:
        user_quota[user_id] = {"date": today, "count": 0}
    if user_quota[user_id]["count"] < MAX_MESSAGES_PER_DAY:
        user_quota[user_id]["count"] += 1
        return True
    return False

def get_response(user_id, user_text):
    user_logs[user_id].append(user_text)

    # ของเด็ดประจำวัน
    if "ของเด็ด" in user_text:
        category = random.choice(list(affiliate_links.keys()))
        return f"ของเด็ดวันนี้ บังแนะนำหมวด: {category} 🔥\n👉 {affiliate_links[category]}"

    messages = [{"role": "system", "content": '''
คุณคือ 'บัง' ผู้ช่วย AI ภาษาไทยที่ฉลาด เป็นกันเอง และใช้ภาษาง่าย ๆ เหมือนเพื่อนคุยกัน
- ตอบให้เข้าใจง่าย กระชับ ชัดเจน
- ไม่ต้องแนะนำตัว
- อย่าเขียนเยิ่นเย้อหรือวกวน
- ใช้ภาษาคนไทยทั่วไป ไม่ใช้คำยาก
- ถ้าผู้ใช้ถามเรื่องสินค้า หรือสิ่งของ ให้แนะนำแบบสุภาพ พร้อมแนบลิงก์ Shopee ถ้าเกี่ยวข้อง
- อย่าตอบเหมือน ChatGPT หรือพูดว่า "นี่คือตัวอย่าง" / "แน่นอน" / "ฉันสามารถ..." 
- อย่าพูดเกินจริง หรือบิดเบือน
'''}]
    for msg in user_logs[user_id][-5:]:
        messages.append({"role": "user", "content": msg})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    reply = response["choices"][0]["message"]["content"].strip()
    reply += find_affiliate_link(user_text)
    return reply

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
    print(f">>> {user_id}: {user_text}")

    if not check_quota(user_id):
        reply_text = (
            "วันนี้คุณใช้ครบ 20 ข้อความแล้วครับ 😢\n"
            "กลับมาใหม่พรุ่งนี้ หรือสมัคร Premium เพื่อใช้งานได้ไม่จำกัด!"
        )
    else:
        try:
            reply_text = get_response(user_id, user_text)
        except Exception as e:
            print(">>> GPT Error:", e)
            reply_text = "ขออภัยครับ บังยังตอบไม่ได้ตอนนี้ 🧠"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
