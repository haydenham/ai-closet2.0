#!/usr/bin/env python3
"""
Real-World Testing Debug Tool
============================

Helper tool to analyze real images and debug color detection issues.
Use this when testing with actual clothing photos.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image
    import numpy as np
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from app.services.gcp_vision_service import GCPVisionService

def analyze_real_image(image_path: str, debug_normalization: bool = True):
    """
    Analyze a real clothing image and provide detailed debugging info
    
    Args:
        image_path: Path to the image file
        debug_normalization: Whether to show before/after normalization
    """
    
    print(f"🔍 Analyzing Real Image: {os.path.basename(image_path)}")
    print("=" * 60)
    
    if not HAS_PIL:
        print("❌ PIL not available for image analysis")
        return
    
    try:
        # Load image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Initialize service
        vision_service = GCPVisionService()
        
        # Analyze image properties
        image = Image.open(image_path)
        print(f"📐 Image Dimensions: {image.size}")
        print(f"📊 Image Mode: {image.mode}")
        print(f"💾 File Size: {len(image_data)} bytes")
        
        if debug_normalization:
            print("\n🔍 NORMALIZATION ANALYSIS:")
            
            # Analyze colors without normalization
            print("\n📊 Colors WITHOUT Normalization:")
            colors_without = analyze_image_colors(image_data, vision_service, normalize=False)
            display_color_analysis(colors_without)
            
            # Analyze colors with normalization
            print("\n📊 Colors WITH Normalization:")
            colors_with = analyze_image_colors(image_data, vision_service, normalize=True)
            display_color_analysis(colors_with)
            
            # Compare results
            print("\n🔄 COMPARISON:")
            compare_color_results(colors_without, colors_with)
        
        else:
            # Just analyze with normalization
            print("\n📊 Color Analysis (With Normalization):")
            colors = analyze_image_colors(image_data, vision_service, normalize=True)
            display_color_analysis(colors)
        
        # Provide recommendations
        print("\n💡 RECOMMENDATIONS:")
        provide_recommendations(image, colors_with if debug_normalization else colors)
        
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def analyze_image_colors(image_data: bytes, vision_service, normalize: bool = True):
    """Extract and analyze colors from image"""
    
    # Apply normalization if requested
    processed_data = image_data
    if normalize:
        processed_data = vision_service.normalize_image(image_data, enhance_clothing_focus=True)
    
    # Open processed image and extract colors
    image = Image.open(io.BytesIO(processed_data))
    img_array = np.array(image)
    
    # Get color distribution
    pixels = img_array.reshape(-1, 3)
    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
    
    # Get top colors
    sorted_indices = np.argsort(counts)[::-1]
    top_colors = unique_colors[sorted_indices[:10]]
    top_counts = counts[sorted_indices[:10]]
    
    # Convert to color names
    color_results = []
    total_pixels = len(pixels)
    
    for i, color in enumerate(top_colors):
        r, g, b = color
        color_name = vision_service._rgb_to_color_name(r, g, b)
        percentage = (top_counts[i] / total_pixels) * 100
        
        color_results.append({
            'color_name': color_name,
            'rgb': (int(r), int(g), int(b)),
            'percentage': percentage,
            'pixel_count': int(top_counts[i])
        })
    
    return color_results

def display_color_analysis(colors):
    """Display color analysis results"""
    for i, color_info in enumerate(colors[:5]):  # Show top 5
        name = color_info['color_name']
        rgb = color_info['rgb']
        pct = color_info['percentage']
        print(f"   {i+1}. {name:<12} RGB{rgb} - {pct:.1f}%")

def compare_color_results(before, after):
    """Compare before and after normalization results"""
    
    before_top3 = [c['color_name'] for c in before[:3]]
    after_top3 = [c['color_name'] for c in after[:3]]
    
    print(f"   Top 3 BEFORE: {before_top3}")
    print(f"   Top 3 AFTER:  {after_top3}")
    
    # Check for improvements
    background_colors = ['white', 'black', 'gray', 'light-gray', 'beige', 'cream']
    clothing_colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'navy', 'brown']
    
    before_bg = sum(1 for c in before_top3 if c in background_colors)
    after_bg = sum(1 for c in after_top3 if c in background_colors)
    
    before_clothing = sum(1 for c in before_top3 if c in clothing_colors)
    after_clothing = sum(1 for c in after_top3 if c in clothing_colors)
    
    print(f"   Background colors: {before_bg} → {after_bg}")
    print(f"   Clothing colors: {before_clothing} → {after_clothing}")
    
    if after_clothing > before_clothing:
        print("   ✅ More clothing colors detected after normalization")
    elif after_bg < before_bg:
        print("   ✅ Background colors reduced after normalization")
    else:
        print("   ⚠️  Mixed results - may need parameter tuning")

def provide_recommendations(image: Image.Image, colors):
    """Provide recommendations based on analysis"""
    
    width, height = image.size
    
    # Check image quality
    if min(width, height) < 300:
        print("   📐 Image resolution is low - consider higher resolution photos")
    
    # Check color diversity
    unique_colors = len(set(c['color_name'] for c in colors))
    if unique_colors > 8:
        print("   🌈 High color diversity - may indicate complex background")
    
    # Check dominant color percentage
    top_color_pct = colors[0]['percentage']
    if top_color_pct > 60:
        print("   🎯 Single color dominates - good for clothing detection")
    elif top_color_pct < 20:
        print("   ⚠️  No dominant color - complex image or poor focus")
    
    # Check for typical background colors
    top_color = colors[0]['color_name']
    if top_color in ['white', 'light-gray', 'beige']:
        print("   📋 Light background detected - good for dark clothing")
    elif top_color in ['black', 'dark-gray', 'charcoal']:
        print("   📋 Dark background detected - good for light clothing")

def quick_test_multiple_images(image_dir: str):
    """Quick test multiple images in a directory"""
    
    print(f"🔍 Quick Test: Multiple Images in {image_dir}")
    print("=" * 50)
    
    import glob
    
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(image_dir, ext)))
        image_files.extend(glob.glob(os.path.join(image_dir, ext.upper())))
    
    if not image_files:
        print("❌ No image files found")
        return
    
    vision_service = GCPVisionService()
    
    for image_path in image_files[:5]:  # Test first 5 images
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            colors = analyze_image_colors(image_data, vision_service, normalize=True)
            top_color = colors[0]['color_name']
            
            print(f"📸 {os.path.basename(image_path):<25} → Primary: {top_color}")
            
        except Exception as e:
            print(f"❌ {os.path.basename(image_path):<25} → Error: {e}")

if __name__ == "__main__":
    print("🧪 Real-World Image Testing Tool")
    print("=" * 40)
    print("Usage examples:")
    print("  python debug_real_images.py")
    print("  analyze_real_image('path/to/your/image.jpg')")
    print("  quick_test_multiple_images('path/to/image/folder')")
    print("\nReady for your image testing! 📸")
