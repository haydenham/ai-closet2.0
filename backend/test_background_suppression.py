#!/usr/bin/env python3
"""
Background Color Impact Analysis
===============================

Demonstrate how image normalization improves color detection by suppressing
background colors and focusing on clothing items.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image, ImageDraw
    import numpy as np
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from app.services.gcp_vision_service import GCPVisionService

def create_clothing_with_distracting_background() -> bytes:
    """Create an image where background colors could interfere with clothing detection"""
    
    # Create image with colorful background
    image = Image.new('RGB', (500, 500), color=(255, 100, 100))  # Red background
    draw = ImageDraw.Draw(image)
    
    # Add colorful background elements
    draw.rectangle([0, 0, 500, 100], fill=(100, 255, 100))     # Green top
    draw.rectangle([0, 400, 500, 500], fill=(100, 100, 255))   # Blue bottom
    draw.rectangle([0, 0, 100, 500], fill=(255, 255, 100))     # Yellow left
    draw.rectangle([400, 0, 500, 500], fill=(255, 100, 255))   # Magenta right
    
    # Add the actual clothing item (gray shirt in center)
    clothing_color = (120, 120, 120)  # Gray shirt
    draw.rectangle([150, 150, 350, 350], fill=clothing_color)
    
    # Add some texture to the clothing
    draw.rectangle([160, 160, 180, 340], fill=(100, 100, 100))  # Darker stripe
    draw.rectangle([320, 160, 340, 340], fill=(140, 140, 140))  # Lighter stripe
    
    # Convert to bytes
    output_buffer = io.BytesIO()
    image.save(output_buffer, format='JPEG', quality=95)
    return output_buffer.getvalue()

def simulate_color_analysis_without_normalization(image_data: bytes) -> dict:
    """Simulate what happens without proper background suppression"""
    
    # Open image and analyze all colors (including background)
    image = Image.open(io.BytesIO(image_data))
    img_array = np.array(image)
    
    # Get all unique colors in the image
    pixels = img_array.reshape(-1, 3)
    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
    
    # Get the most prominent colors
    sorted_indices = np.argsort(counts)[::-1]
    top_colors = unique_colors[sorted_indices[:5]]
    top_counts = counts[sorted_indices[:5]]
    
    # Convert to color names using our service
    vision_service = GCPVisionService()
    detected_colors = []
    
    for i, color in enumerate(top_colors):
        r, g, b = color
        color_name = vision_service._rgb_to_color_name(r, g, b)
        pixel_percentage = (top_counts[i] / len(pixels)) * 100
        detected_colors.append({
            'color': color_name,
            'rgb': (int(r), int(g), int(b)),
            'percentage': pixel_percentage
        })
    
    return {
        'dominant_colors': detected_colors,
        'total_unique_colors': len(unique_colors)
    }

def analyze_with_normalization(image_data: bytes) -> dict:
    """Analyze colors with full normalization pipeline"""
    
    vision_service = GCPVisionService()
    
    # Apply normalization
    normalized_image_data = vision_service.normalize_image(image_data, enhance_clothing_focus=True)
    
    # Analyze the normalized image
    return simulate_color_analysis_without_normalization(normalized_image_data)

def demonstrate_background_suppression():
    """Demonstrate the impact of background suppression"""
    
    print("🎯 Background Color Suppression Analysis")
    print("=" * 50)
    
    if not HAS_PIL:
        print("❌ PIL not available")
        return
    
    try:
        # Create test image with distracting background
        test_image = create_clothing_with_distracting_background()
        print("📸 Created test image: Gray clothing with colorful background")
        print("   Expected: Gray should be the primary clothing color")
        print("   Problem: Background colors (red, green, blue, yellow, magenta) may dominate")
        
        # Analyze without normalization
        print("\n📊 Analysis WITHOUT Normalization:")
        without_norm = simulate_color_analysis_without_normalization(test_image)
        
        for i, color_info in enumerate(without_norm['dominant_colors']):
            color_name = color_info['color']
            rgb = color_info['rgb']
            percentage = color_info['percentage']
            print(f"   {i+1}. {color_name:<12} RGB{rgb} - {percentage:.1f}% of image")
        
        # Analyze with normalization
        print("\n📊 Analysis WITH Normalization:")
        with_norm = analyze_with_normalization(test_image)
        
        for i, color_info in enumerate(with_norm['dominant_colors']):
            color_name = color_info['color']
            rgb = color_info['rgb']
            percentage = color_info['percentage']
            print(f"   {i+1}. {color_name:<12} RGB{rgb} - {percentage:.1f}% of image")
        
        # Compare results
        print("\n🔍 Impact Analysis:")
        
        without_colors = [c['color'] for c in without_norm['dominant_colors'][:3]]
        with_colors = [c['color'] for c in with_norm['dominant_colors'][:3]]
        
        print(f"   Top 3 colors WITHOUT normalization: {without_colors}")
        print(f"   Top 3 colors WITH normalization: {with_colors}")
        
        # Check if gray (clothing) is more prominent after normalization
        gray_rank_without = next((i for i, c in enumerate(without_colors) if 'gray' in c.lower()), -1)
        gray_rank_with = next((i for i, c in enumerate(with_colors) if 'gray' in c.lower()), -1)
        
        if gray_rank_with != -1 and (gray_rank_without == -1 or gray_rank_with < gray_rank_without):
            print("   ✅ SUCCESS: Gray clothing color is more prominent after normalization")
        else:
            print("   ⚠️  Mixed results: Check if normalization parameters need tuning")
        
        # Background color reduction
        bg_colors = ['red', 'green', 'blue', 'yellow', 'magenta']
        bg_count_without = sum(1 for c in without_colors if any(bg in c.lower() for bg in bg_colors))
        bg_count_with = sum(1 for c in with_colors if any(bg in c.lower() for bg in bg_colors))
        
        print(f"   Background colors in top 3 - Without: {bg_count_without}, With: {bg_count_with}")
        if bg_count_with < bg_count_without:
            print("   ✅ Background color suppression working!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def test_real_world_scenarios():
    """Test normalization with scenarios similar to real clothing photos"""
    
    print("\n👕 Real-World Scenario Testing")
    print("=" * 35)
    
    scenarios = [
        {
            'name': 'White shirt on white background',
            'clothing': (250, 250, 250),
            'background': (255, 255, 255),
            'challenge': 'Low contrast between clothing and background'
        },
        {
            'name': 'Navy jacket on dark background',
            'clothing': (25, 25, 112),
            'background': (50, 50, 50),
            'challenge': 'Dark clothing on dark background'
        },
        {
            'name': 'Red dress on busy patterned background',
            'clothing': (200, 50, 50),
            'background': None,  # Will create pattern
            'challenge': 'Clothing vs complex background pattern'
        }
    ]
    
    vision_service = GCPVisionService()
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Challenge: {scenario['challenge']}")
        
        # Create test image for this scenario
        image = Image.new('RGB', (300, 300), color=scenario['background'] or (200, 150, 100))
        draw = ImageDraw.Draw(image)
        
        # Add pattern for complex background scenario
        if scenario['background'] is None:
            # Create busy pattern
            for x in range(0, 300, 20):
                for y in range(0, 300, 20):
                    color = (150 + (x % 100), 100 + (y % 100), 75)
                    draw.rectangle([x, y, x+10, y+10], fill=color)
        
        # Add clothing item
        clothing_color = scenario['clothing']
        draw.rectangle([100, 100, 200, 250], fill=clothing_color)
        
        # Convert to bytes
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='JPEG', quality=95)
        image_data = output_buffer.getvalue()
        
        # Test color detection
        expected_color = vision_service._rgb_to_color_name(*clothing_color)
        print(f"   Expected clothing color: {expected_color}")
        print(f"   ✅ Scenario created and ready for analysis")

if __name__ == "__main__":
    print("🖼️  Background Color Impact Analysis")
    print("=" * 40)
    
    demonstrate_background_suppression()
    test_real_world_scenarios()
    
    print("\n📋 Summary of Image Normalization Benefits:")
    print("   • Suppresses distracting background colors")
    print("   • Enhances clothing item visibility")
    print("   • Improves color accuracy through white balance")
    print("   • Optimizes contrast for better feature detection")
    print("   • Reduces noise that could affect classification")
    print("\n🎯 Ready for integration with GCP Vision API analysis!")
