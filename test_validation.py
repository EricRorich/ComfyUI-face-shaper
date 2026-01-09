#!/usr/bin/env python3
"""
Comprehensive validation script for ear rendering and reset functionality.
Tests all requirements from the problem statement.
"""

import re


def validate_svg_parser_commands():
    """Validate that the SVG parser supports all required commands."""
    print("=" * 70)
    print("Test 1: SVG Parser Command Support")
    print("=" * 70 + "\n")
    
    # Read the parser function
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Find the _parse_svg_path_to_polylines function
    if '_parse_svg_path_to_polylines' not in content:
        print("✗ FAIL: _parse_svg_path_to_polylines function not found")
        return False
    
    # Check for all required commands
    required_commands = {
        'M': ['Mm', '"M"', "'M'"],
        'm': ['Mm', '"m"', "'m'"],
        'L': ['Ll', '"L"', "'L'"],
        'l': ['Ll', '"l"', "'l'"],
        'H': ['Hh', '"H"', "'H'"],
        'h': ['Hh', '"h"', "'h'"],
        'V': ['Vv', '"V"', "'V'"],
        'v': ['Vv', '"v"', "'v'"],
        'Z': ['Zz', '"Z"', "'Z'"],
        'z': ['Zz', '"z"', "'z'"],
        'C': ['Cc', '"C"', "'C'"],
        'c': ['Cc', '"c"', "'c'"],
        'Q': ['Qq', '"Q"', "'Q'"],
        'q': ['Qq', '"q"', "'q'"],
    }
    
    missing = []
    for cmd, patterns in required_commands.items():
        found = any(pattern in content for pattern in patterns)
        if not found:
            missing.append(cmd)
    
    if missing:
        print(f"✗ FAIL: Missing support for commands: {', '.join(missing)}")
        return False
    
    print("✓ All required commands supported: M/m, L/l, H/h, V/v, Z/z, C/c, Q/q")
    
    # Check for curve sampling parameter
    if 'segments_per_curve' in content:
        # Extract default value
        match = re.search(r'segments_per_curve[:\s]*int\s*=\s*(\d+)', content)
        if match:
            segments = int(match.group(1))
            if segments >= 24:
                print(f"✓ Curve sampling uses {segments} segments (≥24 required)")
            else:
                print(f"✗ FAIL: Curve sampling uses {segments} segments (need ≥24)")
                return False
        else:
            print("⚠ Warning: Could not verify segments_per_curve default value")
    
    print()
    return True


def validate_ear_data_structure():
    """Validate that ears are stored as lists of polylines."""
    print("=" * 70)
    print("Test 2: Ear Data Structure (List of Polylines)")
    print("=" * 70 + "\n")
    
    # Read face_shaper.py
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check if FEMALE_FACE has ear_left and ear_right as lists
    # Look for pattern like: "ear_left": [ [ (coordinates) ] ]
    ear_left_match = re.search(r'"ear_left":\s*\[\s*\[', content)
    ear_right_match = re.search(r'"ear_right":\s*\[\s*\[', content)
    
    if not ear_left_match:
        print("✗ FAIL: ear_left not structured as list of polylines")
        return False
    
    if not ear_right_match:
        print("✗ FAIL: ear_right not structured as list of polylines")
        return False
    
    print("✓ ear_left stored as list of polylines: [[(x,y), ...]]")
    print("✓ ear_right stored as list of polylines: [[(x,y), ...]]")
    print()
    return True


def validate_viewbox_normalization():
    """Validate that ViewBox dimensions are used (not hardcoded 1024)."""
    print("=" * 70)
    print("Test 3: ViewBox Normalization")
    print("=" * 70 + "\n")
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check for _normalize_svg_coordinates function
    if '_normalize_svg_coordinates' not in content:
        print("✗ FAIL: _normalize_svg_coordinates function not found")
        return False
    
    # Check that it uses viewbox parameters
    if 'viewbox_w' in content and 'viewbox_h' in content:
        print("✓ Normalization function uses viewbox_w and viewbox_h")
    else:
        print("✗ FAIL: Normalization doesn't use viewBox dimensions")
        return False
    
    # Check ear coordinates are normalized correctly
    # Actual SVG viewBox is 270.93331 x 270.93331
    # Look for comments mentioning viewBox
    if '270.93331' in content:
        print("✓ Ear coordinates reference correct viewBox (270.93331)")
    else:
        print("⚠ Warning: ViewBox dimension 270.93331 not found in comments")
    
    print()
    return True


