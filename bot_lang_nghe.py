import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # Cần Chat ID để biết trả lời vào đâu

print("==============================================")
print("🎧 TRẠM RADAR V2: LẮNG NGHE & PHẢN HỒI LỆNH")
print("==============================================\n")

def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        data = requests.get(url, timeout=5).json()
        return float(data["price"])
    except:
        return 0

def gui_tin_nhan_tra_loi(noi_dung_tra_loi):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': noi_dung_tra_loi, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)

def doc_tin_nhan_moi_nhat():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        phan_hoi = requests.get(url).json()
        danh_sach_tin_nhan = phan_hoi.get("result", [])
        
        if len(danh_sach_tin_nhan) > 0:
            tin_cuoi_cung = danh_sach_tin_nhan[-1]
            print("\n📦 CỤC DỮ LIỆU GỐC TỪ TELEGRAM TRÔNG NHƯ SAU:")
            print(tin_cuoi_cung)
            print("-" * 30)
            
            
            
            nguoi_gui = tin_cuoi_cung["message"]["from"]["first_name"]
            return nguoi_gui, noi_dung
        return None, None
    except:
        return None, None

if __name__ == "__main__":
    print("📲 Đang chờ Hùng ra lệnh từ điện thoại...\n")
    tin_cu_nhat = "" 
    
    while True:
        nguoi_gui, noi_dung = doc_tin_nhan_moi_nhat()
        
        if noi_dung and noi_dung != tin_cu_nhat:
            print(f"👤 Sếp {nguoi_gui} vừa ra lệnh: {noi_dung}")
            
            # --- BỘ NÃO XỬ LÝ LỆNH CỦA BOT ---
            lenh = noi_dung.lower() # Chuyển hết thành chữ thường cho dễ xét
            
            if "gia" in lenh or "btc" in lenh:
                print("-> Đang chạy đi lấy giá BTC để trả lời sếp...")
                gia_hien_tai = get_btc_price()
                cau_tra_loi = f"Dạ báo cáo sếp {nguoi_gui}, giá Bitcoin hiện tại đang là: `${gia_hien_tai:,.0f}` 🚀"
                gui_tin_nhan_tra_loi(cau_tra_loi)
                print("-> Đã trả lời xong!\n")
                
            elif "chao" in lenh or "hello" in lenh:
                gui_tin_nhan_tra_loi(f"Chào sếp {nguoi_gui}! Trạm Radar V2 đang hoạt động ổn định! 🫡")
            elif "ngu" in lenh:
                gui_tin_nhan_tra_loi(f"Sếp {nguoi_gui} ơi, em là bot nghe lệnh chứ không phải bot ngu đâu ạ! 😄")   
            else:
                gui_tin_nhan_tra_loi("Sếp nhắn gì em chưa hiểu? Sếp thử nhắn 'gia' xem sao nhé! 😅")
            
            tin_cu_nhat = noi_dung 
            
        time.sleep(2)