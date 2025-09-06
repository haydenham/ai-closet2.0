#!/usr/bin/env python3
"""
Test script for enhanced color detection improvements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.gcp_vision_service import GCPVisionService

def test_color_detection():
    """Test the enhanced color detection with various RGB values"""
    
    # Create a mock vision service for testing color detection
    class MockVisionService(GCPVisionService):
        def __init__(self):
            # Skip the GCP client initialization for testing
            pass
    
    try:
        service = MockVisionService()
    except Exception as e:
        print(f"Note: Skipping GCP initialization for testing: {e}")
        service = MockVisionService()
    
    # Test cases: (R, G, B, Expected_Color, Description)
    test_cases = [
        # Grayscale tests
        (128, 128, 128, 'gray', 'Medium gray'),
        (200, 200, 200, 'light-gray', 'Light gray'),
        (50, 50, 50, 'dark-gray', 'Dark gray'),
        (255, 255, 255, 'white', 'Pure white'),
        (0, 0, 0, 'black', 'Pure black'),
        
        # Problematic cases from user feedback
        (120, 120, 120, 'gray', 'Gray dress pants (should not be white)'),
        (80, 80, 80, 'dark-gray', 'Charcoal color'),
        
        # Chromatic colors
        (255, 0, 0, 'red', 'Pure red'),
        (0, 255, 0, 'green', 'Pure green'),
        (0, 0, 255, 'blue', 'Pure blue'),
        (255, 255, 0, 'yellow', 'Pure yellow'),
        (255, 165, 0, 'orange', 'Orange'),
        (128, 0, 128, 'purple', 'Purple'),
        
        # Fashion-specific colors
        (139, 69, 19, 'brown', 'Brown leather'),
        (25, 25, 112, 'navy', 'Navy blue'),
        (255, 182, 193, 'pink', 'Light pink'),
        (245, 245, 220, 'beige', 'Beige/cream'),
    ]
    
    print("🎨 Testing Enhanced Color Detection")
    print("=" * 50)
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for r, g, b, expected, description in test_cases:
        try:
            detected = service._rgb_to_color_name(r, g, b)
            is_correct = detected == expected
            status = "✅" if is_correct else "❌"
            
            print(f"{status} RGB({r:3d},{g:3d},{b:3d}) -> {detected:12s} (expected: {expected:12s}) - {description}")
            
            if is_correct:
                correct_predictions += 1
            else:
                # Check if it's a reasonable variant
                if expected in ['gray', 'light-gray', 'dark-gray'] and detected in ['gray', 'light-gray', 'dark-gray', 'charcoal']:
                    print(f"   📝 Note: Grayscale variant acceptable")
                    
        except Exception as e:
            print(f"❌ RGB({r:3d},{g:3d},{b:3d}) -> ERROR: {e}")
    
    print("=" * 50)
    accuracy = (correct_predictions / total_tests) * 100
    print(f"🎯 Accuracy: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
    
    if accuracy >= 80:
        print("🎉 Enhanced color detection is working well!")
    elif accuracy >= 60:
        print("🔧 Color detection improved but needs more tuning")
    else:
        print("⚠️  Color detection needs significant improvement")

if __name__ == "__main__":
    test_color_detection()
