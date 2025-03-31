# main.py (พร้อมใช้งานบน Render, ตอบผ่าน LINE, เชื่อม GPT พร้อม Log ครบ)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
import uvicorn
import json

app = FastAPI()

# ดึง KEY จาก Environment
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

@app.get("/")
async def root():
    return {"message": "LINE GPT Bot พร้อมใช้งาน!"}

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
    user_text = event.message.text
    user_id = event.source.user_id
    print(f"\n>>> Message from {user_id}: {user_text}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "คุณคือผู้ช่วยชื่อ 'บัง' เป็นผู้ชายใจดี ตอบเหมือน Lisa แต่เป็นเวอร์ชันผู้ชาย"},
                {"role": "user", "content": user_text}
            ]
        )
        reply_text = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(">>> GPT ERROR:", e)
        reply_text = "ขอโทษครับ บังยังไม่สามารถตอบคำถามนี้ได้ในตอนนี้ 🧠"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# รันบน Render
if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
