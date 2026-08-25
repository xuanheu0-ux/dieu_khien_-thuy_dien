// ============================================================
// FC_DI_Control
// Final Digital Outputs
// - Hand-Off-Auto: manual pump start/stop when in HAND
// - safety interlocks: the brake and the main contactor can
//   NEVER be forced while the E-Stop is latched or a trip
//   is active (safety overrides HAND mode)
// ============================================================

// ---- Oil pump run ----
IF "DB_HydroPlant"."Trip" OR "DB_HydroPlant"."DO_EStopLatched" THEN
    "DB_HydroPlant"."DO_OilPumpRun" := "DB_HydroPlant"."DO_OilPumpRun_Auto";
ELSIF "DB_HydroPlant"."HOA_PumpSwitch_Hand" THEN
    "DB_HydroPlant"."DO_OilPumpRun" := "DB_HydroPlant"."CMD_OilPumpHand";
ELSE
    "DB_HydroPlant"."DO_OilPumpRun" := "DB_HydroPlant"."DO_OilPumpRun_Auto";
END_IF;

// ---- Generator brake (TRUE = release, FALSE = applied) ----
IF "DB_HydroPlant"."Trip" OR "DB_HydroPlant"."DO_EStopLatched" THEN
    "DB_HydroPlant"."DO_BrakeRelease" := FALSE;
ELSE
    "DB_HydroPlant"."DO_BrakeRelease" := "DB_HydroPlant"."DO_BrakeRelease_Auto";
END_IF;

// ---- Main contactor (grid connection) ----
IF "DB_HydroPlant"."Trip" OR "DB_HydroPlant"."DO_EStopLatched" OR NOT "DB_HydroPlant"."DI_GridInterlock" THEN
    "DB_HydroPlant"."DO_MainContactor" := FALSE;
ELSE
    "DB_HydroPlant"."DO_MainContactor" := "DB_HydroPlant"."DO_MainContactor_Auto";
END_IF;

// ---- Status / alarm outputs ----
"DB_HydroPlant"."DO_AlarmLamp" := "DB_HydroPlant"."ALM_Any" OR "DB_HydroPlant"."Trip";
"DB_HydroPlant"."DO_Running"   := ( "DB_HydroPlant"."PlantState" = 2 ) AND "DB_HydroPlant"."DO_MainContactor";
