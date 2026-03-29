import requests
import json

class NaoClaude:
    def __init__(self, api_key):
        # Đóng gói API Key của Claude
        self.__api_key = api_key
        # Đây là đường dẫn tổng đài của Anthropic (Claude)
        self.url = "https://api.anthropic.com/v1/messages"

    def phan_tich_so_du(self, so_du_eth, so_du_usd):
        print("🧠 Đang truyền dữ liệu qua Mỹ cho Claude phân tích...")
        
        # 1. Khai báo thẻ vào cổng (Headers)
        headers = {
            "x-api-key": self.__api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # 2. Tạo câu lệnh (Prompt) nhồi số liệu thật vào
        cau_hoi = f"Tài khoản cá mập Binance hiện đang nắm giữ {so_du_eth:,.2f} ETH (tương đương {so_du_usd:,.0f} USD). Hãy đóng vai một chuyên gia phân tích thị trường Crypto rành sỏi, cho tôi một lời cảnh báo cực gắt (dưới 50 chữ) về việc gì sẽ xảy ra với thị trường nếu cái ví này xả hàng bán tháo?"

        # 3. Gói tin gửi đi
        payload = {
            "model": "claude-3-haiku-20240307", # Dùng model Haiku cho tốc độ nhanh nhất
            "max_tokens": 300,
            "messages": [
                {"role": "user", "content": cau_hoi}
            ]
        }

        try:
            # Giao cho bưu tá requests mang đi (Dùng POST vì mình gửi câu hỏi đi)
            phan_hoi = requests.post(self.url, headers=headers, json=payload)
            du_lieu_json = phan_hoi.json()
            
            # Bóc tách file JSON để lấy phần câu trả lời của Claude
            cau_tra_loi = du_lieu_json['content'][0]['text']
            
            print("\n" + "="*50)
            print("🤖 [CHUYÊN GIA CLAUDE NHẬN ĐỊNH]:")
            print(cau_tra_loi)
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"❌ Lỗi kết nối AI: {e}")
            # In ra lỗi chi tiết từ máy chủ nếu bị chặn
            if 'phan_hoi' in locals():
                print(phan_hoi.text)

# ==========================================
# CHẠY THỬ HỆ THỐNG NÃO AI
# ==========================================
if __name__ == "__main__":
    # Dán API Key của Claude vào đây
    KEY_CLAUDE = ""
    
    # Khởi tạo cỗ máy AI
    chuyen_gia = NaoClaude(KEY_CLAUDE)
    
    # Giả lập dữ liệu ông quét được đêm qua
    eth_quet_duoc = 95430.76
    usd_quet_duoc = 334007677
    
    # Bấm nút phân tích
    chuyen_gia.phan_tich_so_du(eth_quet_duoc, usd_quet_duoc)