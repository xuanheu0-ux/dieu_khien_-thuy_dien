# PLC Source — Nhà máy thủy điện mô phỏng (SCL)

Toàn bộ chương trình điều khiển đã được viết lại bằng **SCL (IEC 61131-3)** theo đúng mô tả trong README gốc:

- CPU: **Siemens S7-1511F-1 PN** (TIA Portal V18)
- HMI: **WinCC RT Advanced**
- 5 tín hiệu vào (Baffle, Oil Pump VFD, Rotor Speed, Power Station Interlock, Generator Brake)
- 7 điều kiện báo động (Overcurrent, High Oil Temp, Rotor Overspeed, Oil Low Flow, Oil High Flow, E-Stop, Brake Failure)
- **Hand-Off-Auto** cho mọi thiết bị (kể cả setpoint tay cho thiết bị analog)
- Trình tự khởi động / chạy / dừng / trip an toàn

> **Lưu ý:** file `SimLogic_V18.ap18` ở gốc repo là file project **rỗng** (chỉ chứa tên project + version 18.0.1.0).
> Bạn cần tạo project TIA Portal mới và import mã nguồn bên dưới (hoặc thay file .ap18 này bằng project đầy đủ của bạn khi có).
> Mã nguồn SCL hoàn toàn tương đương LD/FBD — sau khi import, bạn có thể xem lại từng block trong TIA Portal.

---

## 1. Cấu trúc thư mục

```
PLC_Source/
├── DB_HydroPlant.db     ← Data block chứa TOÀN BỘ dữ liệu quy trình
├── OB1_Main.st          ← OB1 Main: state machine + gọi các FC theo thứ tự
├── FC_AI_Process.st     ← Xử lý Analog Input (scale + kiểm tra tín hiệu)
├── FC_Alarms.st         ← 7 báo động + latched trip
├── FC_PI_Baffle.st      ← Governor: bộ điều khiển PI (tốc độ → baffle)
├── FC_AO_Control.st     ← Analog Output cuối cùng (HOA + an toàn)
├── FC_DI_Control.st     ← Digital Output cuối cùng (HOA + interlock)
└── README.md            ← tài liệu này
```

Sơ đồ luồng trong OB1 (mỗi vòng quét):

```
OB1_Main
 ├── 1. FC_AI_Process   : raw AI → giá trị công trình + AI_Good
 ├── 2. FC_Alarms       : 7 alarm + latched trip
 ├── 3. FC_PI_Baffle    : governor AUTO (baffle %)
 ├── 4. State machine   : STOP / STARTING / RUNNING / STOPPING / TRIP
 ├── 5. FC_AO_Control   : HOA + an toàn → AO cuối cùng
 └── 6. FC_DI_Control   : HOA + interlock → DO cuối cùng
```

## 2. Import vào TIA Portal

1. Tạo project TIA Portal V18 → **Add new device** → CPU → `CPU 1511F-1 PN` (order number 6ES7 511-1FK02-0AB0 hoặc bản tương ứng).
2. Mở cây thiết bị → `PLC_1 [S7-1500]`:
   - Chuột phải **Data blocks** → **Import...** → chọn `DB_HydroPlant.db`.
   - Với mỗi file `.st`:
     - Chuột phải **Program blocks** → **Add new block** → chọn type (Function/Organization block), language **SCL**, đặt **đúng tên** trong bảng dưới → mở block → **dán toàn bộ nội dung file** vào editor.
3. **Gán giá trị mặc định** (Initial values) cho DB_HydroPlant — xem bảng mục 4.
4. Chuột phải **CPU_1** → **Build** → **Compile** — phải ra `0 error, 0 warning` (có thể có warning do chưa dùng hết tag).
5. **Download** vào CPU (hoặc dùng **Simulator** — S7-PLCSIM — để chạy mô phỏng).
6. Tạo các tag phần cứng/simulator như bảng mục 5, rồi chuyển CPU sang RUN.

### Bảng block cần tạo

