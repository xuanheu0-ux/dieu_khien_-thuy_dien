# -*- coding: utf-8 -*-
"""
Sinh bản vẽ DXF R2007 (mở trực tiếp bằng AutoCAD 2007) cho dự án
"Điều khiển nhà máy thủy điện nội bộ" (S7-1511F / TIA Portal V18).

Bản vẽ:
  TD-01: Sơ đồ mạch điều khiển PLC S7-1511F
  TD-02: Sơ đồ một đường điện (Single Line Diagram)

Chạy:  python3 generate_cad.py
Yêu cầu: ezdxf >= 1.1 , matplotlib (chỉ để xuất ảnh xem trước)
"""
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment as TEA

# ----------------------------------------------------------------------
# Hằng số chung
# ----------------------------------------------------------------------
A3_W, A3_H = 420.0, 297.0
DATE_STR = '05/09/2026'
UNIT = 'AI (Arena)'

# Màu theo mã AutoCAD (ACI)
K = dict(
    KHUNG='KHUNG',           # trắng - khung bản vẽ
    DAY='DAY_CHINH',         # trắng - dây điện
    PLC='PLC',               # vàng  - PLC
    TB='THIET_BI',           # xanh lá - thiết bị
    AT='AN_TOAN',            # đỏ    - mạch an toàn
    AN='ANALOG',             # xanh lam - analog
    TC='TUCAP',              # tím   - tụ điện / bus (SLD)
    CHU='GHI_CHU',           # trắng - chữ
)


def new_doc():
    doc = ezdxf.new('R2007', setup=True)  # R2007 = định dạng AutoCAD 2007
    doc.header['$INSUNITS'] = 4           # milimet
    doc.header['$LWDISPLAY'] = 1
    doc.header['$EXTMIN'] = (0, 0, 0)
    doc.header['$EXTMAX'] = (A3_W, A3_H, 0)
    for name, font in (('VN', 'arial.ttf'), ('VNB', 'arialbd.ttf')):
        if name not in doc.styles:
            doc.styles.add(name, font=font)
    layers = [
        ('KHUNG',      7, 50),
        ('DAY_CHINH',  7, 35),
        ('PLC',        2, 25),
        ('THIET_BI',   3, 25),
        ('AN_TOAN',    1, 25),
        ('ANALOG',     4, 25),
        ('TUCAP',      6, 35),
        ('GHI_CHU',    7, 18),
    ]
    for lname, color, lw in layers:
        if lname not in doc.layers:
            doc.layers.add(lname, color=color, lineweight=lw)
    return doc


