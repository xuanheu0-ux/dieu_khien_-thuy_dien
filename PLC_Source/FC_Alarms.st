// ============================================================
// FC_Alarms
// 7 alarm conditions + latched plant trip
//
//   1. Overcurrent      ALM_OverCurrent  -> alarm + trip   (2 s debounce)
//   2. High oil temp    ALM_HighOilTemp  -> alarm          (2 s debounce)
//                        OilTemp > LIM_TempTrip            -> trip
//   3. Rotor overspeed  ALM_Overspeed    -> alarm + trip   (0.2 s debounce)
//   4. Oil low flow     ALM_OilLowFlow   -> alarm          (5 s debounce)
//                        OilFlow < LIM_FlowTrip for 5 s    -> trip
//   5. Oil high flow    ALM_OilHighFlow  -> alarm          (5 s debounce)
//   6. E-Stop           ALM_EStop        -> immediate + trip (latched)
//   7. Brake failure    ALM_BrakeFail    -> alarm          (10 s debounce)
//
// Debounce timers are manual counters [s].
// They assume a fixed 100 ms program cycle (step 0.1 s).
// ============================================================

// --- 1. Overcurrent ---
IF "DB_HydroPlant"."GenCurrent" > "DB_HydroPlant"."LIM_CurrentOver" THEN
    "DB_HydroPlant"."T_OverCurrent" := "DB_HydroPlant"."T_OverCurrent" + 0.1;
    IF "DB_HydroPlant"."T_OverCurrent" > 999.0 THEN
        "DB_HydroPlant"."T_OverCurrent" := 999.0;
    END_IF;
ELSE
    "DB_HydroPlant"."T_OverCurrent" := 0.0;
END_IF;
IF "DB_HydroPlant"."T_OverCurrent" >= 2.0 THEN
    "DB_HydroPlant"."ALM_OverCurrent" := TRUE;
END_IF;
IF "DB_HydroPlant"."CMD_AlarmReset" AND "DB_HydroPlant"."T_OverCurrent" = 0.0 THEN
    "DB_HydroPlant"."ALM_OverCurrent" := FALSE;
END_IF;

// --- 2. High oil temperature ---
IF "DB_HydroPlant"."OilTemp" > "DB_HydroPlant"."LIM_TempHi" THEN
    "DB_HydroPlant"."T_HighOilTemp" := "DB_HydroPlant"."T_HighOilTemp" + 0.1;
    IF "DB_HydroPlant"."T_HighOilTemp" > 999.0 THEN
        "DB_HydroPlant"."T_HighOilTemp" := 999.0;
    END_IF;
ELSE
    "DB_HydroPlant"."T_HighOilTemp" := 0.0;
END_IF;
IF "DB_HydroPlant"."T_HighOilTemp" >= 2.0 THEN
    "DB_HydroPlant"."ALM_HighOilTemp" := TRUE;
END_IF;
IF "DB_HydroPlant"."CMD_AlarmReset" AND "DB_HydroPlant"."T_HighOilTemp" = 0.0 THEN
    "DB_HydroPlant"."ALM_HighOilTemp" := FALSE;
END_IF;

// --- 3. Rotor overspeed ---
IF "DB_HydroPlant"."RotorSpeed" > "DB_HydroPlant"."LIM_SpeedOver" THEN
    "DB_HydroPlant"."T_Overspeed" := "DB_HydroPlant"."T_Overspeed" + 0.1;
    IF "DB_HydroPlant"."T_Overspeed" > 999.0 THEN
        "DB_HydroPlant"."T_Overspeed" := 999.0;
    END_IF;
ELSE
    "DB_HydroPlant"."T_Overspeed" := 0.0;
END_IF;
IF "DB_HydroPlant"."T_Overspeed" >= 0.2 THEN
    "DB_HydroPlant"."ALM_Overspeed" := TRUE;
END_IF;
IF "DB_HydroPlant"."CMD_AlarmReset" AND "DB_HydroPlant"."T_Overspeed" = 0.0 THEN
    "DB_HydroPlant"."ALM_Overspeed" := FALSE;
END_IF;

// --- 4. Oil low flow ---
IF "DB_HydroPlant"."OilFlow" < "DB_HydroPlant"."LIM_FlowLo" THEN
    "DB_HydroPlant"."T_OilLowFlow" := "DB_HydroPlant"."T_OilLowFlow" + 0.1;
    IF "DB_HydroPlant"."T_OilLowFlow" > 999.0 THEN
        "DB_HydroPlant"."T_OilLowFlow" := 999.0;
    END_IF;
