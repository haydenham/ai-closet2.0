#!/usr/bin/env python3
"""
Color Detection Issue Analysis
=============================

Analyzing the failures from comprehensive testing to identify patterns and fixes needed.
"""

import colorsys

def analyze_failures():
    """Analyze specific color detection failures"""
    
    print("🔍 Analyzing Color Detection Failures")
    print("=" * 45)
    
    failures = [
        ((255, 20, 147), "pink", "purple", "Deep pink - too purple"),
        ((173, 216, 230), "light blue", "powder-blue", "Light blue detection"),
        ((128, 128, 0), "olive", "yellow", "Olive vs yellow issue"),
        ((112, 128, 144), "gray", "sky blue", "Slate gray misclassified"),
        ((222, 184, 135), "beige", "cream", "Beige vs cream distinction"),
        ((70, 130, 180), "blue", "sky blue", "Steel blue classification"),
        ((34, 139, 34), "green", "olive", "Forest green vs olive"),
        ((47, 79, 79), "dark-gray", "mint", "Dark slate gray issue"),
    ]
    
    for rgb, expected, actual, issue in failures:
        r, g, b = rgb
        r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
        h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
        h_deg = h * 360
        
        print(f"\n❌ RGB({r},{g},{b}) -> {actual} (expected: {expected})")
        print(f"   HSV: ({h_deg:.1f}°, {s:.3f}, {v:.3f}) - {issue}")
        
        # Analyze the issue
        if "pink" in expected and "purple" in actual:
            print(f"   → Red hue ({h_deg:.1f}°) with high saturation needs pink detection")
        elif "light blue" in expected and "powder-blue" in actual:
            print(f"   → Need to map powder-blue to light blue")
        elif "olive" in expected and ("yellow" in actual or "green" in actual):
            print(f"   → Yellow-green hue ({h_deg:.1f}°) needs olive detection")
        elif "gray" in expected and "blue" in actual:
            print(f"   → Low saturation ({s:.3f}) should be gray, not blue")

if __name__ == "__main__":
    analyze_failures()