# ----------------------------------------------------------------------
# Hàm vẽ cơ bản
# ----------------------------------------------------------------------
class Sheet:
    """Một tờ A3 nằm trong model space, gốc trái-dưới tại (ox, oy)."""

    def __init__(self, msp, ox=0.0, oy=0.0):
        self.msp = msp
        self.ox, self.oy = ox, oy

    def _p(self, x, y):
        return (self.ox + x, self.oy + y)

    # ---- primitives ----
    def line(self, x1, y1, x2, y2, layer=K['DAY'], lw=None, color=None):
        att = {'layer': layer}
        if lw:
            att['lineweight'] = lw
        if color is not None:
            att['color'] = color
        self.msp.add_line(self._p(x1, y1), self._p(x2, y2), dxfattribs=att)

    def rect(self, x, y, w, h, layer=K['TB'], lw=None):
        att = {'layer': layer}
        if lw:
            att['lineweight'] = lw
        self.msp.add_lwpolyline(
            [self._p(x, y), self._p(x + w, y), self._p(x + w, y + h), self._p(x, y + h)],
            close=True, dxfattribs=att)

    def circle(self, x, y, r, layer=K['TB']):
        self.msp.add_circle(self._p(x, y), r, dxfattribs={'layer': layer})

    def arc(self, x, y, r, a1, a2, layer=K['TB']):
        self.msp.add_arc(self._p(x, y), r, a1, a2, dxfattribs={'layer': layer})

    def text(self, x, y, s, h=2.2, layer=K['CHU'], align='L', rot=0, bold=False, color=None):
        att = {'layer': layer, 'height': h, 'rotation': rot,
               'style': 'VNB' if bold else 'VN'}
        if color is not None:
            att['color'] = color
        t = self.msp.add_text(s, dxfattribs=att)
        amap = {'L': TEA.MIDDLE_LEFT, 'C': TEA.MIDDLE_CENTER, 'R': TEA.MIDDLE_RIGHT}
        t.set_placement(self._p(x, y), align=amap[align])
        return t

    def dot(self, x, y, r=0.5, layer=K['DAY']):
        """Điểm nối (chấm tròn đặc)."""
        pts = [(x + r * math.cos(a), y + r * math.sin(a))
               for a in [i * 2 * math.pi / 12 for i in range(12)]]
        hatch = self.msp.add_hatch(dxfattribs={'layer': layer})
        hatch.set_pattern_fill('SOLID')
        hatch.paths.add_polyline_path([self._p(px, py) for px, py in pts],
                                      is_closed=True)

    def arrow(self, x, y, angle_deg=270, size=2.6, layer=K['DAY']):
        """Mũi tên đặc, đỉnh tại (x, y), hướng angle (độ)."""
        a = math.radians(angle_deg)
        b1, b2 = a + math.radians(150), a - math.radians(150)
        pts = [(x, y),
               (x + size * math.cos(b1), y + size * math.sin(b1)),
               (x + size * math.cos(b2), y + size * math.sin(b2))]
        hatch = self.msp.add_hatch(dxfattribs={'layer': layer})
        hatch.set_pattern_fill('SOLID')
        hatch.paths.add_polyline_path([self._p(px, py) for px, py in pts],
                                      is_closed=True)

    # ---- symbols ----
    def contact(self, x1, y, layer=K['DAY'], nc=False, w=8.0):
        """Tiếp điểm ngang IEC: đầu trái (x1) -> đầu phải (x1+w)."""
        x2 = x1 + w
        g1, g2 = x1 + w * 0.42, x1 + w * 0.58
        self.dot(x1, y, 0.45, layer)
        self.dot(x2, y, 0.45, layer)
        self.line(x1, y, g1, y, layer)
        self.line(g2, y, x2, y, layer)
        self.line(g1, y, g2, y + 2.6, layer)
        if nc:  # thanh chặn của tiếp điểm thường đóng
            self.line(g2, y + 1.6, g2, y - 1.6, layer)

    def coil(self, x, y, w=10.0, h=5.0, layer=K['TB']):
        """Cuộn dây-rêle (hình chữ nhật), tâm tại (x, y)."""
        self.rect(x - w / 2, y - h / 2, w, h, layer)

    def earth(self, x, y, layer=K['DAY'], w=6.0):
        """Ký hiệu nối đất, đầu nối tại (x, y), hướng xuống."""
        for i, ww in enumerate((w, w * 0.66, w * 0.33)):
            self.line(x - ww / 2, y - i * 1.4, x + ww / 2, y - i * 1.4, layer)

    def flag24(self, x, y, layer=K['DAY']):
        """Cờ nguồn +24V đi xuống."""
        self.text(x, y, '+24V', 2.4, layer, 'C')
        self.line(x, y - 1.6, x, y - 3.6, layer)
        self.arrow(x, y - 4.0, 270, 2.2, layer)


# ----------------------------------------------------------------------
# Khung bản vẽ + khung tên (dùng chung)
# ----------------------------------------------------------------------
def draw_frame(sh, ten_ban_ve, so_bv):
    msp = sh.msp
    sh.rect(0, 0, A3_W, A3_H, K['KHUNG'], lw=50)
    sh.rect(10, 10, A3_W - 20, A3_H - 20, K['KHUNG'], lw=25)

    # ---- khung tên 180 x 42, góc dưới-phải ----
    tx, ty = 230.0, 10.0
    sh.rect(tx, ty, 180, 42, K['KHUNG'], lw=35)
    sh.line(tx + 100, ty, tx + 100, ty + 42, K['KHUNG'])      # chia 2 cột
    for yy in (32, 22):
        sh.line(tx, ty + yy, tx + 100, ty + yy, K['KHUNG'])   # cột trái
    for i in range(1, 6):
        sh.line(tx + 100, ty + i * 7, tx + 180, ty + i * 7, K['KHUNG'])
    sh.line(tx + 140, ty, tx + 140, ty + 42, K['KHUNG'])      # chia cột phải

    L = tx + 2
    sh.text(L, ty + 37, 'ĐƠN VỊ: HỆ THỐNG ĐIỀU KHIỂN NHÀ MÁY THỦY ĐIỆN NỘI BỘ', 2.1, K['CHU'], 'L', bold=True)
    sh.text(L, ty + 27, 'CÔNG TRÌNH: TỦ ĐIỀU KHIỂN PLC S7-1511F', 2.1, K['CHU'], 'L')
    sh.text(L, ty + 17, 'TÊN BẢN VẼ: ' + ten_ban_ve, 2.1, K['CHU'], 'L', bold=True)
    sh.text(L, ty + 6, 'BẢN VẼ SINH BỞI AI – DXF R2007 (AUTOCAD 2007)', 1.9, K['CHU'], 'L', color=8)

    right = [
        ('NGƯỜI VẼ', UNIT, 'NGÀY', DATE_STR),
        ('KIỂM TRA', '..........', 'TỈ LỆ', 'KT'),
        ('DUYỆT', '..........', 'GIẤC', 'A3'),
        ('SỐ BẢN VẼ', so_bv, 'ĐƠN VỊ TÍNH', 'mm'),
        ('MÃ HỒ SƠ', f'TD-{so_bv[-2:]}-2026', 'LẦN BV', '00'),
        ('SỐ KỆ', '....', 'SỐ TRANG', '1/1'),
    ]
    for i, (k1, v1, k2, v2) in enumerate(right):
        yy = ty + 42 - (i + 0.5) * 7
        sh.text(tx + 102, yy, f'{k1}: {v1}', 1.8, K['CHU'], 'L')
        sh.text(tx + 142, yy, f'{k2}: {v2}', 1.8, K['CHU'], 'L')


