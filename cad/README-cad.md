# Bản vẽ CAD – Điều khiển nhà máy thủy điện nội bộ

Các file DXF **R2007 ($ACADVER = AC1021)** – định dạng bản địa của **AutoCAD 2007**,
mở trực tiếp bằng lệnh `OPEN`, không cần chuyển đổi.

| File | Nội dung |
|------|----------|
| `TD-01_so_do_mach_dieu_khien_PLC_R2007.dxf` | Sơ đồ mạch điều khiển PLC S7-1511F: nguồn 24VDC, tín hiệu vào DI/F-DI/AI, rack PLC, tín hiệu ra DQ/AQ, tải (chuông – đèn báo, van baffle, bơm dầu, phanh, biến tần), mạch HOA, E-Stop 2 kênh |
| `TD-02_so_do_mot_duong_dien_R2007.dxf` | Sơ đồ một đường điện (SLD): tua bin – máy phát 100kVA, Q0/Q1, tụ cái 400V, các nhánh tải (MBA T1 22kV, tải nội bộ, UPS, bộ tụ bù), bảng thông số |
| `TD-01_preview.png`, `TD-02_preview.png` | Ảnh xem nhanh (không dùng cho CAD) |
| `generate_cad.py` | Script Python (ezdxf) sinh lại 2 bản vẽ – chỉnh sửa và chạy lại bất cứ lúc nào |

## Thông số bản vẽ
- Giấy: **A3 ngang** (420×297), đơn vị **mm**, khung tên chuẩn góc phải-dưới.
- Vẽ trong **Model Space**, đặt sẵn `EXTMIN/EXTMAX` – mở lên là thấy toàn bộ bản vẽ.
- Text: font **Arial** (style `VN` / `VNB` đậm) – hỗ trợ tiếng Việt Unicode.

## Lớp (Layer)
| Layer | Màu | Dùng cho |
|-------|-----|----------|
| KHUNG | trắng | Khung bản vẽ, khung tên, bảng |
| DAY_CHINH | trắng | Dây điện |
| PLC | vàng (2) | Thẻ PLC, địa chỉ I/O |
| THIET_BI | xanh lá (3) | Thiết bị, tải |
| AN_TOAN | đỏ (1) | Mạch E-Stop (F-DI) |
| ANALOG | xanh lam (4) | Tín hiệu analog 4–20mA / 0–10V |
| TUCAP | tím (6) | Tụ điện / bus điện (SLD) |
| GHI_CHU | trắng mảnh | Chú thích |

## Chỉnh sửa & sinh lại
```bash
python3 -m pip install ezdxf matplotlib
python3 generate_cad.py
```
Địa chỉ I/O trong bản vẽ khớp với phần cứng mô tả trong README chính
(Baffle, Oil Pump VFD, Rotor Speed, Interlock, Brake + 7 condition báo động)
và chương trình mẫu `SimLogic_V18.ap18` (TIA Portal V18).
