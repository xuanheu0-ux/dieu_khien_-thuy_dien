// ============================================================
// FC_PI_Baffle
// Governor: PI controller on rotor speed.
// Output = baffle (turbine gate) position [0..100 %].
//
// Runs only in AUTO mode while the plant is RUNNING and the
// speed signal is valid. Controller state (integral, previous
// error) is kept in DB_HydroPlant so the HMI can monitor it.
//
// Assumes a fixed 100 ms program cycle (dt = 0.1 s).
// If you change the cycle time, change the 0.1 accordingly.
// ============================================================

IF "DB_HydroPlant"."PlantState" = 2
   AND NOT "DB_HydroPlant"."HOA_Baffle_Hand"
   AND "DB_HydroPlant"."AI_Good"
THEN
    // proportional term
    "DB_HydroPlant"."PI_PrevError" := "DB_HydroPlant"."SP_RotorSpeed" - "DB_HydroPlant"."RotorSpeed";

    // conditional integration (anti-windup):
    // integrate only while the output is not saturated against the error sign
    IF ( "DB_HydroPlant"."PI_Output" < 100.0 OR "DB_HydroPlant"."PI_PrevError" < 0.0 )
       AND ( "DB_HydroPlant"."PI_Output" > 0.0   OR "DB_HydroPlant"."PI_PrevError" > 0.0 )
    THEN
        "DB_HydroPlant"."PI_Integral" := "DB_HydroPlant"."PI_Integral"
                                        + "DB_HydroPlant"."PI_Ki" * "DB_HydroPlant"."PI_PrevError" * 0.1;
    END_IF;

    "DB_HydroPlant"."PI_Output" := "DB_HydroPlant"."PI_Kp" * "DB_HydroPlant"."PI_PrevError"
                                  + "DB_HydroPlant"."PI_Integral";
    "DB_HydroPlant"."PI_Output" := LIMIT(IN := "DB_HydroPlant"."PI_Output", LO := 0.0, HI := 100.0);

ELSE
    // not governing: freeze the error term, keep the last output
    // (the state machine in OB1 may overwrite PI_Output directly)
    "DB_HydroPlant"."PI_PrevError" := 0.0;
END_IF;
