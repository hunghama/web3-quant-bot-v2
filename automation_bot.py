import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
import glob
import time
import logging
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG (CONFIG) ---
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
CHECK_INTERVAL_SECONDS = 3600  # Kiểm tra dữ liệu mỗi 1 tiếng (3600 giây)

# Kỹ thuật Senior: Tự động xác định thư mục làm việc
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_NAME = os.path.join(BASE_DIR, "whale_chart.png")
LOG_FILE = os.path.join(BASE_DIR, "bot_log.txt")

# Thiết lập hệ thống ghi nhật ký (Logging) để theo dõi lỗi khi chạy ngầm
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_latest_csv_file(directory):
    """Tìm file CSV mới nhất dựa trên thời gian chỉnh sửa."""
    search_pattern = os.path.join(directory, "bao_cao_polymarket_*.csv")
    files = glob.glob(search_pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def send_telegram_photo(token, chat_id, image_path, caption):
    """Gửi ảnh qua Telegram với cơ chế thử lại (Retry logic)."""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    for attempt in range(3):  # Thử lại tối đa 3 lần nếu mạng lỗi
        try:
            with open(image_path, 'rb') as photo:
                payload = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                files = {'photo': photo}
                response = requests.post(url, data=payload, files=files, timeout=30)
                
                if response.status_code == 200:
                    logging.info("✅ Gửi biểu đồ thành công!")
                    return True
                else:
                    logging.error(f"❌ Telegram phản hồi lỗi: {response.text}")
        except Exception as e:
            logging.warning(f"⚠️ Thử lại lần {attempt+1} do lỗi mạng: {e}")
            time.sleep(5)
    return False

def run_pipeline():
    """Quy trình xử lý dữ liệu lõi."""
    data_file = get_latest_csv_file(BASE_DIR)
    
    if not data_file:
        logging.warning("🔍 Không tìm thấy file dữ liệu mới.")
        return

    file_name = os.path.basename(data_file)
    logging.info(f"🔄 Đang xử lý file: {file_name}")

    try:
        # 1. Đọc dữ liệu
        df = pd.read_csv(data_file)
        
        # 2. Xử lý logic cá mập
        threshold = 10000000  # 10 triệu USD
        ca_map = df[df['Tong_Von_Cuoc_USD'] > threshold].sort_values('Tong_Von_Cuoc_USD', ascending=True)

        if ca_map.empty:
            logging.info("ℹ️ Chưa có biến động nào vượt ngưỡng 10M USD.")
            return

        # 3. Vẽ biểu đồ nâng cao
        plt.style.use('ggplot') # Dùng style đẹp hơn
        fig, ax = plt.subplots(figsize=(12, 8))
        
        bars = ax.barh(ca_map['Keo_Du_Doan'], ca_map['Tong_Von_Cuoc_USD'], color='#3498db')
        
        # Thêm nhãn giá trị vào cuối mỗi cột
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                    f' ${width:,.0f}', va='center', fontsize=10, fontweight='bold')

        ax.set_xlabel('Tổng Vốn Cược (USD)')
        ax.set_title(f'BÁO CÁO DÒNG TIỀN CÁ MẬP\nNguồn: {file_name}', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(IMAGE_NAME, dpi=300)
        plt.close() 

        # 4. Tạo báo cáo văn bản chi tiết
        summary_lines = []
        for _, row in ca_map.tail(5).iterrows(): # Lấy top 5 kèo lớn nhất
            summary_lines.append(f"🔹 *{row['Keo_Du_Doan']}*: `${row['Tong_Von_Cuoc_USD']:,.0f}`")
        
        detail_text = "\n".join(summary_lines)
        caption = (
            f"🚨 *PHÁT HIỆN CÁ MẬP MỚI* 🚨\n\n"
            f"📅 Thời gian: `{datetime.now().strftime('%H:%M %d/%m/%Y')}`\n"
            f"📄 File: `{file_name}`\n\n"
            f"*Top biến động lớn nhất:*\n{detail_text}\n\n"
            f"🐋 _Check biểu đồ chi tiết bên dưới Hùng ơi!_"
        )

        send_telegram_photo(TOKEN, CHAT_ID, IMAGE_NAME, caption)

    except Exception as e:
        logging.error(f"💥 Lỗi Pipeline hệ trọng: {e}")

if __name__ == "__main__":
    logging.info("🤖 Bot Day 5 đã sẵn sàng và đang chạy ngầm...")
    
    while True:
        try:
            run_pipeline()
            logging.info(f"😴 Nghỉ ngơi trong {CHECK_INTERVAL_SECONDS/60} phút trước lượt quét tới...")
            time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            logging.info("🛑 Bot đã dừng bởi người dùng.")
            break
        except Exception as e:
            logging.error(f"⚠️ Lỗi vòng lặp chính: {e}")
            time.sleep(60) # Đợi 1 phút rồi thử lại nếu sập