| File | Type trong TIA | Tên block (đúng) |
|---|---|---|
| DB_HydroPlant.db | Data block (import) | `DB_HydroPlant` (optimized) |
| OB1_Main.st | Organization block | dán vào `Main [OB1]` có sẵn |
| FC_AI_Process.st | Function | `FC_AI_Process` |
| FC_Alarms.st | Function | `FC_Alarms` |
| FC_PI_Baffle.st | Function | `FC_PI_Baffle` |
| FC_AO_Control.st | Function | `FC_AO_Control` |
| FC_DI_Control.st | Function | `FC_DI_Control` |

## 3. Logic chính (tóm tắt)

### 3.1 State machine (OB1)

| State | Ý nghĩa | Hành vi chính |
|---|---|---|
| 0 STOP | Dừng | Baffle 0, phanh giữ, bơm dầu tắt. Bắt đầu khi: nút START + không có alarm/trip |
| 1 STARTING | Khởi động | Bật bơm dầu 50 Hz → sau 5s + lưu lượng dầu OK → nhả phanh → sau 10s mở baffle 15% → đạt 90% tốc độ lấy load setpoint → đạt 98% + ổn định 20s + interlock đóng → đóng contactor chính |
| 2 RUNNING | Chạy | Governor PI giữ tốc độ = SP_RotorSpeed, contactor chính theo interlock, kích từ 100% |
| 3 STOPPING | Dừng | Mở contactor → baffle về 0 → tốc độ < 15 RPM → hãm phanh → bơm dầu chạy mát 30s → về STOP |
| 4 TRIP | Bảo vệ | Baffle đóng tức thời, mở contactor, hãm phanh khi tốc độ < 50% định mức, bơm dầu chạy mát 30s. Về STOP khi: TRIP RESET + hết alarm + roto dừng hẳn |

### 3.2 Hand-Off-Auto

| Thiết bị | Tag HOA (TRUE = HAND) | Setpoint HAND |
|---|---|---|
| Baffle | `HOA_Baffle_Hand` | `SP_Baffle_Hand` [0–100 %] |
| Oil Pump VFD | `HOA_OilPump_Hand` | `SP_OilPump_Hand` [0–50 Hz] |
| Gen. Voltage | `HOA_Voltage_Hand` | `SP_Voltage_Hand` [0–100 %] |
| Công tắc bơm dầu | `HOA_PumpSwitch_Hand` | `CMD_OilPumpHand` (run/stop) |

**Nguyên tắc an toàn:** khi `Trip` hoặc E-Stop đang latch, mọi lệnh HAND bị vô hiệu — baffle ép về 0, phanh ép hãm, contactor ép mở, kích từ ép 0.

### 3.3 Bảng báo động

| # | Alarm | Điều kiện | Debounce | Kết quả |
|---|---|---|---|---|
| 1 | `ALM_OverCurrent` | `GenCurrent > LIM_CurrentOver` (110 A) | 2 s | Alarm + **Trip** |
| 2 | `ALM_HighOilTemp` | `OilTemp > LIM_TempHi` (70 °C) | 2 s | Alarm; **Trip** nếu > `LIM_TempTrip` (80 °C) |
| 3 | `ALM_Overspeed` | `RotorSpeed > LIM_SpeedOver` (330 RPM) | 0.2 s | Alarm + **Trip** |
| 4 | `ALM_OilLowFlow` | `OilFlow < LIM_FlowLo` (30 %) | 5 s | Alarm; **Trip** nếu < `LIM_FlowTrip` (10 %) trong 5 s |
| 5 | `ALM_OilHighFlow` | `OilFlow > LIM_FlowHi` (95 %) | 5 s | Alarm |
| 6 | `ALM_EStop` | `DI_EStop = TRUE` | tức thời | Alarm + **Trip** (latch đến khi nhấn RESET sau khi nhả E-Stop) |
| 7 | `ALM_BrakeFail` | Lệnh nhả phanh có hiệu lực nhưng phanh vẫn hãm > 10 s | 10 s | Alarm |

