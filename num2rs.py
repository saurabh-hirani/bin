#!/usr/bin/env python3
import sys

def indian_comma_format(num):
    """Format number with Indian comma system (lakhs, crores)"""
    num_str = str(int(num))
    if len(num_str) <= 3:
        return num_str
    
    # For Indian system: last 3 digits, then groups of 2
    result = num_str[-3:]  # Last 3 digits
    remaining = num_str[:-3]
    
    while remaining:
        if len(remaining) <= 2:
            result = remaining + "," + result
            break
        else:
            result = remaining[-2:] + "," + result
            remaining = remaining[:-2]
    
    return result

def number_to_rupees(num):
    """Convert number to Indian rupee format with lakhs and crores"""
    if num < 0:
        return f"-{number_to_rupees(-num)}"
    
    if num < 1000:
        return f"{num:,.0f}"
    elif num < 100000:  # Less than 1 lakh
        return f"{num:,.0f}"
    elif num < 10000000:  # Less than 1 crore
        lakhs = num / 100000
        return f"{lakhs:.2f} lakhs"
    else:  # 1 crore and above
        crores = num / 10000000
        return f"{crores:.2f} crores"

def main():
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                num = float(line)
                indian_formatted = indian_comma_format(num)
                converted = number_to_rupees(num)
                print(f"{line} = {indian_formatted} = {converted}")
            except ValueError:
                print(f"Invalid number: {line}", file=sys.stderr)
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