# ======================================================================
# TỜ 1 – SƠ ĐỒ MẠCH ĐIỀU KHIỂN PLC
# ======================================================================
def sheet1(msp):
    sh = Sheet(msp, 0, 0)
    draw_frame(sh, 'SƠ ĐỒ MẠCH ĐIỀU KHIỂN PLC', 'TD-01')

    sh.text(12, 281, 'SƠ ĐỒ MẠCH ĐIỀU KHIỂN PLC S7-1511F – NHÀ MÁY THỦY ĐIỆN NỘI BỘ',
            5.0, K['CHU'], 'L', bold=True)

    # ---------- đầu mục ----------
    sh.text(13, 268, '1. NGUỒN ĐIỀU KHIỂN', 3.0, K['CHU'], 'L', bold=True)
    sh.text(78, 268, '2. TÍN HIỆU VÀO (DI / F-DI / AI)', 3.0, K['CHU'], 'L', bold=True)
    sh.text(296, 268, '3. TÍN HIỆU RA & TẢI (DQ / AQ)', 3.0, K['CHU'], 'L', bold=True)

    # ================= KHU VỰC 1: NGUỒN (x 13..70) =================
    sh.text(16, 254, 'L1', 2.2, K['CHU'], 'R')
    sh.text(16, 246, 'N', 2.2, K['CHU'], 'R')
    sh.contact(18, 254, K['DAY'])
    sh.text(22, 258.2, 'QF1', 2.0, K['CHU'], 'C', bold=True)
    sh.line(26, 254, 30, 254, K['DAY'])
    sh.line(17, 246, 30, 246, K['DAY'])
    sh.text(23, 250, 'AC 230V', 1.8, K['CHU'], 'C', color=8)

    sh.rect(30, 230, 34, 28, K['TB'])
    sh.text(47, 251.5, 'BỘ NGUỒN', 2.4, K['CHU'], 'C', bold=True)
    sh.text(47, 246.5, 'SWITCHING', 2.4, K['CHU'], 'C', bold=True)
    sh.text(47, 241.5, '24VDC / 10A', 2.0, K['CHU'], 'C')
    sh.text(47, 236.5, 'SITOP PSU100S', 1.8, K['CHU'], 'C', color=8)
    sh.line(36, 230, 36, 226, K['DAY'])
    sh.earth(36, 225.5)
    sh.text(39, 228.5, 'PE', 2.0, K['CHU'], 'L', color=8)

    # đầu ra DC -> thanh cái +24V / 0V
    X24 = 72.0
    sh.line(64, 254, X24, 254, K['DAY'])
    sh.text(68, 256.3, '+24V', 2.0, K['CHU'], 'C')
    sh.line(64, 246, 68, 246, K['DAY'])
    sh.line(68, 246, 68, 57, K['DAY'])          # dây 0V chạy xuống bar đáy
    sh.line(X24, 254, X24, 64, K['DAY'], lw=60)

    # ================= KHU VỰC 2: TÍN HIỆU VÀO (x 78..158) =================
    XR = 162.0        # mép trái rack 0

    # ---- DI (thường) ----
    di_rows = [
        (254, 'SB1', 'VAN BAFFLE – MỞ/ĐÓNG', 'I0.0'),
        (243, 'SF1', 'BÁO LỖI BIẾN TẦN (VFD)', 'I0.1'),
        (232, 'SE1', 'TỐC ĐỘ ROTOR (ENCODER)', 'I0.2'),
        (221, 'SL1', 'LIÊN KẾT TRẠM (INTERLOCK)', 'I0.3'),
        (210, 'SB2', 'HÃM MÁY PHÁT (BRAKE)', 'I0.4'),
    ]
    for y, ref, name, addr in di_rows:
        sh.line(X24, y, 78, y, K['DAY'])
        sh.dot(X24, y, 0.55)
        sh.contact(78, y, K['DAY'])
        sh.line(86, y, XR, y, K['DAY'])
        sh.text(82, y + 3.2, ref, 2.2, K['CHU'], 'C', bold=True)
        sh.text(112, y - 3.5, name, 2.0, K['CHU'], 'L')
        sh.text(156, y + 1.8, addr, 2.0, K['PLC'], 'R')

    # ---- F-DI (an toàn – đỏ) ----
    sh.text(78, 196, 'MẠCH AN TOÀN: DỪNG KHẨN E-STOP (2 KÊNH)', 2.2, K['AT'], 'L', bold=True)
    fdi_rows = [
        (186, 'SB0-1', 'NÚT DỪNG KHẨN – KÊNH 1', 'F-DI 0.0'),
        (175, 'SB0-2', 'NÚT DỪNG KHẨN – KÊNH 2', 'F-DI 0.1'),
    ]
    for y, ref, name, addr in fdi_rows:
        sh.line(X24, y, 78, y, K['AT'])
        sh.dot(X24, y, 0.55, K['AT'])
        sh.contact(78, y, K['AT'], nc=True)
        sh.line(86, y, XR, y, K['AT'])
        sh.text(82, y + 3.2, ref, 2.2, K['AT'], 'C', bold=True)
        sh.text(112, y - 3.5, name, 2.0, K['AT'], 'L')
        sh.text(156, y + 1.8, addr, 2.0, K['PLC'], 'R')

    # ---- AI (analog – xanh lam) ----
    sh.text(78, 162, 'TÍN HIỆU ANALOG (4–20mA / 0–10V)', 2.2, K['AN'], 'L', bold=True)
    ai_rows = [
        (138, 'TT-1', 'NHIỆT ĐỘ DẦU (OIL TEMP)', '4–20mA', 'IW64'),
        (127, 'FT-1', 'LƯU LƯỢNG DẦU (OIL FLOW)', '4–20mA', 'IW66'),
        (116, 'ST-1', 'TỐC ĐỘ ROTOR (SPEED)', '0–10V', 'IW68'),
    ]
    for y, ref, name, rng, addr in ai_rows:
        sh.rect(78, y - 4, 30, 8, K['AN'])
        sh.line(X24, y, 78, y, K['AN'])
        sh.dot(X24, y, 0.55, K['AN'])
        sh.text(93, y + 1.6, ref, 2.2, K['AN'], 'C', bold=True)
        sh.text(93, y - 2.2, rng, 1.7, K['AN'], 'C')
        sh.line(108, y, XR, y, K['AN'])
        sh.text(112, y - 3.5, name, 2.0, K['AN'], 'L')
        sh.text(156, y + 1.8, addr, 2.0, K['PLC'], 'R')
    sh.text(78, 107, 'Chân M (chung) của thẻ AI nối về 0V nguồn, cáp chống nhiễu.',
            2.0, K['AN'], 'L', color=8)

    # ================= TỦ PLC =================
    # rack trái (nhập): x 162..198, y 96..262
    sh.rect(162, 96, 36, 166, K['PLC'], lw=35)
    sh.text(162, 264.5, 'TỦ PLC – RACK 0', 2.5, K['CHU'], 'L', bold=True)
    slots_left = [
        (246, 262, 'PM 24VDC', 'NGUỒN PLC'),
        (204, 246, 'DI 16×24VDC', '6ES7 521-1BL00'),
        (172, 204, 'CPU 1511F-1 PN', 'FAIL-SAFE'),
        (148, 172, 'F-DI 8×24VDC', 'AN TOÀN (F)'),
        (112, 148, 'AI 4×U/I ST', '6ES7 531-7KF00'),
        (96, 112, 'DỰ PHÒNG', ''),
    ]
    for y0, y1, t1, t2 in slots_left:
        cy = (y0 + y1) / 2
        sh.text(180, cy + (1.6 if t2 else 0), t1, 2.1, K['PLC'], 'C', bold=True)
        if t2:
            sh.text(180, cy - 2.0, t2, 1.6, K['CHU'], 'C', color=8)
    for y0, y1, t1, t2 in slots_left[:-1]:
        sh.line(162, y0, 198, y0, K['PLC'], lw=18, color=8)
    sh.line(180, 96, 180, 92.5, K['DAY'])
    sh.earth(180, 92)
    sh.text(183, 93.5, 'PE', 2.0, K['CHU'], 'L', color=8)

    # rack phải (xuất): x 246..282, y 96..262
    sh.rect(246, 96, 36, 166, K['PLC'], lw=35)
    sh.text(246, 264.5, 'RACK 1 – MỞ RỘNG', 2.5, K['CHU'], 'L', bold=True)
    slots_right = [
        (182, 262, 'DQ 16×24VDC', '6ES7 522-1BL01'),
        (128, 182, 'AQ 2×U/I ST', '6ES7 532-5HF00'),
        (96, 128, 'DỰ PHÒNG', ''),
    ]
    for y0, y1, t1, t2 in slots_right:
        cy = (y0 + y1) / 2
        sh.text(264, cy + (1.6 if t2 else 0), t1, 2.1, K['PLC'], 'C', bold=True)
        if t2:
            sh.text(264, cy - 2.0, t2, 1.6, K['CHU'], 'C', color=8)
    for y0, y1, t1, t2 in slots_right[:-1]:
        sh.line(246, y0, 282, y0, K['PLC'], lw=18, color=8)

    # bus nối 2 rack
    for yy in (252, 256):
        sh.line(198, yy, 246, yy, K['PLC'])
        sh.dot(198, yy, 0.5, K['PLC'])
        sh.dot(246, yy, 0.5, K['PLC'])
    sh.text(222, 259.5, 'BUS PLC (PROFINET IO)', 1.9, K['CHU'], 'C', color=8)

    # ================= KHU VỰC 3: TÍN HIỆU RA (x 286..408) =================
    X0R = 398.0       # thanh 0V bên phải
    sh.line(X0R, 258, X0R, 57, K['DAY'], lw=60)
    sh.line(X0R, 57, 68, 57, K['DAY'], lw=60)          # bar đáy 0V (nối về nguồn)
    sh.text(X0R, 261, '0V', 2.2, K['CHU'], 'C')

    do_rows = [
        (254, 'K1', 'CHUÔNG BÁO ĐỘNG (HOOTER)', 'Q0.0'),
        (243, 'K2', 'ĐÈN BÁO SỰ CỐ (BEACON)', 'Q0.1'),
        (232, 'K3', 'VAN BAFFLE – MỞ', 'Q0.2'),
        (221, 'K4', 'VAN BAFFLE – ĐÓNG', 'Q0.3'),
        (210, 'K5', 'CHẠY BƠM DẦU (OIL PUMP)', 'Q0.4'),
        (199, 'K6', 'HÃM PHANH (BRAKE)', 'Q0.5'),
        (188, 'K7', 'DỪNG KHẨN – TRIP', 'Q0.6'),
    ]
    for y, ref, name, addr in do_rows:
        sh.line(282, y, 292, y, K['DAY'])
        sh.dot(282, y, 0.45)
        sh.text(287, y + 1.8, addr, 2.0, K['PLC'], 'C')
        sh.coil(297, y)
        sh.text(297, y + 3.8, ref, 2.2, K['CHU'], 'C', bold=True)
        sh.line(302, y, 306, y, K['DAY'])
        sh.rect(306, y - 4, 46, 8, K['TB'])
        sh.text(329, y, name, 2.0, K['CHU'], 'C')
        sh.line(352, y, X0R, y, K['DAY'])
        sh.dot(X0R, y, 0.55)

    # ---- AQ -> VFD ----
    sh.line(282, 156, 306, 156, K['AN'])
    sh.dot(282, 156, 0.45, K['AN'])
    sh.text(292, 158.2, 'QW80', 2.0, K['PLC'], 'C')
    sh.rect(306, 140, 74, 30, K['AN'], lw=35)
    sh.text(343, 165, 'BIẾN TẦN BƠM DẦU (VFD)', 2.6, K['AN'], 'C', bold=True)
    sh.text(343, 159.5, 'Tham chiếu tốc độ: 0–10V ← AQ (QW80)', 2.0, K['AN'], 'C')
    sh.text(343, 154.5, 'Lệnh Chạy/Dừng: Q0.4 → K5', 2.0, K['AN'], 'C')
    sh.text(343, 149.5, 'Động lực: 3~ 380V – 3.7kW', 2.0, K['AN'], 'C')
    sh.text(343, 144.5, 'Báo lỗi VFD → SF1 (I0.1)', 2.0, K['AN'], 'C', color=8)
    sh.line(380, 146, X0R, 146, K['AN'])
    sh.dot(X0R, 146, 0.55)
    sh.text(385, 148.2, 'GND', 1.8, K['AN'], 'C', color=8)

    sh.line(282, 132, 302, 132, K['AN'])
    sh.dot(282, 132, 0.45, K['AN'])
    sh.text(292, 134.2, 'QW82', 2.0, K['PLC'], 'C')
    sh.text(304, 132, 'DỰ PHÒNG', 2.0, K['AN'], 'L', color=8)

    # ================= GHI CHÚ (góc phải dưới) =================
    sh.line(248, 93.5, 392, 93.5, K['KHUNG'], lw=18, color=8)
    sh.text(250, 88.5, 'GHI CHÚ / NOTES:', 3.0, K['CHU'], 'L', bold=True)
    notes = [
        '1. Bản vẽ hiển thị trạng thái KHÔNG KÍCH ĐỘNG (de-energized).',
        '2. Cáp DI: 2×0.75mm²; cáp analog chống nhiễu, nối đất chụp 1 đầu.',
        '3. E-STOP: mạch kép Cat.3 / PL d, bắt buộc dùng tiếp điểm NC.',
        '4. Địa chỉ I/O khớp phần cứng TIA Portal V18 – SimLogic_V18.ap18.',
        '5. Ký hiệu IEC 60617 • đi dây IEC 60204-1 • HMI: WinCC RT Adv.',
    ]
    for i, s in enumerate(notes):
        sh.text(250, 83 - i * 5.8, s, 2.1, K['CHU'], 'L')

    # ================= MẠCH HOA (góc trái dưới) =================
    sh.text(13, 98, '4. MẠCH CHỌN CHẾ ĐỘ HOA (HAND – OFF – AUTO)', 3.0, K['CHU'], 'L', bold=True)
    sh.flag24(26, 92, K['DAY'])
    sh.line(26, 88, 26, 62, K['DAY'])
    for yy, lb in ((84, 'TAY'), (74, '0'), (64, 'TỰ ĐỘNG')):
        sh.dot(26, yy, 0.5)
        sh.text(24, yy, lb, 2.1, K['CHU'], 'R')
    sh.line(26, 74, 30.5, 78.5, K['DAY'], lw=35)      # cần gạt ở vị trí TAY
    sh.text(17, 74, 'SA1', 2.0, K['CHU'], 'R', bold=True)
    sh.line(26, 84, 42, 84, K['DAY'])
    sh.line(26, 64, 42, 64, K['DAY'])
    sh.line(42, 84, 42, 64, K['DAY'])
    sh.line(42, 74, 50, 74, K['DAY'])
    sh.coil(55, 74)
    sh.text(55, 78.2, 'KA1', 2.2, K['CHU'], 'C', bold=True)
    sh.line(60, 74, 68, 74, K['DAY'])
    sh.dot(68, 74, 0.5)                      # nối vào dây 0V dọc
    sh.text(13, 53.5, 'TAY: vận hành qua nút nhấn/núm vặn tại tủ.   TỰ ĐỘNG: PLC điều khiển theo chương trình.',
            2.1, K['CHU'], 'L')
    sh.text(13, 49, 'KA1: rêle chọn chế độ TAY. Tiếp điểm K5 cấp lệnh Run cho biến tần bơm dầu.',
            2.1, K['CHU'], 'L')

    # ================= CHÚ THÍCH MÀU + TÀI LIỆU THAM CHIẾU =================
    sh.text(13, 40, 'CHÚ THÍCH MÀU LỚP (LAYER):', 2.4, K['CHU'], 'L', bold=True)
    legend = [
        (13, 34, 7, 'Dây điện / khung'),
        (78, 34, 2, 'PLC'),
        (110, 34, 3, 'Thiết bị'),
        (165, 34, 4, 'Analog'),
        (13, 29, 1, 'An toàn (E-STOP)'),
        (78, 29, 6, 'Tụ/bus (SLD)'),
        (110, 29, 8, 'Ghi chú phụ'),
    ]
    for lx, ly, lc, lb in legend:
        sh.line(lx, ly, lx + 8, ly, K['DAY'], lw=60, color=lc)
        sh.text(lx + 10, ly, lb, 2.0, K['CHU'], 'L', color=None if lc != 8 else 8)
    return sh


