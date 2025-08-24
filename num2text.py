#!/usr/bin/env python3
import sys

def number_to_text(num):
    """Convert number to text format with hundreds, thousands, millions, billions"""
    if num < 0:
        return f"-{number_to_text(-num)}"
    
    if num < 1000:
        return f"{num:,.0f}"
    elif num < 1000000:  # Less than 1 million
        thousands = num / 1000
        return f"{thousands:.2f} thousands"
    elif num < 1000000000:  # Less than 1 billion
        millions = num / 1000000
        return f"{millions:.2f} millions"
    else:  # 1 billion and above
        billions = num / 1000000000
        return f"{billions:.2f} billions"

def main():
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                num = float(line)
                comma_formatted = f"{num:,.0f}"
                converted = number_to_text(num)
                print(f"{line} = {comma_formatted} = {converted}")
            except ValueError:
                print(f"Invalid number: {line}", file=sys.stderr)
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
