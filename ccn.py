from abc import ABC, abstractmethod
import random

# ==========================================
# KHỐI 1: HỆ THỐNG CỔ TRÙNG (ABSTRACTION & INHERITANCE)
# ==========================================
# Lớp cha trừu tượng cho mọi loại Cổ. Không thể tạo trực tiếp đối tượng từ lớp này.
class CoTrung(ABC):
    def __init__(self, ten, chuyen, tieu_hao, mo_ta):
        self.ten = ten
        self.chuyen = chuyen # Cấp bậc Cổ: 1 Chuyển đến 9 Chuyển
        self.__tieu_hao = tieu_hao # Chân nguyên tiêu hao (Private - Đóng gói)
        self.mo_ta = mo_ta

    # Getter an toàn để lấy giá trị tiêu hao
    def get_tieu_hao(self):
        return self.__tieu_hao

    # Hàm trừu tượng: Bắt buộc các loại Cổ con phải tự định nghĩa tác dụng riêng
    @abstractmethod
    def kich_hoat(self):
        pass

    def hien_thi(self):
        print(f"🐛 [{self.ten}] - {self.chuyen} Chuyển | Tiêu hao: {self.__tieu_hao} | Tác dụng: {self.mo_ta}")

# --- Các lớp con kế thừa từ CoTrung ---

# 1. Cổ Bản Mạng (Vital Gu): Loại Cổ quan trọng nhất, gắn liền với sinh mệnh
class CoBanMang(CoTrung):
    def __init__(self, ten, chuyen, tieu_hao, mo_ta, dac_tinh_rieng):
        super().__init__(ten, chuyen, tieu_hao, mo_ta)
        self.dac_tinh_rieng = dac_tinh_rieng # Ví dụ: Tăng tốc độ hồi tu vi

    def kich_hoat(self):
        return f"✨ Kích hoạt Bản Mạng Cổ {self.ten}: {self.dac_tinh_rieng}"

# 2. Cổ Tấn Công (Offensive Gu)
class CoTanCong(CoTrung):
    def __init__(self, ten, chuyen, tieu_hao, mo_ta, sat_thuong):
        super().__init__(ten, chuyen, tieu_hao, mo_ta)
        self.sat_thuong = sat_thuong

    def kich_hoat(self):
        # Đa hình: Trả về lượng sát thương ngẫu nhiên dựa trên chỉ số gốc
        actual_dmg = random.randint(self.sat_thuong - 10, self.sat_thuong + 10)
        return f"⚔️ Sử dụng {self.ten} tấn công: Gây ra {actual_dmg} sát thương hệ {self.mo_ta}!"

class CoPhongThu(CoTrung):
    def __init__(self, ten, chuyen, tieu_hao, mo_ta, chi_so_phong_thu):
        super().__init__(ten, chuyen, tieu_hao, mo_ta)
        self.chi_so_phong_thu = chi_so_phong_thu

    def kich_hoat(self):
        return f"🛡️ Sử dụng {self.ten} phòng thủ: Tạo ra lớp khiên cản {self.chi_so_phong_thu} sát thương!"

