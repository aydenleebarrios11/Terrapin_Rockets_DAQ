import keyboard
from ValveActuator import ExecuteString
import time

#These limits were set arbitrarily, should be adjusted following a pressure transducer and thermocouple calibration
VoltageLimits = [4.5, 4.5, 4.5, 4.5, 4.5, 4.5]

def ScanForErrors(abort_event, clean_exit_event, dataqueue):
    print("Safety Monitor is running, press q at any time to exit")
    
    while not clean_exit_event.is_set(): # Will run until main stops
        # Blocks until a new 100-sample chunk is ready
        data_chunk = dataqueue.get() 
        
        # Flatten and check the chunk for out-of-bounds voltages
        for row in data_chunk:
            for i, voltage in enumerate(row):
                if voltage > VoltageLimits[i]:
                    print(f"CRITICAL: Over-voltage detected ({voltage}V) on channel {i}. Aborting!")
                    abort_event.set()
                    AbortCaseSelector()
                    return

        if keyboard.is_pressed('q'):
            print("Detected soft abort by pressing key 'q' while program was running")
            abort_event.set() # NEW remove if unecessary
            AbortCaseSelector()
            return

        dataqueue.task_done()

def AbortCaseSelector():
    #The following will occur in the case of an error
    print("Please select 1 or 2:\n")

    abort_procedure = "none"
    while abort_procedure not in ("1", "2"):
        print("1. Standard Abort Sequence \t 2. Manual Control")
        abort_procedure = str(input())
        match abort_procedure:
            case "1":
                StandardAbort()
                return
            case "2":
                ManualOverride()
                return
            case _:
                print("Invalid Selection, please select 1 or 2:")
                print("1. Standard Abort Sequence \t 2. Manual Control")

def sleep_or_keyboard_interrupt(seconds, start_time):
    while(time.perf_counter() < start_time + seconds):
        if keyboard.is_pressed('q'):
            print("Detected key 'q' was pressed. Aborting the abort sequence...")
            ManualOverride()

def StandardAbort():
    #Hard Code the standard abort so we can't possibly lose it:

    print("Standard abort sequence running. Press 'q' at any time to abort the abort sequence and switch to manual controls.")

    print("1. Close Everything for 1 second [00000]")
    ExecuteString("00000")
    sleep_or_keyboard_interrupt(1, time.perf_counter())

    print("2. Open Valve 2 for 30 seconds [01000]")
    ExecuteString("01000")
    sleep_or_keyboard_interrupt(30, time.perf_counter())

    print("3. Close Valve 2 for 1 second [00000]")
    ExecuteString("00000")
    sleep_or_keyboard_interrupt(1, time.perf_counter())

    print("4. Purge (open Valve 5) for 5 seconds [00001]")
    ExecuteString("00001")
    sleep_or_keyboard_interrupt(5, time.perf_counter()) 

    print("5. Open Valve 4 for 30 seconds [00010]")
    ExecuteString("00010")
    sleep_or_keyboard_interrupt(30, time.perf_counter()) 

    print("6. Close Valve 4 for 1 second [00000]")
    ExecuteString("00000")
    sleep_or_keyboard_interrupt(1, time.perf_counter()) 

    print("7. Leave Purge Valve open for 1 minute [00001]")
    ExecuteString("00001")
    sleep_or_keyboard_interrupt(60,  time.perf_counter())   

    print("8. Close Purge Valve so we can approach stand [00000]")
    ExecuteString("00000")

    print("Standard abort sequence finished, all valves are closed")

def ManualOverride():
    print("You now have manual control over the valves. Please input a 5 digit sequence of 0 or 1 to control valves 1-5.")
    print("When you are finished please input 'q' or 'quit' to exit")
    while(True):
        inpstr = input()
        match inpstr:
            case "q" | "quit":
                return

            case _:
                ExecuteString(inpstr)
