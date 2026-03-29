import os
import telebot
import requests
import re
from google import genai
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# Load các biến môi trường từ file .env
load_dotenv()

# Lấy các mã Key (Đã khớp với tên biến trong file .env của em)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ETHERSCAN_KEY = os.environ.get("ETHERSCAN_KEY")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

# Khởi tạo con Bot Telegram
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ==========================================
# LỚP XỬ LÝ API VÀ AI (Bê từ Web sang)
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
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1":
                return float(data["result"]) / (10**18)
            return "Lỗi lấy số dư"
        except:
            return "Lỗi mạng"

    def get_recent_transactions(self, wallet_address, limit=5):
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={self.etherscan_key}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1":
                return [{"to": tx['to'][:6]+"...", "value_eth": float(tx['value'])/(10**18)} for tx in data["result"]]
            return [] 
        except:
            return []

    def get_erc20_transfers(self, wallet_address, limit=5):
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=tokentx&address={wallet_address}&page=1&offset={limit}&sort=desc&apikey={self.etherscan_key}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1":
                tokens = []
                for tx in data["result"]:
                    tokens.append({
                        "token_name": tx['tokenSymbol'],
                        "amount": float(tx['value']) / (10 ** int(tx['tokenDecimal']))
                    })
                return tokens
            return []
        except:
            return []

    def analyze_wallet(self, wallet_address):
        balance = self.get_eth_balance(wallet_address)
        eth_txs = self.get_recent_transactions(wallet_address, limit=5)
        erc20_txs = self.get_erc20_transfers(wallet_address, limit=5)
        
        # Sửa lại Prompt: Yêu cầu trả lời bằng văn bản thuần (Text) thay vì HTML
        prompt = (
            f"Ví: {wallet_address}\n"
            f"Số dư ETH: {balance} ETH\n"
            f"5 Giao dịch ETH gần nhất: {eth_txs}\n"
            f"5 Giao dịch Token ERC-20 (Altcoin) gần nhất: {erc20_txs}\n\n"
            "Đóng vai chuyên gia Web3. Phân tích ví này ngắn gọn. Chú ý đánh giá xem ví này có đang chơi các đồng Token (ERC-20) hay không. Trình bày bằng văn bản thường, dùng gạch đầu dòng và Emoji cho sinh động Tuyệt đối KHÔNG DÙNG ký tự in đậm như dấu sao ()."
        )
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Lỗi từ Gemini: {e}"

# Khởi tạo bộ não AI
my_ai_bot = Web3AIBot()

print("🤖 Bot Telegram đã được lắp não AI. Đang lắng nghe tin nhắn từ sếp Hùng...")

# Lệnh /start
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Chào sếp Hùng! Em là Trợ lý AI Web3.\n\nSếp hãy copy và dán một địa chỉ ví Ethereum (bắt đầu bằng 0x) vào đây để em soi tài sản cho nhé! 🕵️‍♂️")

# Lắng nghe mọi tin nhắn văn bản
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text_nhan_duoc = message.text.strip()
    
    # Kiểm tra xem tin nhắn có phải địa chỉ ví hợp lệ không
    if my_ai_bot.is_valid_eth_address(text_nhan_duoc):
        # 1. Báo đang xử lý (Giữ ID tin nhắn để lát sửa)
        waiting_msg = bot.reply_to(message, "⏳ Đang bay bay Blockchain và hỏi ý kiến Gemini... Sếp đợi em 5-10 giây nhé!")
        
        # 2. Gọi hàm phân tích (Tốn thời gian)
        ket_qua = my_ai_bot.analyze_wallet(text_nhan_duoc)
        
        # 3. Chỉnh sửa tin nhắn "Đang xử lý" thành Kết quả cuối cùng
       # 3. Tạo một cái Bàn phím ảo (Nút bấm)
        ban_phim = InlineKeyboardMarkup()
        
        # Tạo 1 nút bấm chứa đường link đến Etherscan của chính cái ví đó
        link_etherscan = f"https://etherscan.io/address/{text_nhan_duoc}"
        nut_xem_web = InlineKeyboardButton(text="🔍 Xem chi tiết trên Etherscan", url=link_etherscan)
        
        # Gắn nút vào bàn phím
        ban_phim.add(nut_xem_web)

        # 4. Ghi đè tin nhắn + Kèm theo cái bàn phím vừa tạo
        bot.edit_message_text(
            chat_id=message.chat.id, 
            message_id=waiting_msg.message_id, 
            text=ket_qua, 
            reply_markup=ban_phim  # <-- Vũ khí bí mật nằm ở đây!
        )
    else:
        # Nếu nhập linh tinh (không phải ví 0x...)
        bot.reply_to(message, "❌ Sếp ơi, đây không phải là địa chỉ ví Ethereum hợp lệ. Địa chỉ chuẩn phải bắt đầu bằng '0x' và có 42 ký tự nhé!")

# Vòng lặp vô hạn giúp Bot luôn chạy
if __name__ == "__main__":
    bot.infinity_polling()