#!/usr/bin/env python3
"""Test script to verify the ears and nose tip implementation."""

import sys
sys.path.insert(0, '/home/runner/work/ComfyUI-face-shaper/ComfyUI-face-shaper')

from face_shaper import ComfyUIFaceShaper, FEMALE_FACE, SETTINGS_LIST_LENGTH

def test_geometry_data():
    """Test that the geometry data is correct."""
    print("Testing geometry data...")
    
    # Check that ear_left exists
    assert "ear_left" in FEMALE_FACE, "ear_left not found in FEMALE_FACE"
    assert len(FEMALE_FACE["ear_left"]) == 5, f"ear_left should have 5 points, got {len(FEMALE_FACE['ear_left'])}"
    
    # Check that ear_right exists
    assert "ear_right" in FEMALE_FACE, "ear_right not found in FEMALE_FACE"
    assert len(FEMALE_FACE["ear_right"]) == 5, f"ear_right should have 5 points, got {len(FEMALE_FACE['ear_right'])}"
    
    # Check that nose_tip exists
    assert "nose_tip" in FEMALE_FACE, "nose_tip not found in FEMALE_FACE"
    assert len(FEMALE_FACE["nose_tip"]) == 5, f"nose_tip should have 5 points, got {len(FEMALE_FACE['nose_tip'])}"
    
    # Verify coordinates are normalized (0-1 range)
    for key in ["ear_left", "ear_right", "nose_tip"]:
        for x, y in FEMALE_FACE[key]:
            assert 0 <= x <= 1, f"{key}: x coordinate {x} out of range"
            assert 0 <= y <= 1, f"{key}: y coordinate {y} out of range"
    
    print("✓ Geometry data test passed")

def test_input_types():
    """Test that INPUT_TYPES includes the new parameters."""
    print("Testing INPUT_TYPES...")
    
    node = ComfyUIFaceShaper()
    input_types = node.INPUT_TYPES()
    required = input_types["required"]
    
    # Check ear parameters
    ear_params = [
        "ear_left_pos_x", "ear_left_pos_y", "ear_left_size_x", "ear_left_size_y",
        "ear_right_pos_x", "ear_right_pos_y", "ear_right_size_x", "ear_right_size_y"
    ]
    for param in ear_params:
        assert param in required, f"{param} not found in INPUT_TYPES"
        param_def = required[param]
        assert param_def[0] == "FLOAT", f"{param} should be FLOAT"
        if "pos" in param:
            assert param_def[1]["default"] == 0.0, f"{param} default should be 0.0"
            assert param_def[1]["min"] == -0.3, f"{param} min should be -0.3"
            assert param_def[1]["max"] == 0.3, f"{param} max should be 0.3"
            assert param_def[1]["step"] == 0.005, f"{param} step should be 0.005"
        else:  # size params
            assert param_def[1]["default"] == 1.0, f"{param} default should be 1.0"
            assert param_def[1]["min"] == 0.5, f"{param} min should be 0.5"
            assert param_def[1]["max"] == 2.0, f"{param} max should be 2.0"
            assert param_def[1]["step"] == 0.01, f"{param} step should be 0.01"
    
    # Check nose_tip parameters
    nose_tip_params = ["nose_tip_pos_y", "nose_tip_size_x", "nose_tip_size_y"]
    for param in nose_tip_params:
        assert param in required, f"{param} not found in INPUT_TYPES"
        param_def = required[param]
        assert param_def[0] == "FLOAT", f"{param} should be FLOAT"
        if "pos" in param:
            assert param_def[1]["default"] == 0.0, f"{param} default should be 0.0"
            assert param_def[1]["min"] == -0.2, f"{param} min should be -0.2"
            assert param_def[1]["max"] == 0.2, f"{param} max should be 0.2"
            assert param_def[1]["step"] == 0.005, f"{param} step should be 0.005"
        else:  # size params
            assert param_def[1]["default"] == 1.0, f"{param} default should be 1.0"
            assert param_def[1]["min"] == 0.5, f"{param} min should be 0.5"
            assert param_def[1]["max"] == 2.0, f"{param} max should be 2.0"
            assert param_def[1]["step"] == 0.01, f"{param} step should be 0.01"
    
    print("✓ INPUT_TYPES test passed")

def test_settings_list_length():
    """Test that SETTINGS_LIST_LENGTH is updated correctly."""
    print("Testing SETTINGS_LIST_LENGTH...")
    
    # Count parameters in order:
    # Eyes: 8, Irises: 6, Head: 4, Lips: 4, Chin: 2, Cheeks: 4
    # Ears: 8 (NEW), Eyebrows: 10, Nose: 3, Nose tip: 3 (NEW)
    # Camera: 4 (distance, pos_x, pos_y, line_thickness), Canvas: 2 (width, height)
    # Total: 8+6+4+4+2+4+8+10+3+3+4+2 = 58 actual parameters
    
    # SETTINGS_LIST_LENGTH is set to 60 for future expansion (58 used + 2 reserved)
    assert SETTINGS_LIST_LENGTH == 60, f"SETTINGS_LIST_LENGTH should be 60, got {SETTINGS_LIST_LENGTH}"
    
    print("✓ SETTINGS_LIST_LENGTH test passed")

def test_draw_face_signature():
    """Test that draw_face has all the new parameters."""
    print("Testing draw_face signature...")
    
    import inspect
    node = ComfyUIFaceShaper()
    sig = inspect.signature(node.draw_face)
    params = list(sig.parameters.keys())
    
    # Check new ear parameters
    ear_params = [
        "ear_left_pos_x", "ear_left_pos_y", "ear_left_size_x", "ear_left_size_y",
        "ear_right_pos_x", "ear_right_pos_y", "ear_right_size_x", "ear_right_size_y"
    ]
    for param in ear_params:
        assert param in params, f"{param} not found in draw_face signature"
    
    # Check new nose_tip parameters
    nose_tip_params = ["nose_tip_pos_y", "nose_tip_size_x", "nose_tip_size_y"]
    for param in nose_tip_params:
        assert param in params, f"{param} not found in draw_face signature"
    
    print("✓ draw_face signature test passed")

def test_basic_rendering():
    """Test that the node can render with default parameters."""
    print("Testing basic rendering...")
    
    node = ComfyUIFaceShaper()
    
    # Call with default parameters (all zeros/ones as appropriate)
    try:
        result = node.draw_face(
            canvas_width=512,
            canvas_height=512,
            gender="female",
            transparent_background=False,
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
            nose_tip_pos_y=0.0, nose_tip_size_x=1.0, nose_tip_size_y=1.0,
            camera_distance=1.0, camera_pos_x=0.0, camera_pos_y=0.0,
            line_thickness=2.0,
            settings_list=None
        )
        
        tensor, settings_list = result
        
        # Check tensor shape
        assert tensor.shape[0] == 1, "Batch size should be 1"
        assert tensor.shape[1] == 512, "Height should be 512"
        assert tensor.shape[2] == 512, "Width should be 512"
        assert tensor.shape[3] == 3, "Should have 3 channels (RGB)"
        
        # Check settings_list length (58 actual parameters in export list)
        assert len(settings_list) == 58, f"settings_list should have 58 elements, got {len(settings_list)}"
        
        print("✓ Basic rendering test passed")
        
    except Exception as e:
        print(f"✗ Basic rendering test failed: {e}")
        raise

if __name__ == "__main__":
    print("Running implementation tests...\n")
    
    test_geometry_data()
    test_input_types()
    test_settings_list_length()
    test_draw_face_signature()
    test_basic_rendering()
    
    print("\n✓ All tests passed!")