Mọi alarm: **latch** (giữ trạng thái) cho đến khi nhấn `CMD_AlarmReset` **và** điều kiện đã hết.
Trip: latch riêng, xóa bằng `CMD_TripReset` (nếu nguyên nhân chưa hết sẽ trip lại ngay).

### 3.4 Governor (PI)

- `PI_Output = PI_Kp × (SP_RotorSpeed − RotorSpeed) + PI_Integral`
- Anti-windup: tích phân bị chặn khi output đã no (0% hoặc 100%).
- Chỉ chạy ở state RUNNING, chế độ AUTO, và tín hiệu tốc độ hợp lệ (`AI_Good`).
- Handover không xóc (bumpless): khi sang RUNNING, `PI_Integral` được nạp bằng baffle hiện tại.

## 4. Giá trị mặc định (gán vào Initial values của DB)

| Tag | Type | Mặc định | Ý nghĩa |
|---|---|---|---|
| `SP_RotorSpeed` | REAL | `300.0` | Tốc độ định mức [RPM] |
| `SP_Baffle_Load` | REAL | `40.0` | Baffle chạy định mức [0–100 %] |
| `LIM_SpeedOver` | REAL | `330.0` | Overspeed trip [RPM] (110 % định mức) |
| `LIM_TempHi` | REAL | `70.0` | Alarm nhiệt độ dầu [°C] |
| `LIM_TempTrip` | REAL | `80.0` | Trip nhiệt độ dầu [°C] |
| `LIM_FlowLo` | REAL | `30.0` | Alarm lưu lượng dầu thấp [%] |
| `LIM_FlowTrip` | REAL | `10.0` | Trip lưu lượng dầu [%] |
| `LIM_FlowHi` | REAL | `95.0` | Alarm lưu lượng dầu cao [%] |
| `LIM_CurrentOver` | REAL | `110.0` | Overcurrent [A] (định mức 100 A) |
| `PI_Kp` | REAL | `0.5` | Gain tỷ lệ [%/RPM] |
| `PI_Ki` | REAL | `0.05` | Gain tích phân [%/RPM/s] |

Các tag còn lại mặc định `0` / `FALSE`.

> **Tuần tự quét:** mọi bộ định thời giả định **chu kỳ quét 100 ms** (bước 0.1 s). Nếu đổi chu kỳ, sửa các hằng `0.1` trong `FC_Alarms.st`, `FC_PI_Baffle.st`, `OB1_Main.st`.

## 5. Bảng tag cho HMI / Simulator

### Input quy trình (HMI/Simulator → PLC)

| Tag | Range | Ghi chú |
|---|---|---|
| `AI_BaffleRaw` | 0–100 % | Vị trí baffle thực tế (phản hồi) |
| `AI_OilPumpFreqRaw` | 0–50 Hz | Tốc độ VFD bơm dầu thực tế |
| `AI_RotorSpeedRaw` | 0–400 RPM | Tốc độ roto (phản hồi) |
| `AI_OilTempRaw` | 0–120 °C | Nhiệt độ dầu |
| `AI_OilFlowRaw` | 0–120 % | Lưu lượng dầu |
| `AI_GenCurrentRaw` | 0–200 A | Dòng máy phát |
| `DI_EStop` | BOOL | Nút E-Stop (TRUE = nhấn) |
| `DI_GenBrake` | BOOL | Phanh đang hãm (TRUE = hãm) |
| `DI_GridInterlock` | BOOL | Interlock trạm điện đóng (TRUE = cho phép đóng lưới) |
| `DI_OilPump` | BOOL | Bơm dầu đang chạy (phản hồi) |

### Lệnh / Setpoint / HOA (HMI → PLC, cho phép ghi)

