#!/usr/bin/env python3
"""Test rendering script to verify the updated geometry visually."""

import sys
sys.path.insert(0, '/home/runner/work/ComfyUI-face-shaper/ComfyUI-face-shaper')

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

def test_default_render():
    """Test rendering with default parameters."""
    print("Testing default render...")
    node = ComfyUIFaceShaper()
    
    result = node.draw_face(
        canvas_width=1024,
        canvas_height=1024,
        gender="female",
        transparent_background=False,
        debug_geometry=False,
        eye_left_size_x=1.0, eye_left_size_y=1.0, eye_left_pos_x=0.0, eye_left_pos_y=0.0,
        eye_right_size_x=1.0, eye_right_size_y=1.0, eye_right_pos_x=0.0, eye_right_pos_y=0.0,
        iris_left_size=1.0, iris_left_pos_x=0.0, iris_left_pos_y=0.0,
        iris_right_size=1.0, iris_right_pos_x=0.0, iris_right_pos_y=0.0,
        outer_head_size_x=1.0, outer_head_size_y=1.0,
        jaw_size_x=1.0, forehead_size_x=1.0,
        lips_pos_y=0.0, lips_size_x=1.0,
        lip_upper_size_y=1.0, lip_lower_size_y=1.0,
        chin_size_x=1.0, chin_size_y=1.0,
        cheek_left_pos_x=0.0, cheek_left_pos_y=0.0,
        cheek_right_pos_x=0.0, cheek_right_pos_y=0.0,
        ear_left_pos_x=0.0, ear_left_pos_y=0.0, ear_left_size_x=1.0, ear_left_size_y=1.0,
        ear_right_pos_x=0.0, ear_right_pos_y=0.0, ear_right_size_x=1.0, ear_right_size_y=1.0,
        eyebrow_left_size_x=1.0, eyebrow_left_size_y=1.0, eyebrow_left_rotation=0.0,
        eyebrow_left_pos_x=0.0, eyebrow_left_pos_y=0.0,
        eyebrow_right_size_x=1.0, eyebrow_right_size_y=1.0, eyebrow_right_rotation=0.0,
        eyebrow_right_pos_x=0.0, eyebrow_right_pos_y=0.0,
        nose_pos_y=0.0, nose_size_x=1.0, nose_size_y=1.0,
        nose_tip_pos_y=0.0,
        camera_distance=1.0, camera_pos_x=0.0, camera_pos_y=0.0,
        fov_mm=80.0,
        line_thickness=2.0,
        settings_list=None
    )
    
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/face_default.png')
    print("✓ Default render test passed")

def test_nose_tip_adjustment():
    """Test rendering with nose tip adjustment."""
    print("\nTesting nose tip adjustment...")
    node = ComfyUIFaceShaper()
    
    # Render with nose tip moved down
    result = node.draw_face(
        canvas_width=1024,
        canvas_height=1024,
        gender="female",
        transparent_background=False,
        debug_geometry=False,
        eye_left_size_x=1.0, eye_left_size_y=1.0, eye_left_pos_x=0.0, eye_left_pos_y=0.0,
        eye_right_size_x=1.0, eye_right_size_y=1.0, eye_right_pos_x=0.0, eye_right_pos_y=0.0,
        iris_left_size=1.0, iris_left_pos_x=0.0, iris_left_pos_y=0.0,
        iris_right_size=1.0, iris_right_pos_x=0.0, iris_right_pos_y=0.0,
        outer_head_size_x=1.0, outer_head_size_y=1.0,
        jaw_size_x=1.0, forehead_size_x=1.0,
        lips_pos_y=0.0, lips_size_x=1.0,
        lip_upper_size_y=1.0, lip_lower_size_y=1.0,
        chin_size_x=1.0, chin_size_y=1.0,
        cheek_left_pos_x=0.0, cheek_left_pos_y=0.0,
        cheek_right_pos_x=0.0, cheek_right_pos_y=0.0,
        ear_left_pos_x=0.0, ear_left_pos_y=0.0, ear_left_size_x=1.0, ear_left_size_y=1.0,
        ear_right_pos_x=0.0, ear_right_pos_y=0.0, ear_right_size_x=1.0, ear_right_size_y=1.0,
        eyebrow_left_size_x=1.0, eyebrow_left_size_y=1.0, eyebrow_left_rotation=0.0,
        eyebrow_left_pos_x=0.0, eyebrow_left_pos_y=0.0,
        eyebrow_right_size_x=1.0, eyebrow_right_size_y=1.0, eyebrow_right_rotation=0.0,
        eyebrow_right_pos_x=0.0, eyebrow_right_pos_y=0.0,
        nose_pos_y=0.0, nose_size_x=1.0, nose_size_y=1.0,
        nose_tip_pos_y=0.1,  # Move tip down
        camera_distance=1.0, camera_pos_x=0.0, camera_pos_y=0.0,
        fov_mm=80.0,
        line_thickness=2.0,
        settings_list=None
    )
    
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/face_nose_tip_down.png')
    print("✓ Nose tip adjustment test passed")

