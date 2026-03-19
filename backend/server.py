from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import requests
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Violation, Base 

app = FastAPI()

# 1. SETUP KONEKSI DATABASE
DATABASE_URL = "mysql+pymysql://root:@localhost/k3_project"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. KONFIGURASI TELEGRAM
TOKEN = "8707229189:AAEPf1wB8XJ3b-_HieOR23qsVBi85zBKiks"
CHAT_ID = "-1003886366274"

# 3. ANTI-SPAM
cooldown_cache = {}

# Kamus terjemahan 
LABEL_MAP = {
    "not_wearing_helmet": "Tidak Memakai Helm",
    "not_wearing_vest": "Tidak Memakai Rompi (Vest)",
    "not_wearing_mask": "Tidak Memakai Masker",
    "not_wearing_any_apd": "Tidak Memakai APD Lengkap",
    "attempt_remove_helmet": "Mencoba Melepas Helm",
    "attempt_remove_vest": "Mencoba Melepas Rompi",
    "attempt_remove_mask": "Mencoba Melepas Masker"
}

# Payload 
class ViolationData(BaseModel):
    camera_id: str
    label: str
    image_path: str
    id_pekerja: Optional[str] = "Tidak diketahui" 

def send_to_telegram(data: ViolationData):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    
    # Terjemahkan label AI ke Bahasa Indonesia
    jenis_pelanggaran = LABEL_MAP.get(data.label, data.label.replace("_", " ").title())
    
    caption = (
        f"⚠️ *PELANGGARAN K3 TERDETEKSI* ⚠️\n\n"
        f"⏰ *Waktu:* {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🆔 *ID Pekerja:* {data.id_pekerja}\n"
        f"📍 *Lokasi:* {data.camera_id}\n"
        f"👤 *Jenis:* {jenis_pelanggaran}\n"
    )

    try:
        with open(data.image_path, 'rb') as photo:
            payload = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
            requests.post(url, data=payload, files={'photo': photo})
    except FileNotFoundError:
        print(f"❌ ERROR: File gambar {data.image_path} tidak ditemukan!")

@app.post("/report-violation")
async def report_violation(data: ViolationData, background_tasks: BackgroundTasks):
    # CEK ANTI SPAM
    key = f"{data.camera_id}_{data.label}_{data.id_pekerja}"
    current_time = time.time()
    
    if key in cooldown_cache and (current_time - cooldown_cache[key] < 30):
        return {"status": "ignored", "reason": "Masih dalam cooldown (Anti-Spam)"}
    
    cooldown_cache[key] = current_time

    # SIMPAN KE DATABASE
    try:
        db = SessionLocal()
        db_item = Violation(
            camera_id=data.camera_id,
            id_pekerja=data.id_pekerja, # Simpan ID pekerja ke DB
            violation_type=data.label,
            image_path=data.image_path
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
    except Exception as e:
        print(f"❌ Gagal simpan ke database: {e}")
    finally:
        db.close()

    # KIRIM KE TELEGRAM 
    background_tasks.add_task(send_to_telegram, data)

    return {"status": "success", "message": "Data berhasil diproses Backend!"}