def validate_bounding_boxes():
    """Validate that ear bounding boxes are reasonable."""
    print("=" * 70)
    print("Test 4: Ear Bounding Box Validation")
    print("=" * 70 + "\n")
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Extract ear_left coordinates
    ear_left_match = re.search(r'"ear_left":\s*\[\s*\[(.*?)\]\s*\]', content, re.DOTALL)
    if not ear_left_match:
        print("✗ FAIL: Could not extract ear_left coordinates")
        return False
    
    ear_left_coords_text = ear_left_match.group(1)
    # Parse coordinates
    coord_pattern = r'\((\d+\.\d+),\s*(\d+\.\d+)\)'
    left_coords = [(float(m.group(1)), float(m.group(2))) 
                   for m in re.finditer(coord_pattern, ear_left_coords_text)]
    
    if not left_coords:
        print("✗ FAIL: Could not parse ear_left coordinates")
        return False
    
    left_xs = [x for x, y in left_coords]
    left_minx, left_maxx = min(left_xs), max(left_xs)
    
    print(f"ear_left: minx={left_minx:.6f}, maxx={left_maxx:.6f}")
    
    if left_maxx >= 0.5:
        print(f"✗ FAIL: Left ear maxx should be < 0.5, got {left_maxx:.6f}")
        return False
    
    print("✓ Left ear correctly positioned (maxx < 0.5)")
    
    # Extract ear_right coordinates
    ear_right_match = re.search(r'"ear_right":\s*\[\s*\[(.*?)\]\s*\]', content, re.DOTALL)
    if not ear_right_match:
        print("✗ FAIL: Could not extract ear_right coordinates")
        return False
    
    ear_right_coords_text = ear_right_match.group(1)
    right_coords = [(float(m.group(1)), float(m.group(2))) 
                    for m in re.finditer(coord_pattern, ear_right_coords_text)]
    
    if not right_coords:
        print("✗ FAIL: Could not parse ear_right coordinates")
        return False
    
    right_xs = [x for x, y in right_coords]
    right_minx, right_maxx = min(right_xs), max(right_xs)
    
    print(f"ear_right: minx={right_minx:.6f}, maxx={right_maxx:.6f}")
    
    if right_minx <= 0.5:
        print(f"✗ FAIL: Right ear minx should be > 0.5, got {right_minx:.6f}")
        return False
    
    print("✓ Right ear correctly positioned (minx > 0.5)")
    print()
    return True


def validate_ear_rendering_code():
    """Validate that ear rendering handles multiple subpaths."""
    print("=" * 70)
    print("Test 5: Ear Rendering Implementation")
    print("=" * 70 + "\n")
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check for proper subpath iteration
    if 'for polyline in ear_polylines' in content or 'for polyline in ear_left' in content:
        print("✓ Ear rendering iterates over subpaths")
    else:
        print("✗ FAIL: Ear rendering doesn't iterate over subpaths")
        return False
    
    # Check for transform application
    if 'transform_polygon' in content:
        print("✓ Transform pipeline applied to ear polylines")
    else:
        print("✗ FAIL: Transform not applied to ears")
        return False
    
    # Check for to_pixel conversion
    if 'to_pixel' in content:
        print("✓ Pixel conversion applied")
    else:
        print("✗ FAIL: to_pixel conversion not found")
        return False
    
    # Check that closed paths are handled
    # The Z command should add the starting point at the end
    if 'subpath_start' in content:
        print("✓ Closed path handling implemented (subpath_start tracking)")
    else:
        print("⚠ Warning: subpath_start not found, closed paths may not work correctly")
    
    print()
    return True


def validate_debug_ears_flag():
    """Validate that debug_ears parameter exists and defaults to False."""
    print("=" * 70)
    print("Test 6: debug_ears Flag")
    print("=" * 70 + "\n")
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check for debug_ears in INPUT_TYPES
    if '"debug_ears"' not in content:
        print("✗ FAIL: debug_ears parameter not found in INPUT_TYPES")
        return False
    
    # Check default is False
    if '"debug_ears": ("BOOLEAN", {"default": False})' in content:
        print("✓ debug_ears parameter exists with default False")
    else:
        print("✗ FAIL: debug_ears default is not False")
        return False
    
    # Check for debug visualization code
    if 'if debug_ears:' in content:
        print("✓ Debug visualization code implemented")
    else:
        print("✗ FAIL: Debug visualization code not found")
        return False
    
    # Check for alternate colors
    if '(255, 0, 0)' in content and '(0, 0, 255)' in content:
        print("✓ Alternate colors for debug (red and blue)")
    else:
        print("⚠ Warning: Debug colors not found or not red/blue")
    
    # Check for logging
    if 'print(' in content and 'ear_' in content:
        print("✓ Debug logging implemented")
    else:
        print("⚠ Warning: Debug logging may not be implemented")
    
    print()
    return True


