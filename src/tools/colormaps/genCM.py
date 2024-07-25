#!/usr/bin/env python
import colorsys
import pandas as pd
algaeCM = []

# read cmocean rgb file
df = pd.read_csv('algae.txt')

# convert to ints, make hex string and store
for index, value in df.iterrows():
    r = value[0]
    g = value[1]
    b = value[2]
    (r,g,b) = (int(r*255),int(g*255),int(b*255))
    hex_string = "#%02x%02x%02x" % (r,g,b)
    algaeCM.append(hex_string)

print(algaeCM)
