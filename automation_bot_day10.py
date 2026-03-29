import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
import time
import json 
from datetime import datetime
from dotenv import load_dotenv
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# THỦ KHO CỦA ÔNG (Đã làm từ các ngày trước)
import database_manager

# ==========================================
# 1. CÀI ĐẶT MÔI TRƯỜNG & NHẬT KÝ (LOGGING)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "whale_bot.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

load_dotenv()

# LẤY CHÌA KHÓA TỪ FILE .env
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_LIMIT = os.getenv("API_FETCH_LIMIT", "100")
HEARTBEAT = int(os.getenv("HEARTBEAT_SECONDS", "60"))
WHALE_THRESHOLD = float(os.getenv("WHALE_THRESHOLD_USD", "5000"))
SUMMARY_INTERVAL = int(os.getenv("SUMMARY_INTERVAL_SECONDS", "3600"))

if not TOKEN or not CHAT_ID:
    logging.error("LỖI: Không tìm thấy Token Telegram trong két sắt (.env)!")
    exit()

API_URL = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit={API_LIMIT}" 
IMAGE_PATH = os.path.join(BASE_DIR, "whale_chart_live.png")
STATE_FILE = os.path.join(BASE_DIR, "market_state.json")

# ==========================================
# 2. MÁY CHỦ CHẠY NGẦM 24/7 (KEEP ALIVE)
# ==========================================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Whale Tracker Bot V2 is Alive 24/7!</h1>")
    def log_message(self, format, *args):
        pass

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    logging.info(f"Đã bật Web Server giả mạo trên cổng {port} để giữ Bot sống")
    server.serve_forever()

# ==========================================
# 3. CÁC HÀM LẤY DỮ LIỆU (SHIPPER)
# ==========================================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_state(df):
    state = dict(zip(df['question'], df['volume']))
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def get_data_from_api():
    """Hàm lấy dữ liệu kèo từ Polymarket"""
    try:
        response = requests.get(API_URL, timeout=15)
        if response.status_code == 200: return response.json() 
    except Exception as e:
        logging.error(f"Lỗi API Polymarket: {e}")
    return None

def get_btc_price():
    """HÀM MỚI (DAY 16): Hàm sang Binance lấy giá Bitcoin"""
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data["price"])
    except Exception as e:
        logging.error(f"Lỗi lấy giá BTC từ Binance: {e}")
        return 0

# ==========================================
# 4. CÁC HÀM GỬI THÔNG BÁO TELEGRAM
# ==========================================
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try: requests.post(url, data=payload, timeout=10)
    except Exception as e: logging.error(f"Lỗi gửi báo động: {e}")

def send_telegram_summary(message, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(image_path, 'rb') as photo:
            payload = {'chat_id': CHAT_ID, 'caption': message, 'parse_mode': 'Markdown'}
            files = {'photo': photo}
            requests.post(url, data=payload, files=files)
            logging.info("Đã gửi Báo cáo Tổng hợp định kỳ thành công!")
    except Exception as e: logging.error(f"Lỗi gửi báo cáo ảnh: {e}")

def create_chart(df_plot):
    plt.style.use('ggplot')
    plt.figure(figsize=(12, 8))
    bars = plt.barh(df_plot['question'], df_plot['volume'], color='#2ecc71')
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2, f' ${width:,.0f}', va='center', fontsize=10, fontweight='bold')
    plt.xlabel('Khối lượng giao dịch (USD)', fontweight='bold')
    plt.title(f'TOP 10 KÈO SÔI ĐỘNG NHẤT POLYMARKET\nCập nhật: {datetime.now().strftime("%d/%m/%Y %H:%M")}', fontweight='bold')
    plt.tight_layout()
    plt.savefig(IMAGE_PATH, dpi=300)
    plt.close()

