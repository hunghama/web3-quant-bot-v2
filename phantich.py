import pandas as pd

# 1. Đọc file CSV mà ông đã lưu từ mấy hôm trước
# (Thay tên file bằng tên file thật của ông nhé)
ten_file = 'bao_cao_polymarket.csv' 
df = pd.read_csv(ten_file)

# 2. Lọc ra những kèo cá mập > 10 triệu đô
ca_map = df[df['Tong_Von_Cuoc_USD'] > 10000000]

# 3. Sắp xếp từ cao xuống thấp cho dễ nhìn
ca_map_sap_xep = ca_map.sort_values(by='Tong_Von_Cuoc_USD', ascending=False)

print("--- 🐋 DANH SÁCH CÁ MẬP SIÊU CẤP ---")
print(ca_map_sap_xep)
import matplotlib.pyplot as plt

# Tạo biểu đồ hình cột
plt.figure(figsize=(10, 6))
plt.barh(ca_map_sap_xep['Keo_Du_Doan'], ca_map_sap_xep['Tong_Von_Cuoc_USD'], color='skyblue')

# Thêm tiêu đề và nhãn
plt.title('Top Cá Mập Polymarket - Day 5', fontsize=14)
plt.xlabel('Volume (USD)', fontsize=12)
plt.ylabel('Kèo dự đoán', fontsize=10)

# Hiển thị biểu đồ
plt.tight_layout()
plt.show()