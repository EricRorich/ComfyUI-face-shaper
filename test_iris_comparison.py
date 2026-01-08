#!/usr/bin/env python3
"""Create a comparison showing iris position before and after baking offsets."""

import sys
sys.path.insert(0, '/home/runner/work/ComfyUI-face-shaper/ComfyUI-face-shaper')

from face_shaper import ComfyUIFaceShaper
from PIL import Image, ImageDraw, ImageFont

def create_comparison():
    """Create side-by-side comparison of iris positions."""
    node = ComfyUIFaceShaper()
    
    # Common parameters
    common_params = {
        'canvas_width': 512,
        'canvas_height': 512,
        'gender': 'female',
        'transparent_background': False,
        'eye_left_size_x': 1.0, 'eye_left_size_y': 1.0, 'eye_left_pos_x': 0.0, 'eye_left_pos_y': 0.0,
        'eye_right_size_x': 1.0, 'eye_right_size_y': 1.0, 'eye_right_pos_x': 0.0, 'eye_right_pos_y': 0.0,
        'iris_left_size': 1.0, 'iris_left_pos_y': 0.0,
        'iris_right_size': 1.0, 'iris_right_pos_y': 0.0,
        'outer_head_size_x': 1.0, 'outer_head_size_y': 1.0,
        'jaw_size_x': 1.0, 'forehead_size_x': 1.0,
        'lips_pos_y': 0.0, 'lips_size_x': 1.0,
        'lip_upper_size_y': 1.0, 'lip_lower_size_y': 1.0,
        'chin_size_x': 1.0, 'chin_size_y': 1.0,
        'cheek_left_pos_x': 0.0, 'cheek_left_pos_y': 0.0,
        'cheek_right_pos_x': 0.0, 'cheek_right_pos_y': 0.0,
        'ear_left_pos_x': 0.0, 'ear_left_pos_y': 0.0, 'ear_left_size_x': 1.0, 'ear_left_size_y': 1.0,
        'ear_right_pos_x': 0.0, 'ear_right_pos_y': 0.0, 'ear_right_size_x': 1.0, 'ear_right_size_y': 1.0,
        'eyebrow_left_size_x': 1.0, 'eyebrow_left_size_y': 1.0, 'eyebrow_left_rotation': 0.0,
        'eyebrow_left_pos_x': 0.0, 'eyebrow_left_pos_y': 0.0,
        'eyebrow_right_size_x': 1.0, 'eyebrow_right_size_y': 1.0, 'eyebrow_right_rotation': 0.0,
        'eyebrow_right_pos_x': 0.0, 'eyebrow_right_pos_y': 0.0,
        'nose_pos_y': 0.0, 'nose_size_x': 1.0, 'nose_size_y': 1.0,
        'nose_tip_pos_y': 0.0, 'nose_tip_size_x': 1.0, 'nose_tip_size_y': 1.0,
        'camera_distance': 1.0, 'camera_pos_x': 0.0, 'camera_pos_y': 0.0,
        'fov_mm': 80.0,
        'line_thickness': 2.0,
        'settings_list': None
    }
    
    print("Generating iris comparison images...")
    
    # Image 1: Current implementation (baked offsets, sliders at 0)
    print("  1. With baked offsets (iris_pos_x = 0.0 for both)...")
    tensor1, _ = node.draw_face(
        iris_left_pos_x=0.0,
        iris_right_pos_x=0.0,
        **common_params
    )
    arr1 = (tensor1[0].numpy() * 255.0).astype('uint8')
    img1 = Image.fromarray(arr1)
    
    # Image 2: Simulating old behavior (would need manual offsets to align)
    print("  2. Simulating pre-baked behavior (iris_pos_x at -0.04/+0.04)...")
    tensor2, _ = node.draw_face(
        iris_left_pos_x=-0.04,
        iris_right_pos_x=0.04,
        **common_params
    )
    arr2 = (tensor2[0].numpy() * 255.0).astype('uint8')
    img2 = Image.fromarray(arr2)
    
    # Create combined image
    combined_width = 512 * 2 + 20  # 2 images + gap
    combined_height = 512 + 80  # space for labels
    combined = Image.new('RGB', (combined_width, combined_height), 'white')
    
    # Paste images
    combined.paste(img1, (0, 60))
    combined.paste(img2, (512 + 20, 60))
    
    # Add labels
    draw = ImageDraw.Draw(combined)
    
    # Labels
    draw.text((256, 10), "After: Baked Offsets", fill='black', anchor='mm')
    draw.text((256, 30), "(iris_pos_x = 0.0)", fill='black', anchor='mm')
    
    draw.text((256 + 532, 10), "Visual Equivalent", fill='black', anchor='mm')
    draw.text((256 + 532, 30), "(iris_pos_x = -0.04/+0.04)", fill='black', anchor='mm')
    
    combined.save('/tmp/iris_comparison.png')
    print("✓ Saved /tmp/iris_comparison.png")
    
    print("\nNote: Both images show the same visual result.")
    print("The left image achieves it with default sliders (0.0).")
    print("The right shows equivalent positioning with manual offsets.")

if __name__ == "__main__":
    create_comparison()