ELSE
    "DB_HydroPlant"."T_OilLowFlow" := 0.0;
END_IF;
IF "DB_HydroPlant"."T_OilLowFlow" >= 5.0 THEN
    "DB_HydroPlant"."ALM_OilLowFlow" := TRUE;
END_IF;
IF "DB_HydroPlant"."CMD_AlarmReset" AND "DB_HydroPlant"."T_OilLowFlow" = 0.0 THEN
    "DB_HydroPlant"."ALM_OilLowFlow" := FALSE;
END_IF;

// --- 5. Oil high flow ---
IF "DB_HydroPlant"."OilFlow" > "DB_HydroPlant"."LIM_FlowHi" THEN
    "DB_HydroPlant"."T_OilHighFlow" := "DB_HydroPlant"."T_OilHighFlow" + 0.1;
    IF "DB_HydroPlant"."T_OilHighFlow" > 999.0 THEN
        "DB_HydroPlant"."T_OilHighFlow" := 999.0;
    END_IF;
ELSE
    "DB_HydroPlant"."T_OilHighFlow" := 0.0;
END_IF;
IF "DB_HydroPlant"."T_OilHighFlow" >= 5.0 THEN
    "DB_HydroPlant"."ALM_OilHighFlow" := TRUE;
END_IF;
IF "DB_HydroPlant"."CMD_AlarmReset" AND "DB_HydroPlant"."T_OilHighFlow" = 0.0 THEN
    "DB_HydroPlant"."ALM_OilHighFlow" := FALSE;
END_IF;

// --- 6. E-Stop (immediate, latched until confirmed) ---
IF "DB_HydroPlant"."DI_EStop" THEN
    "DB_HydroPlant"."ALM_EStop" := TRUE;
    "DB_HydroPlant"."DO_EStopLatched" := TRUE;
END_IF;
IF NOT "DB_HydroPlant"."DI_EStop" AND "DB_HydroPlant"."CMD_AlarmReset" THEN
    "DB_HydroPlant"."ALM_EStop" := FALSE;
    "DB_HydroPlant"."DO_EStopLatched" := FALSE;
END_IF;

// --- 7. Brake failure (release commanded but brake still applied > 10 s) ---
IF "DB_HydroPlant"."DO_BrakeRelease" AND "DB_HydroPlant"."DI_GenBrake" THEN
    "DB_HydroPlant"."T_BrakeFail" := "DB_HydroPlant"."T_BrakeFail" + 0.1;
    IF "DB_HydroPlant"."T_BrakeFail" > 999.0 THEN
        "DB_HydroPlant"."T_BrakeFail" := 999.0;
    END_IF;
ELSE
    "DB_HydroPlant"."T_BrakeFail" := 0.0;
END_IF;
IF "DB_HydroPlant"."T_BrakeFail" >= 10.0 THEN
    "DB_HydroPlant"."ALM_BrakeFail" := TRUE;
END_IF;
IF "DB_HydroPlant"."CMD_AlarmReset" AND "DB_HydroPlant"."T_BrakeFail" = 0.0 THEN
    "DB_HydroPlant"."ALM_BrakeFail" := FALSE;
END_IF;

// --- general alarm flag ---
"DB_HydroPlant"."ALM_Any" := "DB_HydroPlant"."ALM_OverCurrent"
                         OR "DB_HydroPlant"."ALM_HighOilTemp"
                         OR "DB_HydroPlant"."ALM_Overspeed"
                         OR "DB_HydroPlant"."ALM_OilLowFlow"
                         OR "DB_HydroPlant"."ALM_OilHighFlow"
                         OR "DB_HydroPlant"."ALM_EStop"
                         OR "DB_HydroPlant"."ALM_BrakeFail";

// --- latched plant trip ---
IF "DB_HydroPlant"."ALM_Overspeed"
   OR "DB_HydroPlant"."ALM_OverCurrent"
   OR "DB_HydroPlant"."ALM_EStop"
   OR ( "DB_HydroPlant"."OilTemp" > "DB_HydroPlant"."LIM_TempTrip" )
   OR ( "DB_HydroPlant"."OilFlow" < "DB_HydroPlant"."LIM_FlowTrip" AND "DB_HydroPlant"."T_OilLowFlow" >= 5.0 )
THEN
    "DB_HydroPlant"."Trip" := TRUE;
END_IF;
IF "DB_HydroPlant"."CMD_TripReset" THEN
    "DB_HydroPlant"."Trip" := FALSE;
END_IF;
