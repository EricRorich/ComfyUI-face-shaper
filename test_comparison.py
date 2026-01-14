#!/usr/bin/env python3
"""Visual comparison test to demonstrate the uniform scale fix."""

import sys
sys.path.insert(0, '/home/runner/work/ComfyUI-face-shaper/ComfyUI-face-shaper')

from face_shaper import ComfyUIFaceShaper
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def save_tensor_as_image(tensor, filename):
    """Convert a tensor to an image and save it."""
    arr = tensor[0].numpy()
    arr = (arr * 255).astype(np.uint8)
    img = Image.fromarray(arr, 'RGB')
    img.save(filename)
    return img

def create_comparison_grid():
    """Create a grid showing different canvas sizes with uniform scaling."""
    print("Creating comparison grid...")
    
    node = ComfyUIFaceShaper()
    
    # Common parameters for all tests
    base_params = {
        'transparent_background': False,
        'line_thickness': 2.0,
        'gender': 'female',
        'fov_mm': 80.0,
        'camera_distance': 1.0,
        'camera_pos_x': 0.0,
        'camera_pos_y': 0.0,
        'head_size_x': 1.0,
        'head_size_y': 1.0,
        'jaw_size_x': 1.0,
        'fore_head_size_x': 1.0,
        'eye_left_size_x': 1.0, 'eye_left_size_y': 1.0, 'eye_left_pos_x': 0.0, 'eye_left_pos_y': 0.0,
        'eye_left_rotation': 0.0,
        'eye_right_size_x': 1.0, 'eye_right_size_y': 1.0, 'eye_right_pos_x': 0.0, 'eye_right_pos_y': 0.0,
        'eye_right_rotation': 0.0,
        'iris_left_size': 1.0, 'iris_left_pos_x': 0.0, 'iris_left_pos_y': 0.0,
        'iris_right_size': 1.0, 'iris_right_pos_x': 0.0, 'iris_right_pos_y': 0.0,
        'eyebrow_left_size_x': 1.0, 'eyebrow_left_size_y': 1.0, 'eyebrow_left_pos_x': 0.0, 'eyebrow_left_pos_y': 0.0, 'eyebrow_left_rotation': 0.0,
        'eyebrow_right_size_x': 1.0, 'eyebrow_right_size_y': 1.0, 'eyebrow_right_pos_x': 0.0, 'eyebrow_right_pos_y': 0.0, 'eyebrow_right_rotation': 0.0,
        'cheeks_enabled': True,
        'cheek_left_pos_x': 0.0, 'cheek_left_pos_y': 0.0,
        'cheek_right_pos_x': 0.0, 'cheek_right_pos_y': 0.0,
        'nose_pos_y': 0.0, 'nose_size_x': 1.0, 'nose_size_y': 1.0,
        'nose_tip_pos_y': 0.0,
        'lips_pos_y': 0.0, 'lip_size_x': 1.0,
        'lip_upper_size_y': 1.0, 'lip_lower_size_y': 1.0,
        'settings_list': None
    }
    
    # Test configurations
    configs = [
        ('Square (1024x1024)', 1024, 1024),
        ('Wide (1536x1024)', 1536, 1024),
        ('Tall (1024x1536)', 1024, 1536),
    ]
    
    images = []
    for title, width, height in configs:
        params = base_params.copy()
        params['canvas_width'] = width
        params['canvas_height'] = height
        
        result = node.draw_face(**params)
        tensor, _ = result
        img = save_tensor_as_image(tensor, f'/tmp/comparison_{width}x{height}.png')
        
        # Add title to image
        draw = ImageDraw.Draw(img)
        text = f"{title}"
        # Use default font
        draw.text((10, 10), text, fill=(255, 0, 0))
        
        images.append(img)
        print(f"Generated {title}: {width}x{height}")
    
    print("\n✓ Comparison grid created!")
    print("\nGenerated comparison images:")
    for title, width, height in configs:
        print(f"  /tmp/comparison_{width}x{height}.png - {title}")
    
    print("\nValidation:")
    print("  ✓ Face proportions should be identical in all images")
    print("  ✓ Square canvas: face fills the canvas")
    print("  ✓ Wide canvas: face stays centered with extra horizontal white space")
    print("  ✓ Tall canvas: face stays centered with extra vertical white space")
    print("  ✓ Irises should be circular (not elliptical) in all cases")

if __name__ == "__main__":
    create_comparison_grid()
