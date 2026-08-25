// ============================================================
// OB1_Main
// Main program: calls the functions in the right order and
// runs the plant state machine.
//
//   PlantState: 0 = STOP | 1 = STARTING | 2 = RUNNING
//               3 = STOPPING | 4 = TRIP
//
// NOTE: all timers use a fixed 100 ms program cycle (dt = 0.1 s).
//       If you change the cycle time, change the 0.1 values.
// ============================================================

// ---------- 1) analog input processing ----------
FC_AI_Process();

// ---------- 2) alarms + trip ----------
FC_Alarms();

// ---------- 3) governor (AUTO baffle command) ----------
FC_PI_Baffle();

// ---------- 4) HMI command edges + state time ----------
"DB_HydroPlant"."StateTime" := "DB_HydroPlant"."StateTime" + 0.1;
"DB_HydroPlant"."CMD_StartEdge" := "DB_HydroPlant"."CMD_Start" AND NOT "DB_HydroPlant"."PrevStart";
"DB_HydroPlant"."CMD_StopEdge"  := "DB_HydroPlant"."CMD_Stop"  AND NOT "DB_HydroPlant"."PrevStop";
"DB_HydroPlant"."PrevStart" := "DB_HydroPlant"."CMD_Start";
"DB_HydroPlant"."PrevStop"  := "DB_HydroPlant"."CMD_Stop";

// default auto targets (the state machine overwrites them)
"DB_HydroPlant"."DO_OilPumpRun_Auto"    := FALSE;
"DB_HydroPlant"."DO_BrakeRelease_Auto"  := FALSE;
"DB_HydroPlant"."DO_MainContactor_Auto" := FALSE;
"DB_HydroPlant"."AO_OilPumpFreq_Auto"   := 0.0;
"DB_HydroPlant"."AO_Voltage_Auto"       := 0.0;

// ---------- 5) plant state machine ----------
CASE "DB_HydroPlant"."PlantState" OF

0:  // ================= STOP =================
    // start only when nothing is alarming
    IF "DB_HydroPlant"."CMD_StartEdge"
       AND NOT "DB_HydroPlant"."Trip"
       AND NOT "DB_HydroPlant"."ALM_Any"
    THEN
        "DB_HydroPlant"."PlantState" := 1;
        "DB_HydroPlant"."StateTime"  := 0.0;
    END_IF;

1:  // ================= STARTING =================
    // oil pump on at 50 Hz
    "DB_HydroPlant"."DO_OilPumpRun_Auto"  := TRUE;
    "DB_HydroPlant"."AO_OilPumpFreq_Auto" := 50.0;

    // release the brake when the oil flow is OK (after 5 s)
    IF "DB_HydroPlant"."StateTime" > 5.0
       AND "DB_HydroPlant"."OilFlow" > 15.0
       AND "DB_HydroPlant"."AI_Good"
    THEN
        "DB_HydroPlant"."DO_BrakeRelease_Auto" := TRUE;
    END_IF;

    // once the brake really released: open baffle to 15 %
    IF "DB_HydroPlant"."StateTime" > 10.0 AND NOT "DB_HydroPlant"."DI_GenBrake" THEN
        "DB_HydroPlant"."PI_Output" := MAX(IN1 := 15.0, IN2 := "DB_HydroPlant"."PI_Output");
    END_IF;

    // at 90 % of speed: take the load setpoint (ready for grid)
    IF "DB_HydroPlant"."RotorSpeed" >= 0.9 * "DB_HydroPlant"."SP_RotorSpeed" THEN
        "DB_HydroPlant"."PI_Output" := "DB_HydroPlant"."SP_Baffle_Load";
    END_IF;

    // at 98 % of speed, stable 20 s, interlock closed -> connect to grid
    IF "DB_HydroPlant"."RotorSpeed" >= 0.98 * "DB_HydroPlant"."SP_RotorSpeed"
       AND "DB_HydroPlant"."StateTime" > 20.0
       AND "DB_HydroPlant"."DI_GridInterlock"
    THEN
        "DB_HydroPlant"."PlantState" := 2;
        "DB_HydroPlant"."StateTime"  := 0.0;
        "DB_HydroPlant"."DO_MainContactor_Auto" := TRUE;
        // bumpless handover to the governor
        "DB_HydroPlant"."PI_Integral" := "DB_HydroPlant"."PI_Output";
    END_IF;

