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

def number_to_western_words(num):
    """Convert number to full Western text representation"""
    if num < 0:
        return f"minus {number_to_western_words(-num)}"
    
    if num == 0:
        return "zero"
    
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
    billions = int(num // 1000000000)
    num %= 1000000000
    millions = int(num // 1000000)
    num %= 1000000
    thousands = int(num // 1000)
    num %= 1000
    hundreds = int(num)
    
    parts = []
    
    if billions > 0:
        if billions == 1:
            parts.append("one billion")
        else:
            parts.append(convert_hundreds(billions) + " billion")
    
    if millions > 0:
        if millions == 1:
            parts.append("one million")
        else:
            parts.append(convert_hundreds(millions) + " million")
    
    if thousands > 0:
        if thousands == 1:
            parts.append("one thousand")
        else:
            parts.append(convert_hundreds(thousands) + " thousand")
    
    if hundreds > 0:
        parts.append(convert_hundreds(hundreds))
    
    result = ", ".join(parts) if parts else "zero"
    return result.capitalize()

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
                words = number_to_western_words(num)
                print(f"{line} = {comma_formatted} = {converted} = {words}")
            except ValueError:
                print(f"Invalid number: {line}", file=sys.stderr)
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
