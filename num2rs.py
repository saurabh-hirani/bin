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

def number_to_indian_words(num):
    """Convert number to full Indian text representation"""
    if num < 0:
        return f"minus {number_to_indian_words(-num)}"
    
    if num == 0:
        return "zero rupees"
    
    # Define number words
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", 
            "seventeen", "eighteen", "nineteen"]
    
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    
    def convert_hundreds(n):
        result = ""
        if n >= 100:
            result += ones[n // 100] + " hundred"
            n %= 100
            if n > 0:
                result += " and "
        
        if n >= 20:
            result += tens[n // 10]
            if n % 10 > 0:
                result += " " + ones[n % 10]
        elif n > 0:
            result += ones[n]
        
        return result
    
    # Break down the number
    crores = int(num // 10000000)
    num %= 10000000
    lakhs = int(num // 100000)
    num %= 100000
    thousands = int(num // 1000)
    num %= 1000
    hundreds = int(num)
    
    parts = []
    
    if crores > 0:
        if crores == 1:
            parts.append("one crore")
        else:
            parts.append(convert_hundreds(crores) + " crores")
    
    if lakhs > 0:
        if lakhs == 1:
            parts.append("one lakh")
        else:
            parts.append(convert_hundreds(lakhs) + " lakhs")
    
    if thousands > 0:
        if thousands == 1:
            parts.append("one thousand")
        else:
            parts.append(convert_hundreds(thousands) + " thousands")
    
    if hundreds > 0:
        parts.append(convert_hundreds(hundreds))
    
    result = ", ".join(parts)
    if result:
        result += " rupees"
    else:
        result = "zero rupees"
    
    return result.capitalize()

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
                words = number_to_indian_words(num)
                print(f"{line} = {indian_formatted} = {converted} = {words}")
            except ValueError:
                print(f"Invalid number: {line}", file=sys.stderr)
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
