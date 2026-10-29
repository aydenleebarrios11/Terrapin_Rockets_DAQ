# DAQ Refactor Plan

Source of requirements is the Liquids Subteam "DAQ Code Change Write‑Up". This file captures the review of the existing code and the agreed plan for converting it from a timed sequencer to a state based system.

## Goal

Replace the step by step, time based valve sequencer with a state machine that continuously monitors sensors and the DAQ, detects faults, and automatically aborts by commanding valves to a safe state in the correct order.

## Required states

| State | Meaning |
|---|---|
| INIT | Software starting |
| SAFE | Nominal conditions, nothing pressurized by the software |
| PRECHECK | Verify sensors and hardware are working |
| ARMED | Prechecks passed, ready to test |
| RUN | Test operation in progress |
| ABORT | Problem detected, abort sequence running |
| FAULT | Stopped after an abort, stays here until manually reset |
| COMPLETE | Test finished |

Rules
* Faults move the system to ABORT automatically. No operator prompt is required for the abort to start.
* ABORT ends in FAULT. Only a manual operator reset leaves FAULT.
* The system never returns to RUN on its own.

## Valve sequences from the write‑up

Fill (nitrous oxide)
1. Preliminary. SV‑1 open, SV‑2 open, GV‑1 close
2. Start fill. GV‑2 open
3. Fill complete. SV‑2 close, GV‑2 close, SV‑1 close

Abort (drain rocket and fill plumbing of nitrous, vent fuel tank)
1. Vent fuel tank. SV‑3 close, SV‑4 open
2. Dump oxidizer. SV‑2 close, GV‑2 close, GV‑1 open, SV‑1 open (this step actually dumps ox)

Launch
1. Pressurize fuel. SV‑4 close (should already be closed), SV‑3 open
2. Fire ignitor
3. Open fuel. GV‑3 open
4. Open ox. GV‑5 open

## Problems found in the current code

1. **Abort is not automatic.** `SafetyMonitor.AbortCaseSelector` waits for the operator to type 1 or 2 before doing anything.
2. **Abort sequence does not match the spec.** `SafetyMonitor.StandardAbort` uses an old five valve sequence (valve 2, valve 4, purge valve 5).
3. **DAQ comms loss never aborts.** On `DaqError`, `VoltageReader.ReadData` prints and exits. `SafetyMonitor` then blocks forever on `dataqueue.get()`.
4. **Only over‑voltage is checked.** No low limits, no disconnected or frozen sensor checks. `VoltageLimits` are placeholder 4.5 V values.
5. **Two threads can command valves at once.** `ValveActuator.ExecuteTimings` only checks `abort_event` while waiting, so it can fire one more schedule step after an abort begins. Every command opens a new `nidaqmx.Task`.
6. **Valve write errors are swallowed.** `ValveActuate` only prints on `DaqError`.
7. **No valve failure detection.** Nothing confirms a valve actually moved.
8. **`q` during abort misbehaves.** `sleep_or_keyboard_interrupt` calls `ManualOverride`, then the abort sequence resumes afterward. It also busy waits.
9. **Only 5 DO lines.** `Valve_Channels = "Dev1/port0/line0:4"`, but the spec names SV‑1 to SV‑4, GV‑1, GV‑2, GV‑3, GV‑5 and an ignitor.
10. **Raw volts only.** The spec wants pressures shown in the terminal.
11. **Thin logging.** CSV has no header, no state, no valve commands, no faults, approximated timestamps, and reopens the file every chunk.
12. **Untestable without hardware.** `nidaqmx` is imported directly in every module.
13. Minor. `RunSafetyMointor` parameter `datatqueue` is a typo and the function reads the global `dataqueue` by accident.

## Open questions (blockers for the safety logic)

1. Channel map. Which DO line drives each valve (is there a GV‑4) and the ignitor? Which AI channel is each pressure transducer and thermocouple?
2. Is each valve normally open or normally closed?
3. Calibration from volts to psi and volts to temperature for each sensor.
4. Allowed ranges for each sensor in each state (SAFE, fill, ARMED, RUN).
5. Abort timing. How long between steps, and time based or wait for a pressure to drop?
6. Abort by state. During RUN, do GV‑3 and GV‑5 close first and the ignitor go off?
7. What signals fill complete? Pressure, scale, or operator?
8. Do valves have position feedback, or is health inferred from pressure response?

Record answers in the config file and update this section as they come in.

## Target architecture

* **config** holds the channel map, valve names and normal positions, calibration, limits per state, and abort timing. No logic changes needed when lab values change.
* **hardware interface** with two implementations. `NIDaq` wraps `nidaqmx`. `SimDaq` lets tests script pressures and inject failures (stuck sensor, comms loss, valve failure).
* **ValveController** is the single owner of the DO task. Serializes commands, tracks commanded state, raises faults on write errors.
* **FaultManager** turns checks into named faults with severity (warning, abort, latch to FAULT).
* **Monitors** check range, disconnected sensor, frozen sensor, stale data watchdog, DAQ read errors, valve response.
* **StateMachine** single control loop with an explicit transition table and operator commands.
* **Sequences as data.** Each step waits on time, a sensor condition, or operator confirmation, with a timeout that raises a fault.
* **Logging.** Sensor CSV with header and engineering units, plus an event log for state changes, valve commands, faults, and fill status.
* **Terminal display.** Live table of state, pressures, valve positions, active faults.

## Plan

Phase 1. Foundation (no hardware needed)
1. Fill in the open questions and create the config file.
2. Build the hardware interface and `SimDaq`.
3. Build `ValveController` and `FaultManager`.

Phase 2. State machine and sequences
1. States, transitions, operator commands.
2. Encode fill, pressurize, launch, abort.
3. Automatic abort. Manual override only after abort completes.

Phase 3. Monitoring, logging, display
1. Sensor checks and DAQ watchdog.
2. CSV and event log.
3. Live terminal display.

Phase 4. Testing
1. pytest against `SimDaq` for every spec case. Normal operation, sensor failure, pressure fault, DAQ failure, comms loss, valve failure, abort, reset after abort.
2. NI MAX simulated device on the lab computer to exercise the real `nidaqmx` path.
3. Dry run on the stand with no propellant.
4. Abort and flush test in Cadou's lab.

Phase 5. Documentation
README covering each state, fault detection, abort behavior, valve control, how to run, how to test.

## Safety note

Software abort is not the only safeguard. The stand should also have a hardware E‑stop, relief valves, and vent valves that fail safe on power loss.
