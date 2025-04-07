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