# ======================================================================
# TỜ 2 – SƠ ĐỘ MỘT ĐƯỜNG ĐIỆN (SLD)
# ======================================================================
def sheet2(msp):
    sh = Sheet(msp, 480, 0)
    draw_frame(sh, 'SƠ ĐỘ MỘT ĐƯỜNG ĐIỆN (SLD)', 'TD-02')

    sh.text(12, 281, 'SƠ ĐỘ MỘT ĐƯỜNG ĐIỆN (SLD) – NHÀ MÁY THỦY ĐIỆN NỘI BỘ',
            5.0, K['CHU'], 'L', bold=True)
    sh.text(12, 266, '1. NHÓM MÁY PHÁT & TUA BIN', 3.0, K['CHU'], 'L', bold=True)
    sh.text(100, 266, '2. TỤ ĐIỆN & CÁC NGUỒN TẢI RA', 3.0, K['CHU'], 'L', bold=True)
    sh.text(210, 266, '3. BẢNG THÔNG SỐ CHÍNH', 3.0, K['CHU'], 'L', bold=True)

    # ---- tua bin + nước ----
    sh.line(30, 258, 30, 254, K['TB'])
    sh.arrow(30, 253.5, 270, 2.4, K['TB'])
    sh.text(33, 256.5, 'ỐNG DẪN NƯỚC (PENSTOCK)', 2.0, K['CHU'], 'L', color=8)
    sh.rect(24, 244, 20, 9, K['TB'])
    sh.text(34, 248.5, 'TUA BIN', 2.4, K['CHU'], 'C', bold=True)
    sh.line(34, 244, 34, 197, K['TB'])              # trục
    sh.text(30.5, 220, 'TRỤC', 1.6, K['CHU'], 'L', rot=90, color=8)

    # ---- máy phát ----
    sh.circle(34, 189, 8, K['TB'])
    sh.text(34, 190.5, 'G', 4.5, K['CHU'], 'C', bold=True)
    sh.text(34, 186, '3~', 2.6, K['CHU'], 'C')
    sh.text(62, 192, 'MÁY PHÁT ĐỒNG BỘ (G)', 2.2, K['CHU'], 'L', bold=True)
    sh.text(62, 188, '3~ 400V – 100kVA – 50Hz', 2.0, K['CHU'], 'L', color=8)
    sh.text(62, 184, '1500 v/ph – cosφ 0,8', 2.0, K['CHU'], 'L', color=8)

    # ---- trung tính nối đất ----
    sh.line(42, 189, 56, 189, K['DAY'])
    sh.text(58.5, 190.5, 'N', 2.4, K['CHU'], 'L')
    sh.line(56, 189, 56, 180, K['DAY'])
    sh.earth(56, 179.5, K['DAY'])

    # ---- 3 pha: dao cách ly Q0 + cầu dao Q1 ----
    leads = [(28, 'L1'), (34, 'L2'), (40, 'L3')]
    for lx, lb in leads:
        sh.line(lx, 181, lx, 140, K['DAY'])
        sh.text(lx - 1.8, 158, lb, 2.0, K['CHU'], 'R')
        sh.dot(lx, 170, 0.45)
        sh.dot(lx, 164, 0.45)
        sh.line(lx, 164, lx + 3, 169, K['DAY'])
        sh.rect(lx - 3, 146, 6, 8, K['TB'])
    sh.text(47, 168, 'Q0 – Dao cách ly', 2.0, K['CHU'], 'L', color=8)
    sh.text(47, 151, 'Q1 – ACB 250A (LSI)', 2.0, K['CHU'], 'L', color=8)

    # ---- tụ điện (bus) ----
    sh.line(20, 140, 190, 140, K['TC'], lw=60)
    sh.text(105, 144, 'TỤ ĐIỆN 3~ 400V / 50Hz', 3.0, K['CHU'], 'C', bold=True)
    for lx, _ in leads:
        sh.dot(lx, 140, 0.6)

    # ---- bộ đo ----
    sh.dot(60, 140, 0.6)
    sh.line(60, 140, 60, 134, K['DAY'])
    sh.text(63, 134, 'BỘ ĐO V/A/kWh', 1.9, K['CHU'], 'L', color=8)

    # ---- các nhánh tải ----
    def feeder(x, ref, draw_load):
        sh.line(x, 140, x, 116, K['DAY'])
        sh.dot(x, 140, 0.6)
        sh.rect(x - 3, 116, 6, 8, K['TB'])
        sh.text(x + 4.5, 120, ref, 2.0, K['CHU'], 'L')
        draw_load(x)

    def load_t1(x):
        sh.line(x, 116, x, 104, K['DAY'])
        sh.circle(x, 98, 6, K['TB'])
        sh.circle(x, 90, 6, K['TB'])
        sh.text(x, 79, 'MBA T1 – TĂNG ÁP', 1.9, K['CHU'], 'C', bold=True)
        sh.text(x, 75.5, '400/22kV – 125kVA', 1.7, K['CHU'], 'C', color=8)
        sh.text(x, 72, 'Nối hình Dyn11', 1.7, K['CHU'], 'C', color=8)
        sh.line(x, 84, x, 68, K['DAY'])
        sh.arrow(x, 67.5, 270, 2.6, K['DAY'])
        sh.text(x, 63.5, 'Ra trạm 22kV', 1.9, K['CHU'], 'C')

    def load_motor(x):
        sh.line(x, 116, x, 101, K['DAY'])
        sh.circle(x, 95, 5.5, K['TB'])
        sh.text(x, 96, 'M', 3.0, K['CHU'], 'C', bold=True)
        sh.text(x, 92, '3~', 2.0, K['CHU'], 'C')
        sh.line(x, 89.5, x, 84, K['DAY'])
        sh.text(x, 79, 'TẢI NỘI BỘ', 1.9, K['CHU'], 'C', bold=True)
        sh.text(x, 75.5, 'Bơm – chiếu sáng', 1.7, K['CHU'], 'C', color=8)
        sh.text(x, 72, 'hậu cần', 1.7, K['CHU'], 'C', color=8)

    def load_ups(x):
        sh.line(x, 116, x, 102, K['DAY'])
        sh.rect(x - 8, 92, 16, 10, K['TB'])
        sh.text(x, 97, 'UPS/DC', 2.0, K['CHU'], 'C', bold=True)
        sh.line(x, 92, x, 86, K['DAY'])
        sh.earth(x, 85.5, K['DAY'])
        sh.text(x, 79, 'TỦ PLC + HMI', 1.9, K['CHU'], 'C', bold=True)
        sh.text(x, 75.5, '+ BÁO ĐỘNG', 1.7, K['CHU'], 'C', color=8)
        sh.text(x, 72, 'Dự phòng ≥ 15 phút', 1.7, K['CHU'], 'C', color=8)

    def load_cap(x):
        sh.line(x, 116, x, 103, K['DAY'])
        sh.line(x - 6, 100, x + 6, 100, K['TB'])
        sh.line(x - 6, 96, x + 6, 96, K['TB'])
        sh.line(x, 103, x, 100, K['DAY'])
        sh.line(x, 96, x, 92, K['DAY'])
        sh.line(x, 92, x, 88, K['DAY'])
        sh.earth(x, 87.5, K['DAY'])
        sh.text(x, 79, 'BỘ TỤ BÙ', 1.9, K['CHU'], 'C', bold=True)
        sh.text(x, 75.5, '3×20kVAr', 1.7, K['CHU'], 'C', color=8)
        sh.text(x, 72, 'Điều khiển tự động', 1.7, K['CHU'], 'C', color=8)

    feeder(45, 'Q2', load_t1)
    feeder(90, 'Q3', load_motor)
    feeder(135, 'Q4', load_ups)
    feeder(180, 'Q5', load_cap)

    # ---- bảng thông số ----
    bx, by = 210, 138
    col1, col2 = 90, 88
    rows = [
        ('THÔNG SỐ', 'GIÁ TRỊ'),
        ('Công suất danh định', '100 kVA / 80 kW'),
        ('Điện áp phát', '3~ 400V – 50Hz'),
        ('Tốc độ định mức', '1500 v/ph'),
        ('Hệ số công suất', 'cosφ = 0.8'),
        ('Điện áp ra (sau T1)', '22 kV'),
        ('Dòng điện định mức', '144 A'),
        ('Bộ tụ bù', '60 kVAr'),
        ('UPS tủ điều khiển', '1 kVA / 15 phút'),
    ]
    rh = 12.0
    sh.rect(bx, by, col1 + col2, rh * len(rows), K['KHUNG'], lw=35)
    for i in range(1, len(rows)):
        sh.line(bx, by + i * rh, bx + col1 + col2, by + i * rh, K['KHUNG'], lw=18, color=8)
    sh.line(bx + col1, by, bx + col1, by + rh * len(rows), K['KHUNG'])
    for i, (a2, b2) in enumerate(rows):
        yy = by + (len(rows) - i - 0.5) * rh
        bold = (i == 0)
        sh.text(bx + 3, yy, a2, 2.2, K['CHU'], 'L', bold=bold)
        sh.text(bx + col1 + 3, yy, b2, 2.2, K['CHU'], 'L', bold=bold)

    # ---- ghi chú ----
    sh.line(210, 101, 410, 101, K['KHUNG'], lw=18, color=8)
    sh.text(212, 96, 'GHI CHÚ / NOTES:', 3.0, K['CHU'], 'L', bold=True)
    notes2 = [
        '1. Sơ đồ vẽ dạng một đường (single line), đại diện 3 pha.',
        '2. Q1: ACB 250A có bảo vệ quá tải + ngắn mạch (LSI), đồng bộ với lưới.',
        '3. T1: MBA tăng áp 400/22kV, 125kVA, Dyn11 – đóng cắt qua Q2.',
        '4. Bộ tụ bù điều khiển tự động theo hệ số công suất (cosφ ≥ 0,92).',
        '5. Tủ PLC/HMI cấp nguồn qua UPS 1kVA, dự phòng ≥ 15 phút.',
    ]
    for i, s2 in enumerate(notes2):
        sh.text(212, 91.5 - i * 5.2, s2, 2.1, K['CHU'], 'L')
    return sh


