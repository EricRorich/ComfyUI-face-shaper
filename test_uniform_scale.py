#!/usr/bin/env python3
"""Test uniform scene scaling to verify face proportions are maintained across different canvas sizes."""

import sys
import os
# Add the current directory to the path so we can import face_shaper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from face_shaper import ComfyUIFaceShaper
from PIL import Image
import numpy as np

def save_tensor_as_image(tensor, filename):
    """Convert a tensor to an image and save it."""
    # tensor shape: [B, H, W, C]
    arr = tensor[0].numpy()  # Get first batch
    arr = (arr * 255).astype(np.uint8)
    if arr.shape[2] == 3:
        img = Image.fromarray(arr, 'RGB')
    else:
        img = Image.fromarray(arr, 'RGBA')
    img.save(filename)
    print(f"Saved image to {filename}")

def get_default_params():
    """Return default parameters for drawing a face."""
    return {
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

def test_square_canvas():
    """Test 1024x1024 - should be unchanged from previous behavior."""
    print("Testing 1024x1024 (square canvas)...")
    node = ComfyUIFaceShaper()
    
    params = get_default_params()
    params['canvas_width'] = 1024
    params['canvas_height'] = 1024
    
    result = node.draw_face(**params)
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/test_1024x1024.png')
    print("✓ 1024x1024 test passed - face should look normal")

def test_wide_canvas():
    """Test 1536x1024 - face should remain proportional with extra space on sides."""
    print("\nTesting 1536x1024 (wide canvas)...")
    node = ComfyUIFaceShaper()
    
    params = get_default_params()
    params['canvas_width'] = 1536
    params['canvas_height'] = 1024
    
    result = node.draw_face(**params)
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/test_1536x1024.png')
    print("✓ 1536x1024 test passed - face should be proportional with extra horizontal space")

def test_tall_canvas():
    """Test 1024x1536 - face should remain proportional with extra space on top/bottom."""
    print("\nTesting 1024x1536 (tall canvas)...")
    node = ComfyUIFaceShaper()
    
    params = get_default_params()
    params['canvas_width'] = 1024
    params['canvas_height'] = 1536
    
    result = node.draw_face(**params)
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/test_1024x1536.png')
    print("✓ 1024x1536 test passed - face should be proportional with extra vertical space")

def test_camera_zoom():
    """Test camera_distance on square canvas - should zoom uniformly."""
    print("\nTesting camera_distance=1.5 on 1024x1024...")
    node = ComfyUIFaceShaper()
    
    params = get_default_params()
    params['canvas_width'] = 1024
    params['canvas_height'] = 1024
    params['camera_distance'] = 1.5
    
    result = node.draw_face(**params)
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/test_zoom_1.5.png')
    print("✓ Camera zoom test passed - face should be 1.5x larger but still proportional")

def test_camera_zoom_wide():
    """Test camera_distance on wide canvas - should zoom uniformly."""
    print("\nTesting camera_distance=1.5 on 1536x1024...")
    node = ComfyUIFaceShaper()
    
    params = get_default_params()
    params['canvas_width'] = 1536
    params['canvas_height'] = 1024
    params['camera_distance'] = 1.5
    
    result = node.draw_face(**params)
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/test_zoom_wide_1.5.png')
    print("✓ Camera zoom (wide) test passed - face should be 1.5x larger and proportional")

def test_camera_pan():
    """Test camera_pos_x and camera_pos_y - should shift view without distortion."""
    print("\nTesting camera_pos_x=0.2, camera_pos_y=0.1 on 1024x1024...")
    node = ComfyUIFaceShaper()
    
    params = get_default_params()
    params['canvas_width'] = 1024
    params['canvas_height'] = 1024
    params['camera_pos_x'] = 0.2
    params['camera_pos_y'] = 0.1
    
    result = node.draw_face(**params)
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/test_camera_pan.png')
    print("✓ Camera pan test passed - face should be shifted but proportional")

if __name__ == "__main__":
    print("Running uniform scale tests...\n")
    
    test_square_canvas()
    test_wide_canvas()
    test_tall_canvas()
    test_camera_zoom()
    test_camera_zoom_wide()
    test_camera_pan()
    
    print("\n✓ All uniform scale tests completed!")
    print("\nGenerated test images:")
    print("  /tmp/test_1024x1024.png - Square canvas (baseline)")
    print("  /tmp/test_1536x1024.png - Wide canvas (should have extra horizontal space)")
    print("  /tmp/test_1024x1536.png - Tall canvas (should have extra vertical space)")
    print("  /tmp/test_zoom_1.5.png - Zoomed 1.5x on square canvas")
    print("  /tmp/test_zoom_wide_1.5.png - Zoomed 1.5x on wide canvas")
    print("  /tmp/test_camera_pan.png - Camera panned (shifted view)")
    print("\nValidation:")
    print("  - All faces should maintain circular irises (not elliptical)")
    print("  - Face proportions should be identical across all canvas sizes")
    print("  - Non-square canvases should show extra white space, not stretched faces")
