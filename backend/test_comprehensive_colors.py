#!/usr/bin/env python3
"""
Comprehensive Color Detection Cross-Verification Test
===================================================

Extended test suite to validate color detection improvements with additional
edge cases, fashion-specific colors, and real-world scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gcp_vision_service import GCPVisionService

def test_comprehensive_colors():
    """Test comprehensive color detection with expanded test cases"""
    
    # Initialize the service
    vision_service = GCPVisionService()
    
    print("🎨 Comprehensive Color Detection Cross-Verification")
    print("=" * 60)
    
    # Extended test cases with fashion-specific scenarios
    test_cases = [
        # Original test cases
        ((128, 128, 128), "gray", "Medium gray"),
        ((200, 200, 200), "light-gray", "Light gray"),
        ((50, 50, 50), ["dark-gray", "charcoal"], "Dark gray (variant acceptable)"),
        ((255, 255, 255), "white", "Pure white"),
        ((0, 0, 0), "black", "Pure black"),
        ((120, 120, 120), "gray", "Gray dress pants (critical fix)"),
        ((80, 80, 80), "dark-gray", "Charcoal color"),
        
        # Pure colors
        ((255, 0, 0), "red", "Pure red"),
        ((0, 255, 0), "green", "Pure green"),
        ((0, 0, 255), "blue", "Pure blue"),
        ((255, 255, 0), "yellow", "Pure yellow"),
        ((255, 165, 0), "orange", "Orange"),
        ((128, 0, 128), "purple", "Purple"),
        
        # Fashion-specific colors
        ((139, 69, 19), "brown", "Brown leather"),
        ((25, 25, 112), "navy", "Navy blue"),
        ((255, 182, 193), "pink", "Light pink"),
        ((245, 245, 220), "beige", "Beige/cream"),
        
        # Additional edge cases
        ((220, 20, 60), "red", "Crimson red"),
        ((255, 20, 147), "pink", "Deep pink"),
        ((0, 100, 0), "green", "Dark green"),
        ((173, 216, 230), "light blue", "Light blue"),
        ((75, 0, 130), "purple", "Indigo"),
        ((128, 128, 0), "olive", "Olive drab"),
        ((255, 215, 0), "yellow", "Gold"),
        ((192, 192, 192), "light-gray", "Silver"),
        
        # Fashion neutrals
        ((112, 128, 144), "gray", "Slate gray"),
        ((105, 105, 105), "gray", "Dim gray"),
        ((169, 169, 169), "gray", "Dark gray variant"),
        ((211, 211, 211), "light-gray", "Light gray variant"),
        
        # Earth tones
        ((160, 82, 45), "brown", "Saddle brown"),
        ((210, 180, 140), "tan", "Tan"),
        ((222, 184, 135), "beige", "Burlywood"),
        ((245, 222, 179), "beige", "Wheat"),
        
        # Fashion blues
        ((70, 130, 180), "blue", "Steel blue"),
        ((30, 144, 255), "blue", "Dodger blue"),
        ((0, 191, 255), "blue", "Deep sky blue"),
        ((135, 206, 235), "sky blue", "Sky blue"),
        
        # Fashion greens
        ((34, 139, 34), "green", "Forest green"),
        ((50, 205, 50), "green", "Lime green"),
        ((152, 251, 152), "mint", "Pale green"),
        ((143, 188, 143), "sage", "Dark sea green"),
        
        # Pastels
        ((255, 228, 225), "pink", "Misty rose"),
        ((230, 230, 250), "lavender", "Lavender"),
        ((255, 248, 220), "cream", "Cornsilk"),
        ((240, 248, 255), "white", "Alice blue (very light)"),
        
        # Dark colors
        ((47, 79, 79), "dark-gray", "Dark slate gray"),
        ((85, 107, 47), "olive", "Dark olive green"),
        ((72, 61, 139), "purple", "Dark slate blue"),
        ((25, 25, 25), "black", "Very dark gray"),
    ]
    
    correct = 0
    total = len(test_cases)
    
    for rgb, expected, description in test_cases:
        r, g, b = rgb
        result = vision_service._rgb_to_color_name(r, g, b)
        
        # Handle cases where multiple acceptable answers exist
        if isinstance(expected, list):
            is_correct = result in expected
            expected_str = " or ".join(expected)
        else:
            is_correct = result == expected
            expected_str = expected
        
        status = "✅" if is_correct else "❌"
        if is_correct:
            correct += 1
        
        print(f"{status} RGB({r:3d},{g:3d},{b:3d}) -> {result:<12} (expected: {expected_str:<12}) - {description}")
        
        # Add note for acceptable variants
        if not is_correct and isinstance(expected, list):
            print(f"   📝 Note: Acceptable variants, but preference differs")
    
    print("=" * 60)
    accuracy = (correct / total) * 100
    print(f"🎯 Comprehensive Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    
    if accuracy >= 90:
        print("🎉 Excellent color detection performance!")
    elif accuracy >= 80:
        print("✅ Good color detection performance")
    elif accuracy >= 70:
        print("⚠️  Acceptable color detection, room for improvement")
    else:
        print("❌ Color detection needs significant improvement")
    
    return accuracy

def test_color_gradients():
    """Test color detection across gradients to verify smooth transitions"""
    
    print("\n🌈 Color Gradient Transition Test")
    print("=" * 40)
    
    vision_service = GCPVisionService()
    
    # Test red to pink gradient
    print("Red → Pink Gradient:")
    red_pink_gradient = [
        ((255, 0, 0), "red"),      # Pure red
        ((255, 50, 50), "red"),    # Slightly lighter red
        ((255, 100, 100), "red"),  # Light red
        ((255, 150, 150), "pink"), # Light pink
        ((255, 200, 200), "pink"), # Very light pink
    ]
    
    for rgb, expected in red_pink_gradient:
        r, g, b = rgb
        result = vision_service._rgb_to_color_name(r, g, b)
        status = "✅" if result == expected else "❌"
        print(f"  {status} RGB({r},{g},{b}) -> {result} (expected: {expected})")
    
    # Test blue gradient
    print("\nBlue Gradient:")
    blue_gradient = [
        ((0, 0, 139), "navy"),      # Dark blue
        ((0, 0, 200), "blue"),      # Medium blue  
        ((0, 0, 255), "blue"),      # Pure blue
        ((100, 149, 237), "blue"),  # Cornflower blue
        ((173, 216, 230), "light blue"), # Light blue
    ]
    
    for rgb, expected in blue_gradient:
        r, g, b = rgb
        result = vision_service._rgb_to_color_name(r, g, b)
        status = "✅" if result == expected else "❌"
        print(f"  {status} RGB({r},{g},{b}) -> {result} (expected: {expected})")

def test_fashion_scenarios():
    """Test colors in real fashion contexts"""
    
    print("\n👗 Fashion Context Color Test")
    print("=" * 35)
    
    vision_service = GCPVisionService()
    
    fashion_scenarios = [
        # Denim colors
        ((29, 53, 87), "navy", "Dark denim"),
        ((70, 130, 180), "blue", "Medium denim"),
        ((176, 196, 222), "light blue", "Light wash denim"),
        
        # Business attire
        ((47, 79, 79), "dark-gray", "Charcoal suit"),
        ((25, 25, 112), "navy", "Navy blazer"),
        ((255, 255, 255), "white", "White dress shirt"),
        
        # Casual wear
        ((220, 20, 60), "red", "Red t-shirt"),
        ((0, 100, 0), "green", "Forest green hoodie"),
        ((139, 69, 19), "brown", "Brown leather jacket"),
        
        # Footwear
        ((0, 0, 0), "black", "Black dress shoes"),
        ((139, 69, 19), "brown", "Brown leather boots"),
        ((255, 255, 255), "white", "White sneakers"),
        
        # Accessories  
        ((192, 192, 192), "light-gray", "Silver jewelry"),
        ((255, 215, 0), "yellow", "Gold jewelry"),
        ((139, 69, 19), "brown", "Leather belt"),
    ]
    
    correct = 0
    for rgb, expected, context in fashion_scenarios:
        r, g, b = rgb
        result = vision_service._rgb_to_color_name(r, g, b)
        is_correct = result == expected
        if is_correct:
            correct += 1
        status = "✅" if is_correct else "❌"
        print(f"{status} RGB({r:3d},{g:3d},{b:3d}) -> {result:<12} - {context}")
    
    accuracy = (correct / len(fashion_scenarios)) * 100
    print(f"\n🎯 Fashion Context Accuracy: {correct}/{len(fashion_scenarios)} ({accuracy:.1f}%)")

if __name__ == "__main__":
    # Run comprehensive tests
    overall_accuracy = test_comprehensive_colors()
    test_color_gradients() 
    test_fashion_scenarios()
    
    print(f"\n📊 Overall Assessment:")
    print(f"Primary Test Accuracy: {overall_accuracy:.1f}%")
    print(f"Ready for Phase 2: {'Yes' if overall_accuracy >= 85 else 'Needs improvement'}")