def validate_reset_button():
    """Validate that reset button includes all parameters."""
    print("=" * 70)
    print("Test 7: Reset Button Comprehensive Coverage")
    print("=" * 70 + "\n")
    
    with open('web/js/faceShaperReset.js', 'r') as f:
        js_content = f.read()
    
    # Check for comprehensive parameter list
    required_params = [
        'debug_ears', 'debug_geometry', 'nose_tip_pos_y',
        'ear_left_pos_x', 'ear_left_pos_y', 'ear_left_size_x', 'ear_left_size_y',
        'ear_right_pos_x', 'ear_right_pos_y', 'ear_right_size_x', 'ear_right_size_y',
        'camera_distance', 'camera_pos_x', 'camera_pos_y'
    ]
    
    missing_params = []
    for param in required_params:
        if f'"{param}"' not in js_content:
            missing_params.append(param)
    
    if missing_params:
        print(f"✗ FAIL: Missing parameters in reset: {', '.join(missing_params)}")
        return False
    
    print(f"✓ All {len(required_params)} key parameters present in reset defaults")
    
    # Check for settings_list disconnection
    if 'settings_list' in js_content and 'disconnect' in js_content.lower():
        print("✓ settings_list disconnection implemented")
    else:
        print("⚠ Warning: settings_list disconnection may not be implemented")
    
    # Check for graph refresh
    if 'setDirtyCanvas' in js_content:
        print("✓ Graph refresh implemented (setDirtyCanvas)")
    else:
        print("✗ FAIL: Graph refresh not implemented")
        return False
    
    # Check for prompt queueing
    if 'queuePrompt' in js_content:
        print("✓ Prompt queueing implemented")
    else:
        print("⚠ Warning: Prompt queueing may not be implemented")
    
    # Check for dynamic widget iteration
    if 'for (const widget of this.widgets)' in js_content:
        print("✓ Dynamic widget iteration (future-proof)")
    else:
        print("⚠ Warning: Reset may not iterate all widgets dynamically")
    
    print()
    return True


def validate_no_breaking_changes():
    """Validate that no parameters were renamed and compatibility maintained."""
    print("=" * 70)
    print("Test 8: Backward Compatibility")
    print("=" * 70 + "\n")
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check that existing parameters still exist
    existing_params = [
        'canvas_width', 'canvas_height', 'gender', 'transparent_background',
        'eye_left_size_x', 'eye_right_size_x', 'iris_left_size', 'iris_right_size',
        'outer_head_size_x', 'lips_pos_y', 'nose_pos_y', 'camera_distance', 'fov_mm'
    ]
    
    missing = []
    for param in existing_params:
        if f'"{param}"' not in content:
            missing.append(param)
    
    if missing:
        print(f"✗ FAIL: Missing existing parameters: {', '.join(missing)}")
        return False
    
    print(f"✓ All {len(existing_params)} existing core parameters preserved")
    
    # Check NODE_DISPLAY_NAME_MAPPINGS unchanged
    if '"Face Shaper"' in content:
        print("✓ Display name unchanged: 'Face Shaper'")
    else:
        print("✗ FAIL: Display name may have changed")
        return False
    
    # Check CATEGORY unchanged
    if 'CATEGORY = "face"' in content:
        print("✓ Category unchanged: 'face'")
    else:
        print("✗ FAIL: Category may have changed")
        return False
    
    print()
    return True


def main():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE VALIDATION: Ear Rendering & Reset Fixes")
    print("=" * 70 + "\n")
    
    tests = [
        ("SVG Parser Commands", validate_svg_parser_commands),
        ("Ear Data Structure", validate_ear_data_structure),
        ("ViewBox Normalization", validate_viewbox_normalization),
        ("Bounding Box Validation", validate_bounding_boxes),
        ("Ear Rendering Code", validate_ear_rendering_code),
        ("debug_ears Flag", validate_debug_ears_flag),
        ("Reset Button", validate_reset_button),
        ("Backward Compatibility", validate_no_breaking_changes),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"✗ EXCEPTION in {name}: {e}\n")
            results.append((name, False))
    
    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70 + "\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("✓✓✓ ALL VALIDATION TESTS PASSED ✓✓✓")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("✗✗✗ SOME VALIDATION TESTS FAILED ✗✗✗")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
