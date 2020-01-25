#!/usr/bin/env python

# python3 $0 principal rate term tax

import sys

principal = float(sys.argv[1])
rate = float(sys.argv[2]) / 100
term = float(sys.argv[3])

interest = principal * ( ( (1 + rate) ** term) - 1 )

print("principal= {0:.2f}".format(principal))
print("pre_tax_interest = {0:.2f}".format(interest))

if len(sys.argv) == 5:
    tax = float(sys.argv[4]) / 100
    interest = interest - (interest * tax)
    print("tax = {0:.2f}".format(tax))

print("interest = {0:.2f}".format(interest))
print("total = {0:.2f}".format(principal + interest))

