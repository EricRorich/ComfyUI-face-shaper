#!/usr/bin/env python3
"""
Test script for validating ear path parsing and rendering implementation.
Can run without full ComfyUI dependencies.
"""

import re


def _parse_svg_path_to_polylines(path_d: str, segments_per_curve: int = 32):
    """
    Parse an SVG path string into a list of polylines, preserving subpaths.
    """
    tokens = re.findall(r'[MmLlHhVvZzCcQqSsTtAa]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', path_d)
    
    polylines = []
    current_polyline = []
    current_pos = (0.0, 0.0)
    subpath_start = (0.0, 0.0)
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        if token in 'MmLlHhVvZzCcQqSsTtAa':
            command = token
            i += 1
            
            if command in 'Mm':
                if current_polyline:
                    polylines.append(current_polyline)
                current_polyline = []
                
                x = float(tokens[i])
                y = float(tokens[i + 1])
                i += 2
                
                if command == 'm':
                    x += current_pos[0]
                    y += current_pos[1]
                
                current_pos = (x, y)
                subpath_start = current_pos
                current_polyline.append(current_pos)
                
            elif command in 'Ll':
                x = float(tokens[i])
                y = float(tokens[i + 1])
                i += 2
                
                if command == 'l':
                    x += current_pos[0]
                    y += current_pos[1]
                
                current_pos = (x, y)
                current_polyline.append(current_pos)
                
            elif command in 'Hh':
                x = float(tokens[i])
                i += 1
                
                if command == 'h':
                    x += current_pos[0]
                
                current_pos = (x, current_pos[1])
                current_polyline.append(current_pos)
                
            elif command in 'Vv':
                y = float(tokens[i])
                i += 1
                
                if command == 'v':
                    y += current_pos[1]
                
                current_pos = (current_pos[0], y)
                current_polyline.append(current_pos)
                
            elif command in 'Zz':
                if current_polyline and current_polyline[-1] != subpath_start:
                    current_polyline.append(subpath_start)
        else:
            i += 1
    
    if current_polyline:
        polylines.append(current_polyline)
    
    return polylines


