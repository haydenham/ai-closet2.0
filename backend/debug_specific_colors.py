#!/usr/bin/env python3
"""Debug specific colors that are failing"""
import colorsys

def debug_specific_color(r, g, b, expected):
    """Debug a specific color conversion"""
    print(f"\n🔍 Debugging RGB({r:3d},{g:3d},{b:3d}) - Expected: {expected}")
    
    # Normalize RGB
    r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
    print(f"   Normalized RGB: ({r_norm:.3f}, {g_norm:.3f}, {b_norm:.3f})")
    
    # Convert to HSV
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    h_deg = h * 360  # Convert hue to degrees
    
    print(f"   HSV: ({h_deg:.1f}°, {s:.3f}, {v:.3f})")
    
    # Analyze categorization
    if s < 0.2:
        print(f"   → Grayscale (saturation {s:.3f} < 0.2)")
    elif v < 0.15:
        print(f"   → Black (value {v:.3f} < 0.15)")
    elif v > 0.85 and s > 0.2:
        print(f"   → Light chromatic (value {v:.3f} > 0.85, saturation {s:.3f} > 0.2)")
    elif v > 0.85 and s < 0.3:
        print(f"   → Very light with low saturation")
    elif s >= 0.2:
        print(f"   → Chromatic color")
        if h_deg >= 0 and h_deg < 15 or h_deg >= 345:
            print(f"   → Red range (0-15° or 345-360°)")
        elif h_deg >= 15 and h_deg < 45:
            print(f"   → Orange range (15-45°)")
        elif h_deg >= 45 and h_deg < 75:
            print(f"   → Yellow range (45-75°)")
        elif h_deg >= 75 and h_deg < 150:
            print(f"   → Green range (75-150°)")
        elif h_deg >= 150 and h_deg < 190:
            print(f"   → Cyan range (150-190°)")
        elif h_deg >= 190 and h_deg < 270:
            print(f"   → Blue range (190-270°)")
        elif h_deg >= 270 and h_deg < 345:
            print(f"   → Purple range (270-345°)")

# Debug problematic colors
print("🐛 Debugging Problematic Colors")
print("=" * 50)

debug_specific_color(255, 0, 0, "red")      # Currently returns pink
debug_specific_color(0, 0, 255, "blue")     # Currently returns purple  
debug_specific_color(255, 255, 0, "yellow") # Currently returns green
debug_specific_color(255, 165, 0, "orange") # Currently returns yellow
debug_specific_color(139, 69, 19, "brown")  # Currently returns orange
debug_specific_color(245, 245, 220, "beige") # Currently returns white
