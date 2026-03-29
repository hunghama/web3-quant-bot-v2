import requests
import json

class NaoGemini:
    def __init__(self, api_key):
        self.__api_key = api_key
        # Đường dẫn tổng đài của Gemini (Truyền luôn Key vào URL)
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={self.__api_key}"

    def phan_tich_so_du(self, so_du_eth, so_du_usd):
        print("🧠 Đang truyền dữ liệu cho siêu máy chủ Gemini phân tích...")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Câu lệnh (Prompt) nhồi số dư thực tế vào
        cau_hoi = f"Tài khoản cá mập Binance hiện đang nắm giữ {so_du_eth:,.2f} ETH (tương đương {so_du_usd:,.0f} USD). Hãy đóng vai một chuyên gia phân tích thị trường Crypto rành sỏi, cho tôi một lời cảnh báo cực gắt (dưới 50 chữ) về việc gì sẽ xảy ra với thị trường nếu cái ví này xả hàng bán tháo?"

        # Gói tin gửi đi theo chuẩn cấu trúc của Google
        payload = {
            "contents": [{
                "parts": [{"text": cau_hoi}]
            }]
        }

        try:
            # Giao cho bưu tá requests mang đi
            phan_hoi = requests.post(self.url, headers=headers, json=payload)
            du_lieu_json = phan_hoi.json()
            
            # Bóc tách lớp vỏ JSON để lấy câu trả lời cốt lõi
            cau_tra_loi = du_lieu_json['candidates'][0]['content']['parts'][0]['text']
            
            print("\n" + "="*50)
            print("🤖 [CHUYÊN GIA GEMINI NHẬN ĐỊNH]:")
            print(cau_tra_loi)
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"❌ Lỗi kết nối AI: {e}")
            if 'phan_hoi' in locals():
                print("Chi tiết lỗi:", phan_hoi.text)

# ==========================================
# CHẠY THỬ HỆ THỐNG NÃO AI MIỄN PHÍ
# ==========================================
if __name__ == "__main__":
    # 🚨 Dán API Key Gemini của ông vào đây
    KEY_GEMINI = "AIzaSyBbKmktPtUf5G4cdkeDM2FrIUmrNa1E1Fw"
    
    # Khởi tạo cỗ máy
    chuyen_gia = NaoGemini(KEY_GEMINI)
    
    # Dữ liệu quét được từ đêm qua
    eth_quet_duoc = 95430.76
    usd_quet_duoc = 334007677
    
    # Bấm nút phân tích
    chuyen_gia.phan_tich_so_du(eth_quet_duoc, usd_quet_duoc)