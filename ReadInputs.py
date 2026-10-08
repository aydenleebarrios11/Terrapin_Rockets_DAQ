import re

def Inpstr2BoolArr(inpstr):
    #This fucntion converts a string like "11011" into a boolean array
    stringArr = list(inpstr)
    boolArr = [s == "1" for s in stringArr]

    return boolArr

def ParseTimings(filename):
    #reads the input text file and returns a list of (time, state_string) tuples.
    schedule = []
    
    # Initialize with a negative time so the first valid timecode (>= 0) always passes
    previous_time = -1.0 
    
    with open(filename, 'r') as f:
        # Use enumerate to track line numbers for precise error reporting
        for line_num, line in enumerate(f, 1):

            # Strip out comments starting with '#'
            clean_line = line.split('#')[0].strip() 
            if not clean_line:
                continue
            
            # Extract time and valve state using regex or basic string splitting
            # Regex for format: [000.000] 00000
            match = re.match(r'\[([\d.]+)\]\s+([01]+)', clean_line)
            if match:
                time_sec = float(match.group(1))
                
                # --- Chronological Order Check ---
                if time_sec < previous_time:
                    raise ValueError(
                        f"Timing error in '{filename}' on line {line_num}: "
                        f"Time [{time_sec:.3f}] occurs before the previous time [{previous_time:.3f}]. "
                        f"The schedule must be in chronological order."
                    )
                
                # Update the tracker for the next iteration
                previous_time = time_sec 
                
                state_str = match.group(2)
                schedule.append((time_sec, state_str))
                
    return schedule