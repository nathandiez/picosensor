def parse_time_to_ms(time_value):
    """
    Parse a time value to milliseconds with the following rules:
    
    - Integer value = milliseconds directly
    - [ms] = milliseconds (single element array)
    - [min, sec, ms] = minutes, seconds, milliseconds (3-element array)
    - [day, hr, min, sec, ms] = days, hours, minutes, seconds, milliseconds (5-element array)
    
    Returns total milliseconds or raises a ValueError for improper formats
    """
    # Handle direct integer case (milliseconds)
    if isinstance(time_value, int):
        return time_value
    
    # Handle array formats
    if isinstance(time_value, list):
        # Validate all elements are integers
        if not all(isinstance(x, int) for x in time_value):
            raise ValueError("All time array elements must be integers")
            
        if len(time_value) == 1:
            # [ms]
            return time_value[0]
        elif len(time_value) == 3:
            # [min, sec, ms]
            minutes, seconds, ms = time_value
            return (minutes * 60 * 1000) + (seconds * 1000) + ms
        elif len(time_value) == 5:
            # [days, hours, minutes, seconds, ms]
            days, hours, minutes, seconds, ms = time_value
            return (days * 24 * 60 * 60 * 1000) + (hours * 60 * 60 * 1000) + \
                   (minutes * 60 * 1000) + (seconds * 1000) + ms
        else:
            raise ValueError(f"Time array must have 1, 3, or 5 elements. Got: {len(time_value)}")
    else:
        raise ValueError(f"Time value must be an integer or a list. Got: {type(time_value).__name__}")