# ======================================================================
# Xuất file + ảnh xem trước
# ======================================================================
def render_png(doc, msp, png_path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    fig = plt.figure(figsize=(16.8, 11.88), facecolor='#101418')
    ax = fig.add_axes([0, 0, 1, 1], facecolor='#101418')
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend).draw_layout(msp, finalize=True)
    fig.savefig(png_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    import os
    here = os.path.dirname(os.path.abspath(__file__))

    # ---- Tờ 1 ----
    doc1 = new_doc()
    msp1 = doc1.modelspace()
    sheet1(msp1)
    f1 = os.path.join(here, 'TD-01_so_do_mach_dieu_khien_PLC_R2007.dxf')
    doc1.saveas(f1)
    print('Đã tạo:', f1)

    # ---- Tờ 2 ----
    doc2 = new_doc()
    msp2 = doc2.modelspace()
    sheet2(msp2)
    f2 = os.path.join(here, 'TD-02_so_do_mot_duong_dien_R2007.dxf')
    doc2.saveas(f2)
    print('Đã tạo:', f2)

    # ---- ảnh xem trước ----
    render_png(doc1, msp1, os.path.join(here, 'TD-01_preview.png'))
    render_png(doc2, msp2, os.path.join(here, 'TD-02_preview.png'))
    print('Đã tạo ảnh xem trước.')


if __name__ == '__main__':
    main()
