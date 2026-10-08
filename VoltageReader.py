import nidaqmx
from nidaqmx.constants import AcquisitionType
import csv
import os
import time

#Define Channel Names (Should be Global)
Analog_Channels = "Dev1/ai0:5" #6 Channels total

def ReadData(wait_for_data, abort_event, clean_exit_event, dataqueue, start_time):
    # Continuously acquires data at a precise hardware-timed rate and pushes data chunks into the queue.
    
    os.makedirs("logs", exist_ok=True)
    
    normal_file = "logs/data.csv"
    abort_file = "logs/aborted_data.csv"
    
    try:
        with nidaqmx.Task() as task:
            sample_rate = 1000.0
            samples_per_chunk = 100

            task.ai_channels.add_ai_voltage_chan("Dev1/ai0:5")
            # Configure continuous hardware timing at 1000 Hz
            task.timing.cfg_samp_clk_timing(
                rate=sample_rate, 
                sample_mode=AcquisitionType.CONTINUOUS
            )
            wait_for_data.set() #Let RunActuator Run

            # Run until the main schedule finishes successfully
            while not clean_exit_event.is_set():
                # Read a 100-sample chunk
                start_read_time = time.perf_counter() - start_time
                data = task.read(number_of_samples_per_channel=samples_per_chunk)
                
                # Transpose the data
                transposed_data = list(zip(*data))
                
                rows = []
                for i, channel_values in enumerate(transposed_data):
                    # Hack to calculate sample time (is just initial read time + 1/sampletime)
                    timestamp = start_read_time + i/sample_rate
                    
                    # Create a new tuple with the timestamp at the beginning (index 0)
                    row_with_time = (timestamp,) + channel_values
                    rows.append(row_with_time)
                
                
                # data_queue should have infinite memory but we will check for full just in case
                if not dataqueue.full():
                    dataqueue.put(transposed_data)
                    
                # Dynamically choose destination
                current_file = abort_file if abort_event.is_set() else normal_file
                
                # Append to CSV
                with open(current_file, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)

    except nidaqmx.errors.DaqError as e:
        print(f"DAQ Error in VoltageReader: {e}")