from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "สวัสดีครับ ผมชื่อบัง (Bang) พร้อมให้บริการ 🤖"}

@app.post("/webhook")
async def webhook(req: Request):
    body = await req.body()
    print("🔔 ได้รับข้อมูลจาก LINE:", body)
    return JSONResponse(content={"status": "ok"}, status_code=200)
