// ============================================================
// FC_AO_Control
// Final Analog Outputs
// - Hand-Off-Auto: selects AUTO or HAND source per device
// - safety override: on Trip / E-Stop the safety action
//   ALWAYS wins, even in HAND mode
// - clamps to output range
// ============================================================

// ---- Baffle (turbine gate) [0..100 %] ----
IF "DB_HydroPlant"."Trip" OR "DB_HydroPlant"."DO_EStopLatched" THEN
    "DB_HydroPlant"."AO_BaffleCmd" := 0.0;
ELSIF "DB_HydroPlant"."HOA_Baffle_Hand" THEN
    "DB_HydroPlant"."AO_BaffleCmd" := LIMIT(IN := "DB_HydroPlant"."SP_Baffle_Hand", LO := 0.0, HI := 100.0);
ELSE
    "DB_HydroPlant"."AO_BaffleCmd" := LIMIT(IN := "DB_HydroPlant"."PI_Output", LO := 0.0, HI := 100.0);
END_IF;

// ---- Oil pump VFD frequency [0..50 Hz] ----
IF "DB_HydroPlant"."Trip" OR "DB_HydroPlant"."DO_EStopLatched" THEN
    // on trip the pump follows the AUTO target (cooling), never HAND
    "DB_HydroPlant"."AO_OilPumpFreqCmd" := LIMIT(IN := "DB_HydroPlant"."AO_OilPumpFreq_Auto", LO := 0.0, HI := 50.0);
ELSIF "DB_HydroPlant"."HOA_OilPump_Hand" THEN
    "DB_HydroPlant"."AO_OilPumpFreqCmd" := LIMIT(IN := "DB_HydroPlant"."SP_OilPump_Hand", LO := 0.0, HI := 50.0);
ELSE
    "DB_HydroPlant"."AO_OilPumpFreqCmd" := LIMIT(IN := "DB_HydroPlant"."AO_OilPumpFreq_Auto", LO := 0.0, HI := 50.0);
END_IF;

// ---- Generator voltage / excitation [0..100 %] ----
IF "DB_HydroPlant"."Trip" OR "DB_HydroPlant"."DO_EStopLatched" THEN
    "DB_HydroPlant"."AO_GenVoltage" := 0.0;
ELSIF "DB_HydroPlant"."HOA_Voltage_Hand" THEN
    "DB_HydroPlant"."AO_GenVoltage" := LIMIT(IN := "DB_HydroPlant"."SP_Voltage_Hand", LO := 0.0, HI := 100.0);
ELSE
    "DB_HydroPlant"."AO_GenVoltage" := LIMIT(IN := "DB_HydroPlant"."AO_Voltage_Auto", LO := 0.0, HI := 100.0);
END_IF;
