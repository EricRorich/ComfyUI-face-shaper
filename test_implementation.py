#!/usr/bin/env python3
"""Test script to verify the updated ears and integrated nose tip implementation."""

import sys
sys.path.insert(0, '/home/runner/work/ComfyUI-face-shaper/ComfyUI-face-shaper')

from face_shaper import ComfyUIFaceShaper, FEMALE_FACE, SETTINGS_LIST_LENGTH

def test_geometry_data():
    """Test that the geometry data is correct."""
    print("Testing geometry data...")
    
    # Check that ear_left exists with updated coordinates (5 points from UPDATED SVG)
    assert "ear_left" in FEMALE_FACE, "ear_left not found in FEMALE_FACE"
    assert len(FEMALE_FACE["ear_left"]) == 5, f"ear_left should have 5 points, got {len(FEMALE_FACE['ear_left'])}"
    
    # Verify ear_left has updated SVG coordinates (from path184, subpath 1)
    ear_left_first = FEMALE_FACE["ear_left"][0]
    assert abs(ear_left_first[0] - 0.187500) < 0.001, f"ear_left first point x should be ~0.187500, got {ear_left_first[0]}"
    
    # Verify ear_left bbox: maxx should be < 0.5 (left side of face)
    ear_left_xs = [x for x, y in FEMALE_FACE["ear_left"]]
    assert max(ear_left_xs) < 0.5, f"ear_left maxx should be < 0.5, got {max(ear_left_xs)}"
    
    # Check that ear_right exists with updated coordinates (5 points from UPDATED SVG)
    assert "ear_right" in FEMALE_FACE, "ear_right not found in FEMALE_FACE"
    assert len(FEMALE_FACE["ear_right"]) == 5, f"ear_right should have 5 points, got {len(FEMALE_FACE['ear_right'])}"
    
    # Verify ear_right has updated SVG coordinates (from path184, subpath 2)
    ear_right_first = FEMALE_FACE["ear_right"][0]
    assert abs(ear_right_first[0] - 0.796875) < 0.001, f"ear_right first point x should be ~0.796875, got {ear_right_first[0]}"
    
    # Verify ear_right bbox: minx should be > 0.5 (right side of face)
    ear_right_xs = [x for x, y in FEMALE_FACE["ear_right"]]
    assert min(ear_right_xs) > 0.5, f"ear_right minx should be > 0.5, got {min(ear_right_xs)}"
    
    # Check that nose_tip geometry is REMOVED (no longer a separate geometry)
    assert "nose_tip" not in FEMALE_FACE, "nose_tip should be removed from FEMALE_FACE (now integrated in nose)"
    
    # Check that nose still exists with 13 points (updated from SVG path46)
    assert "nose" in FEMALE_FACE, "nose not found in FEMALE_FACE"
    assert len(FEMALE_FACE["nose"]) == 13, f"nose should have 13 points, got {len(FEMALE_FACE['nose'])}"
    
    # Verify nose bbox is roughly central (minx ~0.35-0.45, maxx ~0.55-0.65)
    nose_xs = [x for x, y in FEMALE_FACE["nose"]]
    nose_minx, nose_maxx = min(nose_xs), max(nose_xs)
    assert 0.35 <= nose_minx <= 0.45, f"nose minx should be ~0.35-0.45, got {nose_minx}"
    assert 0.55 <= nose_maxx <= 0.65, f"nose maxx should be ~0.55-0.65, got {nose_maxx}"
    
    # Verify coordinates are normalized (0-1 range)
    for key in ["ear_left", "ear_right", "nose"]:
        for x, y in FEMALE_FACE[key]:
            assert 0 <= x <= 1, f"{key}: x coordinate {x} out of range"
            assert 0 <= y <= 1, f"{key}: y coordinate {y} out of range"
    
    print("✓ Geometry data test passed")

