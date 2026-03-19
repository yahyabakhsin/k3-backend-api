import cv2
import time
import requests
import os 
from ultralytics import YOLO

# Pastikan file best.pt ada di folder yang sama
model = YOLO("best.pt") 
cap = cv2.VideoCapture(0)
API_URL = "http://localhost:8000/report-violation"

# Cooldown lokal
last_saved = 0 

while True:
    ret, frame = cap.read()
    if not ret: 
        print("Gagal membaca kamera")
        break

    results = model(frame)
    
    for r in results:
        detected_labels = [model.names[int(box.cls[0])] for box in r.boxes]
        
        for label in set(detected_labels): 
            # Filter class sesuai label training (gue masukin 'person' buat lo ngetes)
            if label in ["no_helmet", "no_vest", "attempt_remove_mask", "person"]: 
                current_time = time.time()
                
                if current_time - last_saved > 5:
                    # Simpan gambar
                    img_name = f"temp_{int(current_time)}.jpg"
                    cv2.imwrite(img_name, frame)
                    
                    # INI KUNCI JAWABANNYA: Ambil Absolute Path (Alamat Lengkap File)
                    jalur_lengkap = os.path.abspath(img_name)
                    
                    payload = {
                        "camera_id": "Area Proyek A",
                        "label": label,
                        "image_path": jalur_lengkap, # Kirim alamat lengkap ke API
                        "id_pekerja": "191"
                    }
                    
                    try:
                        print(f"[{time.strftime('%H:%M:%S')}] Mengirim data '{label}' ke Server...")
                        res = requests.post(API_URL, json=payload)
                        print("Respon Server:", res.json())
                    except requests.exceptions.RequestException as e:
                        print("Gagal konek ke API Backend: Pastikan server.py lo udah jalan!")
                        
                    last_saved = current_time

    cv2.imshow("K3 AI Detector", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

cap.release()
cv2.destroyAllWindows()