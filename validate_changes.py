#!/usr/bin/env python3
"""
Validation script for the ComfyUI Face Shaper changes.

This script validates:
1. Updated ear geometry from new SVG
2. Removal of obsolete nose_tip geometry
3. Integration of nose tip control within nose polyline
4. Correct settings list handling

Run this without dependencies installed to validate the code structure.
"""

import sys
import ast
import re

def check_female_face_dict():
    """Validate FEMALE_FACE dictionary."""
    print("=" * 60)
    print("1. Validating FEMALE_FACE dictionary")
    print("=" * 60)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Extract FEMALE_FACE dictionary
    start = content.find('FEMALE_FACE: Dict[str, List[Tuple[float, float]]] = {')
    end = content.find('\n}', start) + 2
    female_face_code = content[start:end]
    
    # Execute it in a local namespace
    namespace = {'Dict': dict, 'List': list, 'Tuple': tuple}
    exec(female_face_code, namespace)
    FEMALE_FACE = namespace['FEMALE_FACE']
    
    # Check ear coordinates are updated
    ear_left = FEMALE_FACE.get('ear_left', [])
    ear_right = FEMALE_FACE.get('ear_right', [])
    
    if not ear_left or not ear_right:
        print("✗ FAILED: ear_left or ear_right missing")
        return False
    
    # Verify updated coordinates from new SVG
    if abs(ear_right[0][0] - 0.219108) < 0.001:
        print("✓ ear_right has updated SVG coordinates")
    else:
        print(f"✗ FAILED: ear_right[0][0] = {ear_right[0][0]}, expected ~0.219108")
        return False
    
    if abs(ear_left[0][0] - 0.045475) < 0.001:
        print("✓ ear_left has updated SVG coordinates")
    else:
        print(f"✗ FAILED: ear_left[0][0] = {ear_left[0][0]}, expected ~0.045475")
        return False
    
    # Check nose_tip is removed
    if 'nose_tip' in FEMALE_FACE:
        print("✗ FAILED: nose_tip geometry should be removed")
        return False
    else:
        print("✓ nose_tip geometry successfully removed")
    
    # Check nose still exists
    if 'nose' not in FEMALE_FACE or len(FEMALE_FACE['nose']) != 11:
        print(f"✗ FAILED: nose should have 11 points")
        return False
    else:
        print(f"✓ nose has 11 points (correct)")
    
    print()
    return True

def check_input_types():
    """Validate INPUT_TYPES parameters."""
    print("=" * 60)
    print("2. Validating INPUT_TYPES parameters")
    print("=" * 60)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Find INPUT_TYPES method
    pattern = r'def INPUT_TYPES\(cls\):.*?return\s+\{.*?\n\s+\}'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("✗ FAILED: Could not find INPUT_TYPES method")
        return False
    
    input_types_code = match.group(0)
    
    # Check nose_tip_pos_y is present with correct range
    if 'nose_tip_pos_y' not in input_types_code:
        print("✗ FAILED: nose_tip_pos_y missing")
        return False
    
    if '"min": -0.2' in input_types_code and '"max": 0.2' in input_types_code:
        print("✓ nose_tip_pos_y present with correct range (-0.2 to 0.2)")
    else:
        print("✗ FAILED: nose_tip_pos_y has incorrect range")
        return False
    
    # Check nose_tip_size_x and nose_tip_size_y are removed
    if 'nose_tip_size_x' in input_types_code or 'nose_tip_size_y' in input_types_code:
        print("✗ FAILED: nose_tip_size_x or nose_tip_size_y should be removed")
        return False
    else:
        print("✓ nose_tip_size_x and nose_tip_size_y successfully removed")
    
    # Check ear parameters are present
    ear_params = ['ear_left_pos_x', 'ear_left_pos_y', 'ear_left_size_x', 'ear_left_size_y',
                  'ear_right_pos_x', 'ear_right_pos_y', 'ear_right_size_x', 'ear_right_size_y']
    missing = [p for p in ear_params if p not in input_types_code]
    if missing:
        print(f"✗ FAILED: Missing ear parameters: {missing}")
        return False
    else:
        print("✓ All ear parameters present")
    
    print()
    return True

def check_draw_face_signature():
    """Validate draw_face method signature."""
    print("=" * 60)
    print("3. Validating draw_face signature")
    print("=" * 60)
    
    with open('face_shaper.py', 'r') as f:
        source = f.read()
    
    tree = ast.parse(source)
    
    # Find draw_face method
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'draw_face':
            params = [arg.arg for arg in node.args.args]
            
            # Check nose_tip_pos_y is present
            if 'nose_tip_pos_y' not in params:
                print("✗ FAILED: nose_tip_pos_y missing from signature")
                return False
            else:
                print("✓ nose_tip_pos_y present in signature")
            
            # Check nose_tip_size_x and nose_tip_size_y are removed
            if 'nose_tip_size_x' in params or 'nose_tip_size_y' in params:
                print("✗ FAILED: nose_tip_size parameters should be removed")
                return False
            else:
                print("✓ nose_tip_size_x and nose_tip_size_y removed from signature")
            
            # Check ear parameters
            ear_params = ['ear_left_pos_x', 'ear_left_pos_y', 'ear_left_size_x', 'ear_left_size_y',
                         'ear_right_pos_x', 'ear_right_pos_y', 'ear_right_size_x', 'ear_right_size_y']
            missing = [p for p in ear_params if p not in params]
            if missing:
                print(f"✗ FAILED: Missing ear parameters: {missing}")
                return False
            else:
                print("✓ All ear parameters present in signature")
            
            print()
            return True
    
    print("✗ FAILED: Could not find draw_face method")
    return False

