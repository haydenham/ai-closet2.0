#!/usr/bin/env python3
"""
Create a test image for fashion analysis
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    # Create a 300x400 blue shirt-like image
    img = Image.new('RGB', (300, 400), color='#4169E1')  # Royal blue
    draw = ImageDraw.Draw(img)
    
    # Draw a simple shirt outline
    # Shirt body
    draw.rectangle([50, 100, 250, 350], fill='#4169E1', outline='#000080', width=3)
    
    # Sleeves
    draw.ellipse([10, 80, 80, 180], fill='#4169E1', outline='#000080', width=2)
    draw.ellipse([220, 80, 290, 180], fill='#4169E1', outline='#000080', width=2)
    
    # Collar
    draw.polygon([(120, 100), (180, 100), (160, 120), (140, 120)], fill='#4169E1', outline='#000080')
    
    # Buttons
    for y in [140, 170, 200, 230]:
        draw.ellipse([145, y, 155, y+10], fill='white', outline='black')
    
    # Save the image
    test_dir = "/Users/haydenhamilton/AI-CLOSET-PRODUCTION/ai-closet2.0/backend/test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    img_path = os.path.join(test_dir, "sample_shirt.jpg")
    img.save(img_path, "JPEG", quality=90)
    print(f"Test image created: {img_path}")
    
    return img_path

if __name__ == "__main__":
    create_test_image()