def test_debug_geometry():
    """Test rendering with debug geometry to highlight nose tip points."""
    print("\nTesting debug geometry...")
    node = ComfyUIFaceShaper()
    
    result = node.draw_face(
        canvas_width=1024,
        canvas_height=1024,
        gender="female",
        transparent_background=False,
        debug_geometry=True,  # Enable debug markers
        eye_left_size_x=1.0, eye_left_size_y=1.0, eye_left_pos_x=0.0, eye_left_pos_y=0.0,
        eye_right_size_x=1.0, eye_right_size_y=1.0, eye_right_pos_x=0.0, eye_right_pos_y=0.0,
        iris_left_size=1.0, iris_left_pos_x=0.0, iris_left_pos_y=0.0,
        iris_right_size=1.0, iris_right_pos_x=0.0, iris_right_pos_y=0.0,
        outer_head_size_x=1.0, outer_head_size_y=1.0,
        jaw_size_x=1.0, forehead_size_x=1.0,
        lips_pos_y=0.0, lips_size_x=1.0,
        lip_upper_size_y=1.0, lip_lower_size_y=1.0,
        chin_size_x=1.0, chin_size_y=1.0,
        cheek_left_pos_x=0.0, cheek_left_pos_y=0.0,
        cheek_right_pos_x=0.0, cheek_right_pos_y=0.0,
        ear_left_pos_x=0.0, ear_left_pos_y=0.0, ear_left_size_x=1.0, ear_left_size_y=1.0,
        ear_right_pos_x=0.0, ear_right_pos_y=0.0, ear_right_size_x=1.0, ear_right_size_y=1.0,
        eyebrow_left_size_x=1.0, eyebrow_left_size_y=1.0, eyebrow_left_rotation=0.0,
        eyebrow_left_pos_x=0.0, eyebrow_left_pos_y=0.0,
        eyebrow_right_size_x=1.0, eyebrow_right_size_y=1.0, eyebrow_right_rotation=0.0,
        eyebrow_right_pos_x=0.0, eyebrow_right_pos_y=0.0,
        nose_pos_y=0.0, nose_size_x=1.0, nose_size_y=1.0,
        nose_tip_pos_y=0.0,
        camera_distance=1.0, camera_pos_x=0.0, camera_pos_y=0.0,
        fov_mm=80.0,
        line_thickness=2.0,
        settings_list=None
    )
    
    tensor, settings_list = result
    save_tensor_as_image(tensor, '/tmp/face_debug.png')
    print("✓ Debug geometry test passed")

if __name__ == "__main__":
    print("Running render tests...\n")
    
    test_default_render()
    test_nose_tip_adjustment()
    test_debug_geometry()
    
    print("\n✓ All render tests completed!")
    print("\nGenerated images:")
    print("  /tmp/face_default.png - Default render with updated geometry")
    print("  /tmp/face_nose_tip_down.png - Nose tip adjusted down (+0.1)")
    print("  /tmp/face_debug.png - Debug mode showing nose tip points")
