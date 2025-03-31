from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = FastAPI()

# ดึงค่า Token และ Secret จาก Environment
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    body = body.decode("utf-8")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200

# ฟังค์ชันตอบกลับหลักแบบอัจฉริยะพร้อมแนบลิงก์
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.lower()
    reply = generate_reply(user_msg)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# ฟังค์ชันตอบกลับตามคีย์เวิร์ดและแนบลิงก์ Affiliate

def generate_reply(msg):
    if any(word in msg for word in ["กำไล", "ข้อมือ", "เครื่องประดับ", "แหวน", "สร้อย"]):
        return (
            "กำไลดี ๆ เสริมลุคให้ดูดีขึ้นได้เยอะเลยครับ ✨\n"
            "ลองดูแบบนี้ไหม 👉 https://s.shopee.co.th/5fb3PDunCb"
        )
    elif any(word in msg for word in ["เสื้อผ้าชาย", "เสื้อยืด", "กางเกง", "สูท"]):
        return "👔 เสื้อผ้าผู้ชายแบบหล่อเท่มีสไตล์ คลิกดูเลย 👉 https://s.shopee.co.th/8zrT7bBLKl"
    elif any(word in msg for word in ["เสื้อผ้าหญิง", "กระโปรง", "เดรส", "แฟชั่น"]):
        return "👗 แฟชั่นผู้หญิงสุดน่ารัก ราคาน่ารักกว่า คลิกเลย 👉 https://s.shopee.co.th/AUgGuu4tJk"
    elif any(word in msg for word in ["สุขภาพ", "วิตามิน", "supplement"]):
        return "💪 สุขภาพดีเริ่มที่นี่เลยครับ 👉 https://s.shopee.co.th/9pQcMPzJ5S"
    elif any(word in msg for word in ["รับของเด็ดประจำวัน"]):
        return "🎁 ของเด็ดประจำวัน: เสื้อผ้าลดราคาจัดเต็ม! 👉 https://s.shopee.co.th/8zrT7bBLKl"
    else:
        return (
            "สวัสดีครับ ผมบัง AI ครับ 🧠\n"
            "สามารถถามผมได้ทุกเรื่อง ผมจะตอบแบบฉลาดขึ้นเรื่อย ๆ\n"
            "และถ้าคุณสนใจสินค้าอะไร ผมก็แนะนำให้ได้นะครับ 😉"
        )
