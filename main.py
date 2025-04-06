from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
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
user_latest_image = {}  # จำภาพล่าสุดของแต่ละ user
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

def upload_to_imgur(image_data):
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    response = requests.post(url, headers=headers, files={"image": image_data})
    if response.status_code == 200:
        return response.json()["data"]["link"]
    return None

def get_response(user_id, user_text):
    user_logs[user_id].append(user_text)

    if "ของเด็ด" in user_text:
        category = random.choice(list(affiliate_links.keys()))
        return f"ของเด็ดวันนี้ บังแนะนำหมวด: {category} 🔥\n👉 {affiliate_links[category]}"

    if "สร้างภาพ" in user_text and user_id in user_latest_image:
        latest_image_url = user_latest_image[user_id]
        redirect_url = f"https://your-project-name.onrender.com/redirect?img={latest_image_url}"
        return f"ภาพของคุณพร้อมแล้วครับ 🎨\nดูได้ที่นี่ 👉 {redirect_url}"

    messages = [{"role": "system", "content": '''
คุณคือ 'บัง' ผู้ช่วย AI ภาษาไทยที่ฉลาด เป็นกันเอง และใช้ภาษาง่าย ๆ เหมือนเพื่อนคุยกัน
- ตอบให้เข้าใจง่าย กระชับ ชัดเจน
- ไม่ต้องแนะนำตัว
- ใช้ภาษาคนไทยทั่วไป ไม่ใช้คำยาก
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
def handle_text(event):
    user_text = event.message.text.strip()
    user_id = event.source.user_id
    print(f">>> {user_id}: {user_text}")

    if not check_quota(user_id):
        reply_text = "วันนี้คุณใช้ครบ 20 ข้อความแล้วครับ 😢\nกลับมาใหม่พรุ่งนี้นะครับ!"
    else:
        try:
            reply_text = get_response(user_id, user_text)
        except Exception as e:
            print(">>> GPT Error:", e)
            reply_text = "ขออภัยครับ บังยังตอบไม่ได้ตอนนี้ 🧠"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id).content
    imgur_url = upload_to_imgur(image_content)
    if imgur_url:
        user_latest_image[user_id] = imgur_url
        reply_text = "รับภาพแล้วครับ! 📷\nพิมพ์ว่า 'สร้างภาพการ์ตูน' เพื่อแปลงภาพ"
    else:
        reply_text = "อัปโหลดภาพไม่สำเร็จครับ ลองใหม่อีกครั้งนะครับ"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

@app.get("/redirect")
async def redirect_image(img: str):
    if not img.startswith("http"):
        return {"error": "ลิงก์ไม่ถูกต้อง"}
    return RedirectResponse(url=img)
