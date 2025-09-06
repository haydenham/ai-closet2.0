#!/usr/bin/env python3
"""
Debug HSV calculation issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def rgb_to_hsv_debug(r, g, b):
    """Debug version of RGB to HSV conversion"""
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    
    max_val = max(r_norm, g_norm, b_norm)
    min_val = min(r_norm, g_norm, b_norm)
    diff = max_val - min_val
    
    # Calculate brightness (Value)
    value = max_val
    
    # Calculate saturation
    saturation = 0 if max_val == 0 else diff / max_val
    
    # Calculate hue
    if diff == 0:
        hue = 0
    elif max_val == r_norm:
        hue = (60 * ((g_norm - b_norm) / diff) + 360) % 360
    elif max_val == g_norm:
        hue = (60 * ((b_norm - r_norm) / diff) + 120) % 360
    else:  # max_val == b_norm
        hue = (60 * ((r_norm - g_norm) / diff) + 240) % 360
    
    print(f"RGB({r:3d},{g:3d},{b:3d}) -> HSV({hue:6.1f}, {saturation:.3f}, {value:.3f})")
    return hue, saturation, value

# Test problematic cases
test_cases = [
    (255, 0, 0, "Pure red"),
    (0, 0, 255, "Pure blue"), 
    (255, 255, 0, "Pure yellow"),
    (255, 165, 0, "Orange"),
    (139, 69, 19, "Brown"),
    (245, 245, 220, "Beige"),
]

print("🔍 Debugging HSV Conversion")
print("=" * 50)

for r, g, b, desc in test_cases:
    print(f"{desc}:")
    hue, sat, val = rgb_to_hsv_debug(r, g, b)
    print()
