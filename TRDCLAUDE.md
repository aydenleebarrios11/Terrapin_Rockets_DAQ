# Terrapin Rocketry Liquids DAQ

Python test stand software for the Terrapin Rocketry Team Liquids Subteam. It reads sensors through an NI DAQ (`nidaqmx`) and commands valves for nitrous oxide fill, fuel pressurization, launch, and abort.

## Current work

We are refactoring from a time based valve sequencer to a state based system with automatic abort. **Read `docs/REFACTOR_PLAN.md` before making changes.** It contains the requirements, the review of the existing code, open hardware questions, the target architecture, and the phased plan. Update it as decisions are made or open questions are answered.

## Running today

`python main.py Test0.txt` (needs `nidaqmx` and `keyboard`). `Test0.txt` is a timed schedule of `[seconds] valvebits` lines.

## Working rules

* This is safety critical code that controls nitrous oxide. Prefer simple, explicit logic over clever code.
* Never change the abort sequence or valve channel mapping without the change being reflected in `docs/REFACTOR_PLAN.md` and called out in the PR description.
* All new logic must be testable without NI hardware by going through the hardware interface and the simulator.
* Do not invent channel numbers, calibration values, or pressure limits. If a value is unknown, leave it in config marked TODO and list it under open questions in the plan.
* Work on a branch and open a pull request. Reviewers are Kieran Ung and Milo Messinger.
