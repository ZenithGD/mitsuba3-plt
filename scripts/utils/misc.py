import os

def get_filename(full_path):
    return os.path.basename(full_path)

def format_time(time_ns):
    """Given time in nanoseconds return formatted time with 3 decimal places

    Args:
        time_ns (float): The time in nanoseconds

    Returns:
        str: the formatted time as a string with the correct units
    """
    magnitude_steps = [
        ("ns", 1e3),
        ("us", 1e3),
        ("ms", 1e3),
        ("s", 60),
        ("m", 60),
        ("h", 24),
        ("d", None)  # No further step after days
    ]

    value = time_ns
    for unit, step in magnitude_steps:
        if step is None or value < step:
            return f"{value} {unit}"
        else:
            value /= step
    
    return f"{value:.3f} {unit}"