# ==========================================
# KHỐI 2: HỆ THỐNG CỔ SƯ (MANAGEMENT OBJECT)
# ==========================================
class CoSu:
    # Bản đồ tư chất Không Khiếu (Aptitude)
    __TU_CHAT_MAP = {
        'A': 0.9, # 90% Chân nguyên
        'B': 0.7, # 70% 
        'C': 0.5, # 50%
        'D': 0.3  # 30%
    }

    def __init__(self, ten, tu_chat, canh_gioi):
        self.ten = ten
        self.tu_chat = tu_chat.upper()
        self.canh_gioi = canh_gioi # 1 Chuyển đến 9 Chuyển
        self.__chan_nguyen_toi_da = canh_gioi * 1000 * self.__TU_CHAT_MAP.get(self.tu_chat, 0.3)
        self.__chan_nguyen_hien_tai = self.__chan_nguyen_toi_da # Đóng gói chân nguyên
        
        # Quản lý danh sách Cổ: Sử dụng Dictionary để tra cứu nhanh bằng tên
        self.phuc_dia_co = {} 
        self.co_ban_mang = None

    def add_co(self, co_obj):
        # Kiểm tra nếu là Cổ Bản Mạng
        if isinstance(co_obj, CoBanMang):
            if self.co_ban_mang:
                print("❌ Cổ Sư chỉ có thể có 1 Cổ Bản Mạng!")
                return
            self.co_ban_mang = co_obj
            print(f"✅ Đã luyện hóa thành công Cổ Bản Mạng: {co_obj.ten}")
        else:
            self.phuc_dia_co[co_obj.ten] = co_obj
            print(f"✅ Đã luyện hóa thành công Cổ: {co_obj.ten}")

    def su_dung_co(self, ten_co):
        print(f"\n⚡ {self.ten} bắt đầu sử dụng Cổ...")
        
        # 1. Tìm Cổ trong Phúc Địa
        target_co = self.phuc_dia_co.get(ten_co)
        if not target_co and self.co_ban_mang and self.co_ban_mang.ten == ten_co:
            target_co = self.co_ban_mang
            
        if not target_co:
            print(f"❌ Không tìm thấy Cổ [{ten_co}] trong Phúc Địa!")
            return

        # 2. Kiểm tra Chân nguyên
        cost = target_co.get_tieu_hao()
        if self.__chan_nguyen_hien_tai < cost:
            print(f"❌ Không đủ Chân nguyên! Hiện có: {self.__chan_nguyen_hien_tai:.0f}, Cần: {cost}")
            return

        # 3. Trừ chân nguyên và kích hoạt hiệu ứng (Đa hình)
        self.__chan_nguyen_hien_tai -= cost
        print(target_co.kich_hoat())
        print(f"💧 Chân nguyên còn lại: {self.__chan_nguyen_hien_tai:.0f}")

    def hien_thi_thong_tin(self):
        print(f"\n--- THÔNG TIN CỔ SƯ ---")
        print(f"👤 Tên: {self.ten} | Tư chất: {self.tu_chat}-Hạng | Canh giới: {self.canh_gioi}-Chuyển")
        print(f"💧 Chân nguyên: {self.__chan_nguyen_hien_tai:.0f}/{self.__chan_nguyen_toi_da:.0f}")
        print(f"📜 Danh sách Cổ đang luyện hóa:")
        if self.co_ban_mang:
            print(f" ⭐ Bản Mạng: {self.co_ban_mang.ten}")
        for co in self.phuc_dia_co.values():
            print(f" - {co.ten} ({co.__class__.__name__})")


# ==========================================
# KỊCH BẢN CHẠY THỬ
# ==========================================
if __name__ == "__main__":
    # 1. Tạo Cổ Sư (Cổ Nguyệt Phương Nguyên, tư chất C - phế vật lúc đầu)
    phuong_nguyen = CoSu("Cổ Nguyệt Phương Nguyên", "C", 1)
    
    # 2. Tạo Cổ Trùng
    xuan_thu_thien = CoBanMang("Xuân Thu Thiền", 6, 800, "Trùng sinh về quá khứ", "Nén sinh mệnh và tu vi")
    nguyet_quang_co = CoTanCong("Nguyệt Quang Cổ", 1, 100, "Nguyệt nhận", 50)
    thach_bi_co = CoPhongThu("Thạch Bì Cổ", 1, 150, "Cơ thể hóa đá", "Tăng thủ")

    # 3. Luyện hóa Cổ
    phuong_nguyen.add_co(xuan_thu_thien)
    phuong_nguyen.add_co(nguyet_quang_co)
    phuong_nguyen.add_co(thach_bi_co)

    phuong_nguyen.hien_thi_thong_tin()

    # 4. Sử dụng Cổ
    phuong_nguyen.su_dung_co("Nguyệt Quang Cổ") # Chạy mượt
    phuong_nguyen.su_dung_co("Xuân Thu Thiền") # Hết chân nguyên, báo lỗi