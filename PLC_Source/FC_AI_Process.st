// ============================================================
// FC_AI_Process
// Analog Input processing
// - clamps raw analog inputs to their physical ranges
// - flags AI_Good when all signals are inside the expected
//   measurement range (sensor failure detection, crude)
// Called FIRST in OB1, every scan.
// ============================================================

// scale / clamp to physical ranges
"DB_HydroPlant"."BafflePos"   := LIMIT(IN := "DB_HydroPlant"."AI_BaffleRaw",      LO := 0.0,   HI := 100.0);
"DB_HydroPlant"."OilPumpFreq" := LIMIT(IN := "DB_HydroPlant"."AI_OilPumpFreqRaw", LO := 0.0,   HI := 50.0);
"DB_HydroPlant"."RotorSpeed"  := LIMIT(IN := "DB_HydroPlant"."AI_RotorSpeedRaw",  LO := 0.0,   HI := 400.0);
"DB_HydroPlant"."OilTemp"     := LIMIT(IN := "DB_HydroPlant"."AI_OilTempRaw",     LO := -40.0, HI := 150.0);
"DB_HydroPlant"."OilFlow"     := LIMIT(IN := "DB_HydroPlant"."AI_OilFlowRaw",     LO := 0.0,   HI := 150.0);
"DB_HydroPlant"."GenCurrent"  := LIMIT(IN := "DB_HydroPlant"."AI_GenCurrentRaw",  LO := 0.0,   HI := 300.0);

// validity check: all raw signals inside their expected measurement range
"DB_HydroPlant"."AI_Good" := (  "DB_HydroPlant"."AI_BaffleRaw"      >= -5.0
                            AND "DB_HydroPlant"."AI_BaffleRaw"      <= 105.0
                            AND "DB_HydroPlant"."AI_OilPumpFreqRaw" >= -2.0
                            AND "DB_HydroPlant"."AI_OilPumpFreqRaw" <= 55.0
                            AND "DB_HydroPlant"."AI_RotorSpeedRaw"  >= -10.0
                            AND "DB_HydroPlant"."AI_RotorSpeedRaw"  <= 450.0
                            AND "DB_HydroPlant"."AI_OilTempRaw"     >= -50.0
                            AND "DB_HydroPlant"."AI_OilTempRaw"     <= 160.0
                            AND "DB_HydroPlant"."AI_OilFlowRaw"     >= -10.0
                            AND "DB_HydroPlant"."AI_OilFlowRaw"     <= 160.0
                            AND "DB_HydroPlant"."AI_GenCurrentRaw"  >= -10.0
                            AND "DB_HydroPlant"."AI_GenCurrentRaw"  <= 320.0
                            );
