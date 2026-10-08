import nidaqmx
import time
from ReadInputs import Inpstr2BoolArr

#Define Channel Names (Should be Global)
Valve_Channels = "Dev1/port0/line0:4" #5 channels total

def ValveActuate(TFArr):
    #----------------------------------------------------
    #Inputs: 
    #       Boolean Array of length 5 (i.e. [0,0,1,0,1])
    #Outputs:
    #       Activates Valves 0 - 4 accordingly
    #----------------------------------------------------

    try:
        with nidaqmx.Task() as task:
            # Add all lines in port0 (lines 0 through 4) to the task at once
            task.do_channels.add_do_chan(Valve_Channels)
            # Write the entire boolean array simultaneously
            task.write(TFArr)
            print(f"Valves actuated to {TFArr}")
            
    except nidaqmx.errors.DaqError as e:
        print(f"Error: {e}")

def ExecuteString(inpstr):
    #To make things ever so slightly more readable
    ValveActuate(Inpstr2BoolArr(inpstr)) #Make sure this is always a set of 5 boolean values

def ExecuteTimings(schedule, start_time, abort_event, clean_exit_event):
    #----------------------------------------------------
    #Inputs: 
    #       schedule - List of tuples that are (timecode, valvestate)
    #       start_time - Global time set by main
    #Outputs:
    #       Activates Valves 0 - 4 with timing
    #----------------------------------------------------

    #Start off by setting all valves to closed
    ExecuteString("00000")
    
    for target_time, state_str in schedule:
        # Wait until the elapsed time matches the target time
        while (time.perf_counter() - start_time) < target_time:
            time.sleep(0.001)  # Sleep briefly to prevent maxing out the CPU

            #Constantly Check if abort has been called
            if (abort_event.is_set()):
                return #Abort is called
            
        # Convert string to boolean array and actuate
        boolArr = Inpstr2BoolArr(state_str)
        print(f"\n[Time: {target_time:.3f}s] Actuating valves to: {state_str}")
        ValveActuate(boolArr)

    #Let other threads know we sucessfully finished execution
    clean_exit_event.set()

#If you need to do just 1 valve activation you can call ValveActuator.py from terminal
if __name__ == "__main__":
    boolArr = Inpstr2BoolArr(input())

    ValveActuate(boolArr)