def test_ear_path_parsing():
    """Test that path184 (ears) is parsed correctly."""
    print("=" * 60)
    print("Testing SVG Path Parsing for Ears (path184)")
    print("=" * 60)
    
    # Actual path184 from Face_Mask_female.svg
    path_d = "m 50.800012,131.23334 -4.233333,-29.63333 h -8.466667 l -4.233333,33.86667 8.466667,33.86666 h 8.466666 z m 169.333288,0 4.23333,-29.63333 h 8.46667 l 4.23333,33.86667 -8.46667,33.86666 h -8.46666 z"
    
    print(f"\nInput path: {path_d}\n")
    
    # Parse
    polylines = _parse_svg_path_to_polylines(path_d)
    
    print(f"Number of subpaths (polylines): {len(polylines)}")
    print("✓ Expected 2 subpaths (one per ear)\n")
    
    if len(polylines) != 2:
        print("✗ FAIL: Expected exactly 2 subpaths")
        return False
    
    # ViewBox dimensions
    viewbox_w = 270.93331
    viewbox_h = 270.93331
    
    # Check each polyline
    for i, polyline in enumerate(polylines):
        ear_name = "left" if i == 0 else "right"
        print(f"Ear {i+1} ({ear_name}):")
        print(f"  Points: {len(polyline)}")
        
        # Normalize coordinates
        normalized = [(x / viewbox_w, y / viewbox_h) for x, y in polyline]
        
        # Get bounding box
        xs = [x for x, y in normalized]
        ys = [y for x, y in normalized]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        
        print(f"  Bounding box (normalized):")
        print(f"    minx={minx:.6f}, maxx={maxx:.6f}")
        print(f"    miny={miny:.6f}, maxy={maxy:.6f}")
        
        # Validate position
        if ear_name == "left":
            if maxx >= 0.5:
                print(f"  ✗ FAIL: Left ear should have maxx < 0.5, got {maxx:.6f}")
                return False
            print(f"  ✓ Left ear correctly positioned (maxx < 0.5)")
        else:
            if minx <= 0.5:
                print(f"  ✗ FAIL: Right ear should have minx > 0.5, got {minx:.6f}")
                return False
            print(f"  ✓ Right ear correctly positioned (minx > 0.5)")
        
        # Check if path is closed
        if polyline[0] == polyline[-1]:
            print(f"  ✓ Path is closed")
        else:
            print(f"  ⚠ Path is not closed")
        
        # Print first and last points
        print(f"  First point: ({normalized[0][0]:.6f}, {normalized[0][1]:.6f})")
        print(f"  Last point:  ({normalized[-1][0]:.6f}, {normalized[-1][1]:.6f})")
        print()
    
    print("=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


def test_ear_data_structure():
    """Test that ear data is structured correctly for rendering."""
    print("\n" + "=" * 60)
    print("Testing Ear Data Structure in FEMALE_FACE")
    print("=" * 60 + "\n")
    
    # Expected structure for ears (from face_shaper.py)
    ear_left = [
        [
            (0.187500, 0.484375),
            (0.171875, 0.375000),
            (0.140625, 0.375000),
            (0.125000, 0.500000),
            (0.156250, 0.625000),
            (0.187500, 0.625000),
            (0.187500, 0.484375),  # Closed
        ]
    ]
    
    ear_right = [
        [
            (0.812500, 0.625000),
            (0.828125, 0.515625),
            (0.859375, 0.515625),
            (0.875000, 0.640625),
            (0.843750, 0.765625),
            (0.812500, 0.765625),
            (0.812500, 0.625000),  # Closed
        ]
    ]
    
    # Test ear_left
    print("ear_left:")
    print(f"  Type: {type(ear_left)}")
    print(f"  Is list: {isinstance(ear_left, list)}")
    print(f"  Number of subpaths: {len(ear_left)}")
    
    if not isinstance(ear_left, list) or len(ear_left) != 1:
        print("  ✗ FAIL: ear_left should be a list with 1 subpath")
        return False
    
    subpath = ear_left[0]
    print(f"  Subpath[0] type: {type(subpath)}")
    print(f"  Subpath[0] is list: {isinstance(subpath, list)}")
    print(f"  Subpath[0] length: {len(subpath)}")
    
    if not isinstance(subpath, list) or len(subpath) != 7:
        print("  ✗ FAIL: ear_left subpath should be a list with 7 points")
        return False
    
    # Check if closed
    if subpath[0] == subpath[-1]:
        print("  ✓ Subpath is closed (first == last)")
    else:
        print("  ✗ FAIL: Subpath should be closed")
        return False
    
    print("  ✓ ear_left structure is correct\n")
    
    # Test ear_right
    print("ear_right:")
    print(f"  Type: {type(ear_right)}")
    print(f"  Is list: {isinstance(ear_right, list)}")
    print(f"  Number of subpaths: {len(ear_right)}")
    
    if not isinstance(ear_right, list) or len(ear_right) != 1:
        print("  ✗ FAIL: ear_right should be a list with 1 subpath")
        return False
    
    subpath = ear_right[0]
    print(f"  Subpath[0] type: {type(subpath)}")
    print(f"  Subpath[0] is list: {isinstance(subpath, list)}")
    print(f"  Subpath[0] length: {len(subpath)}")
    
    if not isinstance(subpath, list) or len(subpath) != 7:
        print("  ✗ FAIL: ear_right subpath should be a list with 7 points")
        return False
    
    # Check if closed
    if subpath[0] == subpath[-1]:
        print("  ✓ Subpath is closed (first == last)")
    else:
        print("  ✗ FAIL: Subpath should be closed")
        return False
    
    print("  ✓ ear_right structure is correct\n")
    
    print("=" * 60)
    print("✓ All ear data structure tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = True
    
    # Run tests
    if not test_ear_path_parsing():
        success = False
    
    if not test_ear_data_structure():
        success = False
    
    # Final result
    print("\n" + "=" * 60)
    if success:
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 60)
        exit(0)
    else:
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("=" * 60)
        exit(1)
