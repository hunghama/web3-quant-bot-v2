import requests
import pandas as pd
from datetime import datetime
import time

# ==========================================
# 🛑 BƯỚC 1: ĐIỀN THÔNG TIN TELEGRAM CỦA ÔNG VÀO ĐÂY
# ==========================================
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # <-- XÓA
CHAT_ID = "YOUR_CHAT_ID"          # <-- XÓA

URL = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"

def gui_tin_nhan_telegram(noi_dung):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": noi_dung}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def xuat_bao_cao_va_canh_bao():
    print("--- 🤖 KHỞI ĐỘNG MẮT THẦN TELEGRAM ---")
    try:
        response = requests.get(URL)
        data = response.json()
        
        data_da_sap_xep = sorted(data, key=lambda x: float(x.get('volume', 0)), reverse=True)
        danh_sach_rut_gon = []
        so_luong_ca_map = 0
        
        for market in data_da_sap_xep:
            volume = float(market.get('volume', 0))
            keo_du_doan = market.get('question')
            
            # Lọc lưu file (> 100$)
            if volume > 100:
                danh_sach_rut_gon.append({
                    'Thoi_Gian': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Keo_Du_Doan': keo_du_doan,
                    'Tong_Von_Cuoc_USD': volume
                })
            
            # 🚨 BÁO ĐỘNG CÁ MẬP VỀ TELEGRAM (> 10 TRIỆU ĐÔ)
            if volume > 10000000:
                thong_bao = f"🚨 PHÁT HIỆN CÁ MẬP POLYMARKET!\n🔥 Kèo: {keo_du_doan}\n💰 Volume: ${volume:,.0f}"
                gui_tin_nhan_telegram(thong_bao)
                print(f"🚀 Đã bắn tin nhắn về điện thoại: {keo_du_doan}")
                so_luong_ca_map += 1
        
        # Xuất file CSV
        thoi_gian_hien_tai = datetime.now().strftime("%d_%m_%Hh%M")
        ten_file = f"bao_cao_polymarket_{thoi_gian_hien_tai}.csv"
        pd.DataFrame(danh_sach_rut_gon).to_csv(ten_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ HOÀN TẤT! Đã lưu file {ten_file} và gửi {so_luong_ca_map} cảnh báo.")

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")

# Kích hoạt chương trình
# ==========================================
# 🛑 BƯỚC 2: KÍCH HOẠT AUTO-SCAN CHẠY NGẦM
# ==========================================
print("🚀 HỆ THỐNG AUTO-SCAN ĐÃ KHỞI ĐỘNG! (Nhấn Ctrl + C ở Terminal để tắt)")

while True:
    xuat_bao_cao_va_canh_bao()  # Bot bắt đầu quét Polymarket
    
    # Số phút ông muốn bot nghỉ ngơi trước khi quét vòng tiếp theo
    so_phut_cho = 30
    
    print(f"⏳ Đang theo dõi thị trường... Quét lại sau {so_phut_cho} phút nữa.")
    time.sleep(so_phut_cho * 60)  # Ép máy tính đếm ngược