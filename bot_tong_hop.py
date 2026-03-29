import os
import telebot
import requests
import re
import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
from google import genai
from dotenv import load_dotenv
import schedule
import threading
import time
from flask import Flask

# ==========================================
# 0. KHỞI TẠO BIẾN MÔI TRƯỜNG & BOT
# ==========================================
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ETHERSCAN_KEY = os.environ.get("ETHERSCAN_KEY")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

# ID Admin để Bot tự động gửi báo cáo buổi sáng
ADMIN_CHAT_ID = "5881345386" 

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ==========================================
# KHỐI NÃO 1: ON-CHAIN (SOI VÍ BẰNG ETHERSCAN + GEMINI)
# ==========================================
class Web3AIBot:
    def __init__(self):
        self.etherscan_key = ETHERSCAN_KEY
        self.client = genai.Client(api_key=GEMINI_KEY) 

    def is_valid_eth_address(self, address):
        pattern = r'^0x[a-fA-F0-9]{40}$'
        return bool(re.match(pattern, address))

    def get_eth_balance(self, wallet_address):
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=balance&address={wallet_address}&tag=latest&apikey={self.etherscan_key}"
        try:
            return float(requests.get(url, timeout=10).json()["result"]) / (10**18)
        except: return 0

    def get_erc20_transfers(self, wallet_address, limit=3):
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=tokentx&address={wallet_address}&page=1&offset={limit}&sort=desc&apikey={self.etherscan_key}"
        try:
            data = requests.get(url, timeout=10).json()
            return [{"token_name": tx['tokenSymbol'], "amount": float(tx['value']) / (10 ** int(tx['tokenDecimal']))} for tx in data.get("result", [])]
        except: return []

    def analyze_wallet(self, wallet_address):
        balance = self.get_eth_balance(wallet_address)
        erc20_txs = self.get_erc20_transfers(wallet_address, limit=5)
        
        prompt = (
            f"Ví: {wallet_address}\nSố dư ETH: {balance}\nGiao dịch Token gần nhất: {erc20_txs}\n"
            "Đóng vai chuyên gia Web3. Phân tích ví này ngắn gọn (Cá mập hay người thường, có đang gom Token nào không). Dùng văn bản thuần, gạch đầu dòng và Emoji."
        )
        try:
            return self.client.models.generate_content(model='gemini-2.5-flash', contents=prompt).text
        except Exception as e: return f"Lỗi Gemini: {e}"

my_onchain_bot = Web3AIBot()

# ==========================================
# KHỐI NÃO 2: OFF-CHAIN (ĐỊNH LƯỢNG TOÁN HỌC TỪ BINANCE)
# ==========================================
def lay_du_lieu_binance(symbol='BTC/USDT', timeframe='1d', limit=50):
    try:
        bars = ccxt.bybit().fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['thoi_gian', 'gia_mo', 'gia_cao', 'gia_thap', 'gia_dong', 'khoi_luong'])
        return df['gia_dong']
    except Exception as e:
        print(f"Chi tiết lỗi CCXT Bybit: {e}")
        return None

def tinh_xac_suat_tang(danh_sach_gia, so_ngay_du_bao=30):
    returns = np.log(danh_sach_gia / danh_sach_gia.shift(1)).dropna()
    z_score = (0 - (returns.mean() * so_ngay_du_bao)) / (returns.std() * np.sqrt(so_ngay_du_bao))
    return (1 - norm.cdf(z_score)) * 100

def tinh_rsi(danh_sach_gia, chu_ky=14):
    delta = danh_sach_gia.diff()
    gain = delta.where(delta > 0, 0).ewm(com=chu_ky-1, min_periods=chu_ky).mean()
    loss = -delta.where(delta < 0, 0).ewm(com=chu_ky-1, min_periods=chu_ky).mean()
    return 100 - (100 / (1 + (gain / loss))).iloc[-1]

def tinh_macd(danh_sach_gia):
    macd_line = danh_sach_gia.ewm(span=12, adjust=False).mean() - danh_sach_gia.ewm(span=26, adjust=False).mean()
    return macd_line.iloc[-1] - macd_line.ewm(span=9, adjust=False).mean().iloc[-1]

