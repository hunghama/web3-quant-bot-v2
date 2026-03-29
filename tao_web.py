import datetime

# 1. Lấy giờ hiện tại bằng Python
gio_hien_tai = datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
ten_sếp = "Phí Công Hùng"

print("Đang đúc gạch xây Web...")

# 2. Dùng Python viết mã HTML (Đây chính là Giao diện Web)
# Chú ý: Cấu trúc HTML bắt đầu bằng <html> và kết thúc bằng </html>
noi_dung_web = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Trạm Radar Cá Mập</title>
    <meta charset="utf-8">
</head>
<body style="background-color: #1a1a1a; color: #00ff00; font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
    
    <h1>🚨 BẢNG ĐIỀU KHIỂN WHALE TRACKER 🚨</h1>
    <h2>Xưởng trưởng: {ten_sếp}</h2>
    
    <div style="border: 2px solid #00ff00; width: 50%; margin: 0 auto; padding: 20px; border-radius: 10px;">
        <h3 style="color: yellow;">Trạng thái hệ thống: ONLINE 🟢</h3>
        <p>Cập nhật lần cuối: <b>{gio_hien_tai}</b></p>
        <p>Tất cả cá mập đang nằm trong tầm ngắm!</p>
    </div>

</body>
</html>
"""

# 3. Ra lệnh cho Python tạo ra một file tên là "dashboard.html" và nhét nội dung vào
with open("dashboard.html", "w", encoding="utf-8") as file_web:
    file_web.write(noi_dung_web)

print("✅ Đã xây xong trang Web! Sếp hãy tìm file 'dashboard.html' và mở lên nhé!")