| Tag | Ý nghĩa |
|---|---|
| `CMD_Start` / `CMD_Stop` | Nút START / STOP (momentary) |
| `CMD_AlarmReset` / `CMD_TripReset` | Nút RESET alarm / RESET trip (momentary) |
| `CMD_OilPumpHand` | Chạy/tắt bơm dầu thủ công (khi HOA_PumpSwitch_Hand) |
| `HOA_Baffle_Hand` `HOA_OilPump_Hand` `HOA_Voltage_Hand` `HOA_PumpSwitch_Hand` | Công tắc chế độ Hand/Auto |
| `SP_RotorSpeed` `SP_Baffle_Load` | Setpoint AUTO |
| `SP_Baffle_Hand` `SP_OilPump_Hand` `SP_Voltage_Hand` | Setpoint HAND |

### Output (PLC → HMI/Simulator, chỉ đọc để hiển thị; simulator ghi ngược các AI)

| Tag | Ý nghĩa |
|---|---|
| `AO_BaffleCmd` | Lệnh baffle [0–100 %] |
| `AO_OilPumpFreqCmd` | Lệnh tần số VFD bơm dầu [0–50 Hz] |
| `AO_GenVoltage` | Lệnh điện áp/kích từ [0–100 %] |
| `DO_OilPumpRun` | Chạy bơm dầu |
| `DO_BrakeRelease` | Nhả phanh (TRUE = nhả) |
| `DO_MainContactor` | Contactor chính (đóng lưới) |
| `DO_AlarmLamp` | Đèn/bộ báo động tổng |
| `DO_EStopLatched` | Trạng thái E-Stop đang latch |
| `DO_Running` | Nhà máy đang chạy (RUNNING + đóng lưới) |
| `PlantState` | 0/1/2/3/4 = STOP/STARTING/RUNNING/STOPPING/TRIP |
| `BafflePos` `OilPumpFreq` `RotorSpeed` `OilTemp` `OilFlow` `GenCurrent` | Giá trị công trình đã scale |
| `ALM_OverCurrent` `ALM_HighOilTemp` `ALM_Overspeed` `ALM_OilLowFlow` `ALM_OilHighFlow` `ALM_EStop` `ALM_BrakeFail` `ALM_Any` | Các báo động |
| `Trip` `StateTime` `CoolDownTimer` | Trạng thái trip / thời gian state / timer chạy mát |
| `PI_Output` `PI_Integral` `PI_PrevError` | Giám sát governor |

## 6. Gợi ý cho simulator (HMI "đổi môi trường")

Vì đây là nhà máy mô phỏng, HMI/simulator cần đóng vai "thế giới vật lý" — mỗi vòng quét (~100 ms):

1. Đọc `AO_BaffleCmd`, `AO_OilPumpFreqCmd`, `DO_*` từ PLC.
2. Tính phản hồi vật lý (ví dụ):
   - `AI_RotorSpeedRaw` tăng khi baffle mở, giảm ma sát khi baffle đóng;
   - `AI_OilFlowRaw` tăng theo `DO_OilPumpRun` + `AO_OilPumpFreqCmd` (lệch pha ~1–2 s);
   - `AI_OilTempRaw` từ từ tăng theo thời gian chạy, giảm khi bơm dừng;
   - `AI_GenCurrentRaw` tỷ lệ với tải khi `DO_MainContactor = TRUE`;
   - `DI_GenBrake` = NOT `DO_BrakeRelease` (khi không có fault);
   - `DI_GenBrake` có thể "kẹt TRUE" một thời đoạn để diễn tập alarm `ALM_BrakeFail`.
3. Ghi các giá trị vào tag `AI_*Raw` / `DI_*` của PLC.

## 7. Mô phỏng tương tác (web)

Có mô phỏng web tương tác của hệ thống dầu thủy lực (thiết bị trên bản vẽ gốc: bể dầu áp lực, máy nén khí, van补气, van điện từ dừng khẩn cấp, bơm ốc vít, van an toàn, servomotor, van phân phối chính, relay dầu + feed rod, step motor, bánh tay) ở thư mục [`../simulator/`](../simulator/index.html). Governor trong mô phỏng dùng cùng nguyên lý PI như `FC_PI_Baffle` (thang 0–1: Kp≈0,002 /RPM, Ki≈0,0002 /(s·RPM), đã hiệu chỉnh để khởi động không quá tốc).