def tinh_bollinger_bands(danh_sach_gia, window=20, num_std=2):
    rolling_mean = danh_sach_gia.rolling(window=window).mean()
    rolling_std = danh_sach_gia.rolling(window=window).std()
    return (rolling_mean + (rolling_std * num_std)).iloc[-1], (rolling_mean - (rolling_std * num_std)).iloc[-1]

# ==========================================
# KHỐI NÃO 3: ĐIỀU HƯỚNG GIAO TIẾP TELEGRAM
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    loi_chao = (
        "🤖 **TRỢ LÝ WEB3 TỔNG HỢP (V2.0 MAX)**\n\n"
        "1️⃣ **Soi On-chain (Cá mập):** Gửi thẳng địa chỉ ví `0x...` vào đây.\n"
        "2️⃣ **Soi Off-chain (Biểu đồ Quant):** Gõ lệnh `/soichart [Tên Coin]`. Ví dụ: `/soichart ETH`"
    )
    bot.reply_to(message, loi_chao, parse_mode="Markdown")

@bot.message_handler(commands=['soichart'])
def phan_tich_chart(message):
    text_split = message.text.split()
    if len(text_split) < 2:
        bot.reply_to(message, "⚠️ Sếp gõ thiếu tên coin rồi. Ví dụ: `/soichart BTC`", parse_mode="Markdown")
        return
    
    coin_symbol = text_split[1].upper() + "/USDT"
    waiting_msg = bot.reply_to(message, f"⏳ Đang lấy dữ liệu lượng tử & Gọi Gemini AI phân tích {coin_symbol}...")
    
    gia_realtime = lay_du_lieu_binance(symbol=coin_symbol, limit=50)
    if gia_realtime is None or len(gia_realtime) == 0:
        bot.edit_message_text(chat_id=message.chat.id, message_id=waiting_msg.message_id, text="❌ Lỗi dữ liệu sàn Binance.")
        return
        
    gia_cuoi = gia_realtime.iloc[-1]
    xac_suat = tinh_xac_suat_tang(gia_realtime)
    rsi = tinh_rsi(gia_realtime)
    macd_hist = tinh_macd(gia_realtime)
    bb_upper, bb_lower = tinh_bollinger_bands(gia_realtime)
    
    prompt_chuyen_gia = f"""
    Đóng vai chuyên gia phân tích định lượng (Quant Trader).
    Phân tích ngắn gọn tình hình {coin_symbol} dựa trên các số liệu thực tế:
    - Giá: {gia_cuoi} USDT
    - Xác suất tăng 30 ngày: {xac_suat:.2f}%
    - RSI (14): {rsi:.2f}
    - Động lượng MACD: {'VÀO' if macd_hist > 0 else 'RÚT RA'}
    - Khung BB: Đáy {bb_lower:.0f} - Đỉnh {bb_upper:.0f}

    Yêu cầu: Nhận định xu hướng, đưa ra chiến lược (Múc/DCA/Đứng ngoài/Short). Dùng văn phong dứt khoát, chuyên nghiệp, có Emoji.
    """
    
    try:
        ai_nhan_dinh = my_onchain_bot.client.models.generate_content(model='gemini-2.5-flash', contents=prompt_chuyen_gia).text
    except Exception:
        ai_nhan_dinh = "⚠️ Lỗi kết nối API của AI."

    bao_cao = (
        f"📊 **BÁO CÁO QUANT & AI: {coin_symbol}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Giá:** {gia_cuoi:,.2f} USDT\n"
        f"📈 **XS Tăng:** {xac_suat:.2f}% | 📊 **RSI:** {rsi:.2f}\n"
        f"🌪️ **MACD:** {'Dương 🟢' if macd_hist > 0 else 'Âm 🔴'}\n"
        f"📐 **Khung BB:** {bb_lower:,.0f} - {bb_upper:,.0f}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤖 **GEMINI CHỈ ĐẠO CHIẾN LƯỢC:**\n{ai_nhan_dinh}"
    )
    bot.edit_message_text(chat_id=message.chat.id, message_id=waiting_msg.message_id, text=bao_cao, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_wallet(message):
    text_nhan_duoc = message.text.strip()
    if my_onchain_bot.is_valid_eth_address(text_nhan_duoc):
        waiting_msg = bot.reply_to(message, "⏳ Đang soi ví trên mạng Ethereum & hỏi AI...")
        ket_qua = my_onchain_bot.analyze_wallet(text_nhan_duoc)
        bot.edit_message_text(chat_id=message.chat.id, message_id=waiting_msg.message_id, text=f"🕵️‍♂️ **BÁO CÁO ON-CHAIN:**\n\n{ket_qua}")
    else:
        bot.reply_to(message, "❌ Sếp nhập sai định dạng. Hãy nhập 1 ví `0x...` để soi On-chain, hoặc dùng lệnh `/soichart BTC` để soi kỹ thuật!")

# ==========================================
# KHỐI NÃO 4: CHUYÊN GIA BÁO THỨC (CRON JOB)
# ==========================================
def bao_cao_buoi_sang():
    coin_symbol = "BTC/USDT"
    gia_realtime = lay_du_lieu_binance(symbol=coin_symbol, limit=50)
    if gia_realtime is None: return
    
    gia_cuoi = gia_realtime.iloc[-1]
    xac_suat = tinh_xac_suat_tang(gia_realtime)
    rsi = tinh_rsi(gia_realtime)
    macd_hist = tinh_macd(gia_realtime)
    bb_upper, bb_lower = tinh_bollinger_bands(gia_realtime)
    
    prompt = f"Phân tích nhanh {coin_symbol} sáng nay: Giá {gia_cuoi}, XS Tăng {xac_suat:.1f}%, RSI {rsi:.1f}, MACD {'Dương' if macd_hist>0 else 'Âm'}. Đưa ra 1 câu chốt chiến lược. Xưng hô là 'Sếp Hùng'."
    try:
        ai_nhan_dinh = my_onchain_bot.client.models.generate_content(model='gemini-2.5-flash', contents=prompt).text
    except:
        ai_nhan_dinh = "Lỗi AI."

    bao_cao = (
        f"🌅 **CHÀO BUỔI SÁNG SẾP HÙNG!**\n"
        f"Đã đến giờ cà phê và điểm tin thị trường ☕\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 **{coin_symbol}:** {gia_cuoi:,.2f} USDT\n"
        f"📈 **XS Tăng:** {xac_suat:.2f}% | 📊 **RSI:** {rsi:.2f}\n"
        f"🤖 **GEMINI:** {ai_nhan_dinh}"
    )
    bot.send_message(ADMIN_CHAT_ID, bao_cao, parse_mode="Markdown")

def chay_lich_trinh():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Hẹn giờ gửi báo cáo vào 07:00 sáng mỗi ngày
schedule.every().day.at("07:00").do(bao_cao_buoi_sang)

# ==========================================
# KHỐI NÃO 5: WEB SERVER GIẢ (ĐÁNH LỪA RENDER)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Siêu Trợ Lý Tổng Hợp V2 đang hoạt động bình thường trên Render Cloud!"

def chay_web_server():
    # Chạy Flask ở port 8080 (hoặc port do Render tự cấp)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# KHU VỰC CHẠY CHÍNH (ĐA LUỒNG - MULTITHREADING)
# ==========================================
print("🚀 SIÊU TRỢ LÝ TỔNG HỢP V2 ĐÃ SẴN SÀNG TRÊN CLOUD!")
if __name__ == "__main__":
    # 1. Bật luồng canh giờ báo thức
    luong_canh_gio = threading.Thread(target=chay_lich_trinh)
    luong_canh_gio.daemon = True
    luong_canh_gio.start()
    
    # 2. Bật luồng Web Server để giữ mạng Render
    luong_web = threading.Thread(target=chay_web_server)
    luong_web.daemon = True
    luong_web.start()
    
    # 3. Bật luồng Telegram lắng nghe vô tận
    bot.infinity_polling()