def check_nose_rendering():
    """Validate nose rendering logic."""
    print("=" * 60)
    print("4. Validating nose rendering logic")
    print("=" * 60)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Find the nose rendering section
    nose_section_pattern = r'# Draw nose.*?draw\.line\(pixel_points.*?\)'
    matches = list(re.finditer(nose_section_pattern, content, re.DOTALL))
    
    if len(matches) != 1:
        print(f"✗ FAILED: Should have exactly 1 nose drawing section, found {len(matches)}")
        return False
    else:
        print("✓ Nose is drawn exactly once")
    
    nose_code = matches[0].group(0)
    
    # Check nose_tip_indices
    if 'nose_tip_indices = {3, 5, 7}' in nose_code:
        print("✓ nose_tip_indices correctly set to {3, 5, 7}")
    else:
        print("✗ FAILED: nose_tip_indices not correctly set")
        return False
    
    # Check that it applies the offset
    if 'y + nose_tip_pos_y' in nose_code:
        print("✓ nose_tip_pos_y offset applied to tip points")
    else:
        print("✗ FAILED: nose_tip_pos_y offset not applied")
        return False
    
    # Check that there's no separate nose_tip rendering
    # (excluding comments and docstrings)
    remaining = content[matches[0].end():]
    remaining_no_comments = re.sub(r'#.*', '', remaining)
    remaining_no_comments = re.sub(r'""".*?"""', '', remaining_no_comments, flags=re.DOTALL)
    
    if 'face_points["nose_tip"]' in remaining_no_comments:
        print("✗ FAILED: Separate nose_tip rendering still exists")
        return False
    else:
        print("✓ No separate nose_tip rendering")
    
    print()
    return True

def check_settings_list():
    """Validate settings list handling."""
    print("=" * 60)
    print("5. Validating settings list handling")
    print("=" * 60)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check SETTINGS_LIST_LENGTH
    match = re.search(r'SETTINGS_LIST_LENGTH = (\d+)', content)
    if match:
        length = int(match.group(1))
        if length == 60:
            print(f"✓ SETTINGS_LIST_LENGTH = 60 (correct)")
        else:
            print(f"✗ FAILED: SETTINGS_LIST_LENGTH = {length}, expected 60")
            return False
    else:
        print("✗ FAILED: Could not find SETTINGS_LIST_LENGTH")
        return False
    
    # Count parameters in settings_export
    export_match = re.search(r'settings_export = \[(.*?)\]', content, re.DOTALL)
    if export_match:
        export_content = export_match.group(1)
        params = [line.strip().rstrip(',') for line in export_content.split('\n') 
                  if line.strip() and not line.strip().startswith('#')]
        param_count = len(params)
        
        if param_count == 57:
            print(f"✓ settings_export has 57 parameters (correct)")
        else:
            print(f"⚠ settings_export has {param_count} parameters (expected 57)")
        
        # Check nose_tip_pos_y is present but not size parameters
        if 'nose_tip_pos_y' in export_content:
            print("✓ nose_tip_pos_y in settings_export")
        else:
            print("✗ FAILED: nose_tip_pos_y missing from settings_export")
            return False
        
        if 'nose_tip_size_x' in export_content or 'nose_tip_size_y' in export_content:
            print("✗ FAILED: nose_tip size parameters should be removed from settings_export")
            return False
        else:
            print("✓ nose_tip size parameters removed from settings_export")
    else:
        print("✗ FAILED: Could not find settings_export")
        return False
    
    # Check settings import indices
    if 'nose_tip_pos_y = settings_list[49]' in content:
        print("✓ nose_tip_pos_y at index 49 in import (correct)")
    else:
        print("✗ FAILED: nose_tip_pos_y should be at index 49 in import")
        return False
    
    if 'camera_distance = settings_list[50]' in content:
        print("✓ camera_distance at index 50 in import (correct)")
    else:
        print("✗ FAILED: camera_distance should be at index 50 in import")
        return False
    
    print()
    return True

def main():
    """Run all validation checks."""
    print("\nComfyUI Face Shaper - Change Validation")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("FEMALE_FACE dictionary", check_female_face_dict()))
    results.append(("INPUT_TYPES parameters", check_input_types()))
    results.append(("draw_face signature", check_draw_face_signature()))
    results.append(("Nose rendering logic", check_nose_rendering()))
    results.append(("Settings list handling", check_settings_list()))
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All validation checks passed!")
        return 0
    else:
        print("✗ Some validation checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