# ==========================================
# 5. BỘ NÃO TRUNG TÂM (MAIN LOOP)
# ==========================================
def main():
    # 1. Bật máy chủ ngầm
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # 2. Khởi động thủ kho SQLite
    database_manager.init_db()
    
    logging.info("🚀 KHỞI ĐỘNG HỆ THỐNG WHALE TRACKER V2 (Tích hợp BINANCE & SQLITE) 🚀")
    last_summary_time = time.time() - SUMMARY_INTERVAL 
    
    # Vòng lặp vĩnh cửu
    while True:
        logging.info("Nhịp tim: Đang quét ngầm API...")
        raw_data = get_data_from_api()
        
        if raw_data:
            # --- XỬ LÝ DỮ LIỆU BẰNG PANDAS ---
            df = pd.DataFrame(raw_data)
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
            df['endDate'] = pd.to_datetime(df['endDate'], errors='coerce')
            now = pd.to_datetime(datetime.now(), utc=True)
            df_active = df[df['endDate'] > now]
            if df_active.empty: df_active = df

            previous_state = load_state()
            df_active['previous_volume'] = df_active['question'].map(previous_state).fillna(df_active['volume'])
            
            # TÍNH TOÁN LƯỢNG TIỀN BƠM VÀO
            df_active['volume_change'] = df_active['volume'] - df_active['previous_volume']
            
            # Lưu trạng thái ngắn hạn & dài hạn
            save_state(df_active)
            database_manager.save_data_to_db(df_active)

            # --- BỘ LỌC CÁ MẬP ---
            whales = df_active[df_active['volume_change'] >= WHALE_THRESHOLD]
            
            # NẾU CÓ CÁ MẬP -> RÚT SÚNG BẮN TELEGRAM
            if not whales.empty:
                logging.info(f"🚨 PHÁT HIỆN {len(whales)} CÁ MẬP! Đang réo còi báo động Telegram...")
                
                # Gọi Shipper Binance lấy giá
                gia_btc_hien_tai = get_btc_price()
                
                # Xây dựng tin nhắn cộng dồn (+=)
                alert_msg = f"🚨 *WHALE ALERT! PHÁT HIỆN DÒNG TIỀN ĐỘT BIẾN* 🚨\n\n"
                alert_msg += f"👑 *Giá BTC hiện tại:* `${gia_btc_hien_tai:,.0f}`\n"
                alert_msg += "━" * 20 + "\n\n"
                alert_msg += f"🔥 *{len(whales)} KÈO SÔI ĐỘNG NHẤT VỪA BỊ BƠM* 🔥\n\n"
                
                for _, row in whales.iterrows():
                    question = row['question']
                    if len(question) > 55: question = question[:52] + "..."
                    # --- BẮT ĐẦU CHÈN THÊM LOGIC PHÂN LOẠI (DAY 17) ---
                    vol_change = row['volume_change']
                    
                    # Áp dụng logic If/Elif/Else y hệt bài Quản lý Tướng
                    if vol_change >= 500000:       # Bơm nửa triệu đô trở lên
                        muc_do = "🔴 [SIÊU CÁ VOI]"
                    elif vol_change >= 50000:      # Bơm 50 ngàn đô trở lên
                        muc_do = "🟠 [CÁ MẬP]"
                    else:                          # Bơm dưới 50 ngàn đô
                        muc_do = "🟡 [CÁ CON]"
                    # --- KẾT THÚC CHÈN LOGIC ---

                    # Sửa lại tin nhắn để nối cái muc_do (icon) vào đầu câu
                    alert_msg += f"{muc_do} *{question}*\n"
                    alert_msg += f"💸 Vừa bơm: `+${vol_change:,.0f}`\n"
                    alert_msg += f"💰 Tổng Vol hiện tại: `${row['volume']:,.0f}`\n\n"
                    
                    logging.info(f"{muc_do} Bơm +${vol_change:,.0f} vào: {question}")
                alert_msg += f"⏱️ _Phát hiện trong {HEARTBEAT}s qua_"
                send_telegram_alert(alert_msg)

            # --- BÁO CÁO ĐỊNH KỲ TỔNG HỢP ---
            current_time = time.time()
            if current_time - last_summary_time >= SUMMARY_INTERVAL:
                logging.info("Đã đến giờ gửi Báo cáo Tổng hợp. Đang vẽ biểu đồ...")
                top_10_plot = df_active.sort_values('volume', ascending=False).head(10).sort_values('volume', ascending=True)
                create_chart(top_10_plot)
                top_5 = df_active.sort_values('volume', ascending=False).head(5)
                
                summary_msg = "📊 *BÁO CÁO TỔNG HỢP ĐỊNH KỲ* 📊\n"
                summary_msg += "━" * 25 + "\n\n"
                for i, row in top_5.iterrows():
                    question = row['question']
                    if len(question) > 60: question = question[:57] + "..."
                    summary_msg += f"*{i+1}. {question}*\n"
                    summary_msg += f"💰 Vol: `${row['volume']:,.0f}`\n\n"
                summary_msg += "🗄️ _Hệ thống Whale Tracker V2 - Lưu Kho SQLite 24/7_"
                
                send_telegram_summary(summary_msg, IMAGE_PATH)
                last_summary_time = current_time 

        # NGỦ ĐÔNG CHỜ NHỊP TIM TIẾP THEO
        logging.info(f"Ngủ {HEARTBEAT} giây cho nhịp tim tiếp theo...")
        time.sleep(HEARTBEAT)

if __name__ == "__main__":
    main()