def test_input_types():
    """Test that INPUT_TYPES includes the correct parameters."""
    print("Testing INPUT_TYPES...")
    
    node = ComfyUIFaceShaper()
    input_types = node.INPUT_TYPES()
    required = input_types["required"]
    
    # Check debug_geometry parameter
    assert "debug_geometry" in required, "debug_geometry not found in INPUT_TYPES"
    param_def = required["debug_geometry"]
    assert param_def[0] == "BOOLEAN", "debug_geometry should be BOOLEAN"
    assert param_def[1]["default"] == False, "debug_geometry default should be False"
    
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
    
    # Check nose_tip_pos_y parameter (integrated control, no separate size controls)
    assert "nose_tip_pos_y" in required, "nose_tip_pos_y not found in INPUT_TYPES"
    param_def = required["nose_tip_pos_y"]
    assert param_def[0] == "FLOAT", "nose_tip_pos_y should be FLOAT"
    assert param_def[1]["default"] == 0.0, "nose_tip_pos_y default should be 0.0"
    assert param_def[1]["min"] == -0.2, "nose_tip_pos_y min should be -0.2"
    assert param_def[1]["max"] == 0.2, "nose_tip_pos_y max should be 0.2"
    assert param_def[1]["step"] == 0.005, "nose_tip_pos_y step should be 0.005"
    
    # Verify nose_tip_size_x and nose_tip_size_y are REMOVED
    assert "nose_tip_size_x" not in required, "nose_tip_size_x should be removed from INPUT_TYPES"
    assert "nose_tip_size_y" not in required, "nose_tip_size_y should be removed from INPUT_TYPES"
    
    print("✓ INPUT_TYPES test passed")

def test_settings_list_length():
    """Test that SETTINGS_LIST_LENGTH is updated correctly."""
    print("Testing SETTINGS_LIST_LENGTH...")
    
    # Count parameters in order:
    # Eyes: 8, Irises: 6, Head: 4, Lips: 4, Chin: 2, Cheeks: 4
    # Ears: 8, Eyebrows: 10, Nose: 3, Nose tip: 1 (only pos_y, sizes removed)
    # Camera: 5 (distance, pos_x, pos_y, fov_mm, line_thickness), Canvas: 2 (width, height)
    # Total: 8+6+4+4+2+4+8+10+3+1+5+2 = 57 actual parameters
    
    # SETTINGS_LIST_LENGTH is set to 60 for future expansion (57 used + 3 reserved)
    assert SETTINGS_LIST_LENGTH == 60, f"SETTINGS_LIST_LENGTH should be 60, got {SETTINGS_LIST_LENGTH}"
    
    print("✓ SETTINGS_LIST_LENGTH test passed")

def test_draw_face_signature():
    """Test that draw_face has the correct parameters."""
    print("Testing draw_face signature...")
    
    import inspect
    node = ComfyUIFaceShaper()
    sig = inspect.signature(node.draw_face)
    params = list(sig.parameters.keys())
    
    # Check debug_geometry parameter is present
    assert "debug_geometry" in params, "debug_geometry not found in draw_face signature"
    
    # Check ear parameters are present
    ear_params = [
        "ear_left_pos_x", "ear_left_pos_y", "ear_left_size_x", "ear_left_size_y",
        "ear_right_pos_x", "ear_right_pos_y", "ear_right_size_x", "ear_right_size_y"
    ]
    for param in ear_params:
        assert param in params, f"{param} not found in draw_face signature"
    
    # Check nose_tip_pos_y parameter is present
    assert "nose_tip_pos_y" in params, "nose_tip_pos_y not found in draw_face signature"
    
    # Verify nose_tip_size_x and nose_tip_size_y are REMOVED
    assert "nose_tip_size_x" not in params, "nose_tip_size_x should be removed from draw_face signature"
    assert "nose_tip_size_y" not in params, "nose_tip_size_y should be removed from draw_face signature"
    
    print("✓ draw_face signature test passed")

def test_basic_rendering():
    """Test that the node can render with default parameters."""
    print("Testing basic rendering...")
    
    node = ComfyUIFaceShaper()
    
    # Call with default parameters (all zeros/ones as appropriate)
    # Note: Removed nose_tip_size_x and nose_tip_size_y parameters, added debug_geometry
    try:
        result = node.draw_face(
            canvas_width=512,
            canvas_height=512,
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
            nose_tip_pos_y=0.0,  # Only position control, no size controls
            camera_distance=1.0, camera_pos_x=0.0, camera_pos_y=0.0,
            fov_mm=80.0,
            line_thickness=2.0,
            settings_list=None
        )
        
        tensor, settings_list = result
        
        # Check tensor shape
        assert tensor.shape[0] == 1, "Batch size should be 1"
        assert tensor.shape[1] == 512, "Height should be 512"
        assert tensor.shape[2] == 512, "Width should be 512"
        assert tensor.shape[3] == 3, "Should have 3 channels (RGB)"
        
        # Check settings_list length (57 actual parameters in export list)
        assert len(settings_list) == 57, f"settings_list should have 57 elements, got {len(settings_list)}"
        
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