2:  // ================= RUNNING =================
    "DB_HydroPlant"."DO_OilPumpRun_Auto"  := TRUE;
    "DB_HydroPlant"."AO_OilPumpFreq_Auto" := 50.0;
    "DB_HydroPlant"."DO_BrakeRelease_Auto" := TRUE;
    "DB_HydroPlant"."DO_MainContactor_Auto" := "DB_HydroPlant"."DI_GridInterlock";

    // excitation up when the rotor is at speed
    IF "DB_HydroPlant"."RotorSpeed" >= 0.9 * "DB_HydroPlant"."SP_RotorSpeed" THEN
        "DB_HydroPlant"."AO_Voltage_Auto" := 100.0;
    END_IF;

    IF "DB_HydroPlant"."CMD_StopEdge" THEN
        "DB_HydroPlant"."PlantState" := 3;
        "DB_HydroPlant"."StateTime"  := 0.0;
    END_IF;

3:  // ================= STOPPING =================
    "DB_HydroPlant"."PI_Output"           := 0.0;   // close baffle
    "DB_HydroPlant"."DO_OilPumpRun_Auto"  := TRUE;  // keep pump running (cooling)
    "DB_HydroPlant"."AO_OilPumpFreq_Auto" := 50.0;

    // apply the brake when the rotor is slow enough
    IF "DB_HydroPlant"."RotorSpeed" < 15.0 THEN
        "DB_HydroPlant"."DO_BrakeRelease_Auto" := FALSE;
    END_IF;

    // once stopped & brake confirmed: pump cools 30 s, then off
    IF "DB_HydroPlant"."DI_GenBrake" AND "DB_HydroPlant"."RotorSpeed" < 15.0 THEN
        "DB_HydroPlant"."CoolDownTimer" := "DB_HydroPlant"."CoolDownTimer" + 0.1;
        IF "DB_HydroPlant"."CoolDownTimer" > 999.0 THEN
            "DB_HydroPlant"."CoolDownTimer" := 999.0;
        END_IF;
    ELSE
        "DB_HydroPlant"."CoolDownTimer" := 0.0;
    END_IF;

    IF "DB_HydroPlant"."CoolDownTimer" >= 30.0 THEN
        "DB_HydroPlant"."PlantState"    := 0;
        "DB_HydroPlant"."StateTime"     := 0.0;
        "DB_HydroPlant"."CoolDownTimer" := 0.0;
    END_IF;

4:  // ================= TRIP =================
    "DB_HydroPlant"."PI_Output"           := 0.0;   // close baffle immediately
    "DB_HydroPlant"."DO_MainContactor_Auto" := FALSE;
    "DB_HydroPlant"."DO_OilPumpRun_Auto"  := TRUE;  // keep pump running (cooling)
    "DB_HydroPlant"."AO_OilPumpFreq_Auto" := 50.0;

    // apply the brake below 50 % of nominal speed
    IF "DB_HydroPlant"."RotorSpeed" < 0.5 * "DB_HydroPlant"."SP_RotorSpeed" THEN
        "DB_HydroPlant"."DO_BrakeRelease_Auto" := FALSE;
    END_IF;

    // after the stop: pump cools 30 s, then off
    IF "DB_HydroPlant"."DI_GenBrake" AND "DB_HydroPlant"."RotorSpeed" < 15.0 THEN
        "DB_HydroPlant"."CoolDownTimer" := "DB_HydroPlant"."CoolDownTimer" + 0.1;
        IF "DB_HydroPlant"."CoolDownTimer" > 999.0 THEN
            "DB_HydroPlant"."CoolDownTimer" := 999.0;
        END_IF;
        IF "DB_HydroPlant"."CoolDownTimer" >= 30.0 THEN
            "DB_HydroPlant"."DO_OilPumpRun_Auto"  := FALSE;
            "DB_HydroPlant"."AO_OilPumpFreq_Auto" := 0.0;
        END_IF;
    ELSE
        "DB_HydroPlant"."CoolDownTimer" := 0.0;
    END_IF;

    // when everything is cleared and the rotor stopped: back to STOP
    IF "DB_HydroPlant"."CMD_TripReset"
       AND NOT "DB_HydroPlant"."Trip"
       AND NOT "DB_HydroPlant"."ALM_Any"
       AND "DB_HydroPlant"."RotorSpeed" < 5.0
    THEN
        "DB_HydroPlant"."PlantState"    := 0;
        "DB_HydroPlant"."StateTime"     := 0.0;
        "DB_HydroPlant"."CoolDownTimer" := 0.0;
    END_IF;

END_CASE;

// ---------- 6) final analog outputs (HOA + safety) ----------
FC_AO_Control();

// ---------- 7) final digital outputs (HOA + interlocks) ----------
FC_DI_Control();
