import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
import time
from datetime import datetime

# ==========================================
# BƯỚC 1: HACK VÀO SÀN BINANCE LẤY DỮ LIỆU
# ==========================================
def lay_du_lieu_binance(symbol='BTC/USDT', timeframe='1d', limit=50):
    try:
        san_binance = ccxt.binance()
        bars = san_binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['thoi_gian', 'gia_mo', 'gia_cao', 'gia_thap', 'gia_dong', 'khoi_luong'])
        df['thoi_gian'] = pd.to_datetime(df['thoi_gian'], unit='ms')
        return df['gia_dong'] # Chỉ lấy cột giá đóng cửa cho gọn
    except Exception as e:
        print(f"⚠️ Lỗi kết nối sàn: {e}")
        return None

# ==========================================
# BƯỚC 2: TÍNH XÁC SUẤT BẰNG TOÁN HỌC THỐNG KÊ
# ==========================================
def tinh_xac_suat_tang(danh_sach_gia, so_ngay_du_bao=30):
    returns = np.log(danh_sach_gia / danh_sach_gia.shift(1)).dropna()
    mu_ngay = returns.mean()
    vol_ngay = returns.std()
    
    mu_tong = mu_ngay * so_ngay_du_bao
    vol_tong = vol_ngay * np.sqrt(so_ngay_du_bao)
    
    z_score = (0 - mu_tong) / vol_tong
    prob = 1 - norm.cdf(z_score)
    return prob * 100

# ==========================================
# BƯỚC 3: TÍNH CHỈ BÁO RSI (PHÂN TÍCH KỸ THUẬT)
# ==========================================
def tinh_rsi(danh_sach_gia, chu_ky=14):
    # Tính sự chênh lệch giá giữa các ngày
    delta = danh_sach_gia.diff()
    
    # Tách riêng ngày Tăng (gain) và ngày Giảm (loss)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Tính trung bình trượt mũ (EMA) của chu kỳ 14 ngày
    avg_gain = gain.ewm(com=chu_ky-1, min_periods=chu_ky).mean()
    avg_loss = loss.ewm(com=chu_ky-1, min_periods=chu_ky).mean()
    
    # Công thức RSI chuẩn mực
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))
    
    return rsi_series.iloc[-1] # Chỉ lấy con số RSI của ngày hôm nay

# ==========================================
# BƯỚC 4: LẮP NÃO ĐƯA RA QUYẾT ĐỊNH
# ==========================================
def dua_ra_loi_khuyen(prob, rsi, gia_hien_tai):
    bay_gio = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    print(f"\n======================================")
    print(f"🚀 BOT PHÂN TÍCH BTC | {bay_gio}")
    print(f"======================================")
    print(f"💰 Giá hiện tại: {gia_hien_tai:,.2f} USDT")
    print(f"📈 Xác suất tăng: {prob:.2f}% | 📊 RSI: {rsi:.2f}")
    
    # Logic ra quyết định:
    # Nếu xác suất tăng cao (>55%) VÀ RSI cho thấy giá đang bị bán tháo quá đà (<35) -> MÚC
    if prob > 55 and rsi < 35:
        print("🚨 TÍN HIỆU: MÚC (Vùng mua đẹp!)")
    # Nếu xác suất tăng thấp (<45) VÀ RSI cho thấy giá đang bị bơm ảo (>65) -> CHỐT
    elif prob < 45 and rsi > 65:
        print("⚠️ TÍN HIỆU: CHỐT (Vùng rủi ro!)")
    else:
        print("⚖️ TRẠNG THÁI: Đang quan sát...")

# ==========================================
# KHU VỰC CHẠY CHÍNH (VÒNG LẶP TREO MÁY)
# ==========================================
if __name__ == "__main__":
    phut_nghi = 5 # 5 phút quét 1 lần
    
    print(f"🤖 Bot Quant đã khởi động! Quét sàn mỗi {phut_nghi} phút một lần.")
    print("Nhấn Ctrl + C để dừng Bot.")
    
    while True:
        try:
            # 1. Lấy dữ liệu
            gia_realtime = lay_du_lieu_binance(limit=50)
            
            if gia_realtime is not None:
                gia_cuoi = gia_realtime.iloc[-1]
                
                # 2. Xử lý Logic
                xac_suat = tinh_xac_suat_tang(gia_realtime)
                rsi_hien_tai = tinh_rsi(gia_realtime)
                
                # 3. Đưa ra lệnh
                dua_ra_loi_khuyen(xac_suat, rsi_hien_tai, gia_cuoi)
            
            # 4. Kỹ thuật né Rate Limit học từ Ngày 37
            print(f"\n💤 Đang đợi {phut_nghi} phút cho lần quét tiếp theo...")
            time.sleep(phut_nghi * 60)
            
        except KeyboardInterrupt:
            print("\n🛑 Sếp đã tắt Bot. Hẹn gặp lại!")
            break