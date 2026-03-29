import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. THÂN THỂ: MÁY QUÉT ETHERSCAN
# ==========================================
class MayQuetCaMap:
    def __init__(self, api_key):
        self.__api_key = api_key
        self.url = "https://api.etherscan.io/v2/api"

    def lay_so_du(self, dia_chi_vi):
        tham_so = {
            "chainid": "1", "module": "account", "action": "balance",
            "address": dia_chi_vi, "tag": "latest", "apikey": self.__api_key
        }
        try:
            phan_hoi = requests.get(self.url, params=tham_so).json()
            if phan_hoi["status"] == "1":
                return int(phan_hoi["result"]) / (10**18)
        except:
            pass
        return None

# ==========================================
# 2. BỘ NÃO: AI GEMINI (Tập trung vào Biến động)
# ==========================================
class NaoGemini:
    def __init__(self, api_key):
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"

    def phan_tich_bien_dong(self, ten_vi, chenh_lech, tong_so_du):
        hanh_dong = "VỪA GOM THÊM" if chenh_lech > 0 else "VỪA XẢ BÁN"
        cau_hoi = f"Ví cá mập ({ten_vi}) {hanh_dong} {abs(chenh_lech):,.2f} ETH. Tổng tài sản hiện tại là {tong_so_du:,.2f} ETH. Đóng vai một dân trade chuyên nghiệp, cho 1 câu nhận định cực gắt và giang hồ (dưới 50 chữ) về động thái này."
        
        payload = {"contents": [{"parts": [{"text": cau_hoi}]}]}
        try:
            phan_hoi = requests.post(self.url, headers={"Content-Type": "application/json"}, json=payload).json()
            if 'error' not in phan_hoi:
                return phan_hoi['candidates'][0]['content']['parts'][0]['text'].strip()
        except:
            pass
        return "AI đang bận, tóm lại là thị trường sắp có biến!"

# ==========================================
# 3. CÁI MIỆNG: PHÁT THANH VIÊN TELEGRAM
# ==========================================
class LoaTelegram:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def gui_tin_nhan(self, noi_dung):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": noi_dung, "parse_mode": "Markdown"}
        requests.post(url, json=payload)

# ==========================================
# TRUNG TÂM ĐIỀU KHIỂN: VÒNG LẶP THỜI GIAN
# ==========================================
if __name__ == "__main__":
    print("🚀 SIÊU HỆ THỐNG ĐÃ BẬT. ĐANG GIĂNG LƯỚI BẮT CÁ MẬP...\n")
    
    # Khởi tạo vũ khí từ két sắt .env
    radar = MayQuetCaMap(os.getenv("ETHERSCAN_KEY"))
    ai = NaoGemini(os.getenv("GEMINI_KEY"))
    loa = LoaTelegram(os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"))
    
    # Danh sách đen
    danh_sach_den = {
        "Binance Cold Wallet": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "Vitalik Buterin": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    }
    
    # Cuốn sổ ghi nhớ số dư
    so_du_cu = {}

    while True:
        print(f"[{time.strftime('%H:%M:%S')}] Đang quét radar...")
        
        for ten_ca_map, dia_chi_vi in danh_sach_den.items():
            eth_hien_tai = radar.lay_so_du(dia_chi_vi)
            
            if eth_hien_tai is not None:
                # Nếu là lần quét đầu tiên, chỉ ghi vào sổ, chưa hú còi
                if dia_chi_vi not in so_du_cu:
                    so_du_cu[dia_chi_vi] = eth_hien_tai
                    print(f"  -> Đã chốt sổ mốc ban đầu cho {ten_ca_map}: {eth_hien_tai:,.2f} ETH")
                    continue

                # Từ lần thứ 2 trở đi, tính toán biến động
                chenh_lech = eth_hien_tai - so_du_cu[dia_chi_vi]
                
                if chenh_lech != 0:
                    bieu_tuong = "🟢 GOM HÀNG" if chenh_lech > 0 else "🔴 XẢ HÀNG"
                    loi_phan_tich = ai.phan_tich_bien_dong(ten_ca_map, chenh_lech, eth_hien_tai)
                    
                    # Soạn tin nhắn chuẩn Markdown gửi về điện thoại
                    tin_nhan = f"🚨 *BÁO ĐỘNG {bieu_tuong}*\n\n" \
                               f"🦈 *Mục tiêu:* {ten_ca_map}\n" \
                               f"📊 *Biến động:* {chenh_lech:,.2f} ETH\n" \
                               f"💰 *Tổng tài sản:* {eth_hien_tai:,.2f} ETH\n\n" \
                               f"🤖 *Nhận định AI:*\n_{loi_phan_tich}_"
                    
                    loa.gui_tin_nhan(tin_nhan)
                    print(f"  -> ⚠️ CÓ BIẾN! Đã gửi tin nhắn Telegram cho {ten_ca_map}!")
                    
                    # Cập nhật lại cuốn sổ ghi nhớ
                    so_du_cu[dia_chi_vi] = eth_hien_tai
                else:
                    print(f"  -> {ten_ca_map} đang nằm im.")

        print("Đã quét xong vòng này. Chờ 1 tiếng nữa...\n")
        # Đi ngủ 3600 giây (1 tiếng)
        time.sleep(3600)