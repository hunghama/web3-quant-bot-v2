import os
import requests
import re
import sqlite3 # Thư viện Database (Cơ sở dữ liệu) tích hợp sẵn của Python
from google import genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CẤU HÌNH DATABASE (LƯU TRỮ LỊCH SỬ)
# ==========================================
def init_db():
    # Tạo (hoặc kết nối nếu đã có) file database.db ngay trong thư mục code
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Tạo bảng 'history' gồm 4 cột: id, ví, kết quả phân tích, thời gian
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address TEXT NOT NULL,
            ai_result TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Chạy hàm tạo Database ngay khi khởi động file
init_db()

# ==========================================
# LỚP XỬ LÝ API VÀ AI
# ==========================================
class Web3AIBot:
    def __init__(self):
        self.etherscan_key = os.environ.get("ETHERSCAN_KEY")
        gemini_key = os.environ.get("GEMINI_KEY")
        self.client = genai.Client(api_key=gemini_key) 

    def is_valid_eth_address(self, address):
        pattern = r'^0x[a-fA-F0-9]{40}$'
        return bool(re.match(pattern, address))

    def get_eth_balance(self, wallet_address):
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=balance&address={wallet_address}&tag=latest&apikey={self.etherscan_key}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1":
                return float(data["result"]) / (10**18)
            return "Lỗi lấy số dư"
        except:
            return "Lỗi mạng"

    def get_recent_transactions(self, wallet_address, limit=3):
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={self.etherscan_key}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1":
                return [{"to": tx['to'][:6]+"...", "value_eth": float(tx['value'])/(10**18)} for tx in data["result"]]
            return [] 
        except:
            return []

    # --- HÀM MỚI: LẤY GIAO DỊCH TOKEN ERC-20 (SHIB, PEPE, USDT...) ---
    def get_erc20_transfers(self, wallet_address, limit=3):
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=tokentx&address={wallet_address}&page=1&offset={limit}&sort=desc&apikey={self.etherscan_key}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1":
                tokens = []
                for tx in data["result"]:
                    tokens.append({
                        "token_name": tx['tokenSymbol'],
                        # Phải chia cho tokenDecimal vì mỗi token có số 0 khác nhau
                        "amount": float(tx['value']) / (10 ** int(tx['tokenDecimal']))
                    })
                return tokens
            return []
        except:
            return []

    def analyze_wallet(self, wallet_address):
        if not self.is_valid_eth_address(wallet_address):
            return "LỖI: Địa chỉ ví không hợp lệ!"

        balance = self.get_eth_balance(wallet_address)
        eth_txs = self.get_recent_transactions(wallet_address, limit=3)
        erc20_txs = self.get_erc20_transfers(wallet_address, limit=3) # Gọi hàm mới lấy Token
        
        prompt = (
            f"Ví: {wallet_address}\n"
            f"Số dư ETH: {balance} ETH\n"
            f"3 Giao dịch ETH gần nhất: {eth_txs}\n"
            f"3 Giao dịch Token ERC-20 (Altcoin) gần nhất: {erc20_txs}\n\n"
            "Đóng vai chuyên gia Web3. Phân tích ví này ngắn gọn. Chú ý đánh giá xem ví này có đang chơi các đồng Token (ERC-20) hay không. Dùng HTML cơ bản để trình bày."
        )
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Lỗi từ Gemini: {e}"

# ==========================================
# KHỞI TẠO WEB FLASK
# ==========================================
app = Flask(__name__)
my_bot = Web3AIBot()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        data = request.get_json()
        wallet_input = data.get('wallet_address')
        
        if wallet_input:
            ai_result = my_bot.analyze_wallet(wallet_input)
            
            # --- CHỨC NĂNG MỚI: LƯU KẾT QUẢ VÀO DATABASE ---
            if "LỖI" not in ai_result:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO history (wallet_address, ai_result) VALUES (?, ?)", (wallet_input, ai_result))
                conn.commit()
                conn.close()

            return jsonify({"status": "success", "data": ai_result})
            
        return jsonify({"status": "error", "message": "Vui lòng nhập địa chỉ ví."})

    # NẾU LÀ GET (Khách mở Web) -> Lấy lịch sử từ Database truyền sang HTML
    history_data = []
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        # Lấy 5 kết quả mới nhất (sắp xếp ID giảm dần)
        cursor.execute("SELECT wallet_address, ai_result, created_at FROM history ORDER BY id DESC LIMIT 5")
        history_data = cursor.fetchall()
        conn.close()
    except Exception as e:
        print("Lỗi đọc Database:", e)

    return render_template('index.html', history=history_data)

if __name__ == "__main__":
    app.run(debug=True)