# This is the main running file. This should be the only thing you execute during a test.
# The number of function definitions in here should be minimal.
# Last Updated: 8/12/26

import sys
from pathlib import Path
import threading
import time
from queue import Queue

import ReadInputs
import ValveActuator
import VoltageReader
import SafetyMonitor


# The 3 functions below are "wrappers". They wait until the thread for the safety monitor is clear to begin.
def RunActuator(wait_for_safety, wait_for_data, 
                abort_event, clean_exit_event,
                start_time, schedule):
    print("Valve Actuator thread is Ready")

    wait_for_safety.wait() #Wait for safety monitor
    wait_for_data.wait() #Wait for data reader
    
    ValveActuator.ExecuteTimings(schedule, start_time, abort_event, clean_exit_event)

def RunDataReader(wait_for_safety, wait_for_data, 
                  abort_event, clean_exit_event,
                  dataqueue,
                  start_time):
    print("Data Reader thread is Ready")

    wait_for_safety.wait() #Wait for safety monitor
    #wait_for_data.set() is located inside of VoltageReader.ReadData()

    VoltageReader.ReadData(wait_for_data, abort_event, clean_exit_event, dataqueue, start_time)

def RunSafetyMointor(wait_for_safety, 
                     abort_event, clean_exit_event,
                     datatqueue):
    print("Safety Monitor is Ready")

    wait_for_safety.set() #Let other wrappers run

    SafetyMonitor.ScanForErrors(abort_event, clean_exit_event, dataqueue)

if __name__ == "__main__":

    #-----------------------------------------------------------------------
    # 1. Read input file
    #This block of code checks that the input file both exists and is a file
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    
        #Check if it exists AND is a file (not a directory)
        if not file_path.is_file():
            print(f"Error: '{file_path}' does not exist or is not a file.")
            sys.exit(1)
    else:
        print("Error: No file path argument provided.")
        sys.exit(1)

    print(f"Found {file_path}. Parsing Schedule...")

    #schedule is a list of (time, valvestate_string) tuples
    schedule = ReadInputs.ParseTimings(file_path)
    print("Done.")
    PrintSchedule = True
    if PrintSchedule:
        print("Raw tuple list for valve timings:")
        print(schedule)
        print("\n---Now setting up threads---")

    #----------------------------------------------------------------------------
    # 2. Set up 3 threads in this order Safety Monitor -> Voltage Reading -> Valve Actuating
    
    wait_for_SafetyMonitor = threading.Event()
    wait_for_DataReader = threading.Event()

    dataqueue = Queue() #Shared data between the data reader and security monitor

    #Our two exit cases
    abort_event = threading.Event()
    clean_exit_event = threading.Event()

    #Official start time is 1 second after we start initializing the threads
    start_time = time.perf_counter() + 1 

    # 3. Start all threads
    monitor_thread = threading.Thread(target=RunSafetyMointor, 
                                      args=(wait_for_SafetyMonitor, 
                                            abort_event, clean_exit_event,
                                            dataqueue))
    
    data_thread = threading.Thread(target=RunDataReader, 
                                   args=(wait_for_SafetyMonitor, wait_for_DataReader,
                                         abort_event, clean_exit_event,
                                         dataqueue,
                                         start_time),
                                    daemon=True #Daemons will run until main stops
                                    )
    
    actuator_thread = threading.Thread(target=RunActuator, 
                                       args=(wait_for_SafetyMonitor, wait_for_DataReader,
                                             abort_event, clean_exit_event,
                                             start_time, schedule),
                                       )

    monitor_thread.start()
    data_thread.start()
    actuator_thread.start()

    monitor_thread.join()
    actuator_thread.join()
    
    if(clean_exit_event.is_set()):
        print("Successfully completed schedule, now exiting...")
    else:
        print("Abort sequence has ended. Terminating program...")
    

