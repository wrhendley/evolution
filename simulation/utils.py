def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def sign(n):
    return (n > 0) - (n < 0)