#!/usr/bin/env python3
"""
Validation script to verify complete removal of ear geometry and controls.

This script validates that:
1. Ear geometry removed from FEMALE_FACE dictionary
2. Ear parameters removed from INPUT_TYPES
3. Ear parameters removed from draw_face signature
4. Ear rendering code removed
5. Ear parameters removed from settings import/export
6. Ear parameters removed from web extension
"""

import ast
import re
import sys


def check_female_face_dict():
    """Validate FEMALE_FACE dictionary has no ear geometry."""
    print("=" * 70)
    print("1. Validating FEMALE_FACE dictionary")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Find FEMALE_FACE dictionary
    female_face_match = re.search(r'FEMALE_FACE.*?\n\}', content, re.DOTALL)
    if not female_face_match:
        print("✗ FAILED: Could not find FEMALE_FACE dictionary")
        return False
    
    female_face_str = female_face_match.group(0)
    
    # Check that ear geometry is removed
    if '"ear_left"' in female_face_str or '"ear_right"' in female_face_str:
        print("✗ FAILED: Ear geometry still present in FEMALE_FACE")
        return False
    
    print("✓ Ear geometry successfully removed from FEMALE_FACE")
    print()
    return True


def check_input_types():
    """Validate INPUT_TYPES has no ear parameters."""
    print("=" * 70)
    print("2. Validating INPUT_TYPES parameters")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Find INPUT_TYPES method
    input_types_match = re.search(r'def INPUT_TYPES\(cls\):.*?return\s+\{.*?\n\s+\}', 
                                   content, re.DOTALL)
    if not input_types_match:
        print("✗ FAILED: Could not find INPUT_TYPES method")
        return False
    
    input_types_str = input_types_match.group(0)
    
    # Check for ear parameters
    ear_count = input_types_str.count('ear_')
    debug_ears_count = input_types_str.count('debug_ears')
    
    if ear_count > 0:
        print(f"✗ FAILED: Found {ear_count} ear_ parameters in INPUT_TYPES")
        return False
    
    if debug_ears_count > 0:
        print(f"✗ FAILED: Found debug_ears parameter in INPUT_TYPES")
        return False
    
    print("✓ All ear parameters removed from INPUT_TYPES")
    print("✓ debug_ears parameter removed from INPUT_TYPES")
    print()
    return True


def check_draw_face_signature():
    """Validate draw_face signature has no ear parameters."""
    print("=" * 70)
    print("3. Validating draw_face method signature")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        source = f.read()
    
    tree = ast.parse(source)
    
    # Find draw_face method
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'draw_face':
            params = [arg.arg for arg in node.args.args]
            
            # Check for ear parameters
            ear_params = [p for p in params if 'ear_' in p]
            has_debug_ears = 'debug_ears' in params
            
            if ear_params:
                print(f"✗ FAILED: Found ear parameters in signature: {ear_params}")
                return False
            
            if has_debug_ears:
                print(f"✗ FAILED: Found debug_ears in signature")
                return False
            
            print(f"✓ All ear parameters removed from draw_face signature")
            print(f"✓ debug_ears removed from signature")
            print(f"  Total parameters: {len(params)}")
            print()
            return True
    
    print("✗ FAILED: Could not find draw_face method")
    return False


def check_ear_rendering_code():
    """Validate ear rendering code is removed."""
    print("=" * 70)
    print("4. Validating ear rendering code removal")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check for ear drawing code patterns
    ear_drawing_patterns = [
        r'if\s+["\']ear_left["\'].*?draw\.line',
        r'if\s+["\']ear_right["\'].*?draw\.line',
        r'ear_polylines\s*=',
        r'if\s+debug_ears:',
    ]
    
    found_patterns = []
    for pattern in ear_drawing_patterns:
        if re.search(pattern, content, re.DOTALL):
            found_patterns.append(pattern)
    
    if found_patterns:
        print(f"✗ FAILED: Found ear rendering code patterns:")
        for pattern in found_patterns:
            print(f"  - {pattern}")
        return False
    
    print("✓ Ear rendering code successfully removed")
    print()
    return True


def check_settings_list():
    """Validate settings list handling has no ear parameters."""
    print("=" * 70)
    print("5. Validating settings list import/export")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check settings import section
    import_section = re.search(r'if settings_list is not None.*?line_thickness = settings_list\[\d+\]',
                               content, re.DOTALL)
    if import_section:
        import_str = import_section.group(0)
        ear_in_import = import_str.count('ear_')
        
        if ear_in_import > 0:
            print(f"✗ FAILED: Found {ear_in_import} ear references in settings import")
            return False
        
        print("✓ Ear parameters removed from settings import")
    else:
        print("⚠ WARNING: Could not find settings import section")
    
    # Check settings export section
    export_match = re.search(r'settings_export = \[(.*?)\]', content, re.DOTALL)
    if export_match:
        export_str = export_match.group(0)
        ear_in_export = export_str.count('ear_')
        
        if ear_in_export > 0:
            print(f"✗ FAILED: Found {ear_in_export} ear references in settings export")
            return False
        
        print("✓ Ear parameters removed from settings export")
    else:
        print("✗ FAILED: Could not find settings export section")
        return False
    
    # Verify SETTINGS_LIST_LENGTH comment reflects new parameter count
    settings_length_match = re.search(r'# Set to 60.*?currently (\d+) parameters', content)
    if settings_length_match:
        param_count = int(settings_length_match.group(1))
        expected_count = 48  # 57 - 9 ear parameters
        
        if param_count == expected_count:
            print(f"✓ SETTINGS_LIST_LENGTH comment updated: {param_count} parameters")
        else:
            print(f"✗ FAILED: Parameter count is {param_count}, expected {expected_count}")
            return False
    else:
        print("⚠ WARNING: Could not verify SETTINGS_LIST_LENGTH comment")
    
    print()
    return True


def check_web_extension():
    """Validate web extension has no ear parameters."""
    print("=" * 70)
    print("6. Validating web extension (faceShaperReset.js)")
    print("=" * 70)
    
    try:
        with open('web/js/faceShaperReset.js', 'r') as f:
            js_content = f.read()
        
        # Check for ear parameters
        ear_count = js_content.count('ear_')
        debug_ears_count = js_content.count('debug_ears')
        
        if ear_count > 0:
            print(f"✗ FAILED: Found {ear_count} ear_ references in JS")
            return False
        
        if debug_ears_count > 0:
            print(f"✗ FAILED: Found debug_ears in JS")
            return False
        
        print("✓ All ear parameters removed from web extension")
        print()
        return True
        
    except FileNotFoundError:
        print("✗ FAILED: Could not find web/js/faceShaperReset.js")
        return False


def check_debug_geometry():
    """Validate debug_geometry output has no ear references."""
    print("=" * 70)
    print("7. Validating debug_geometry output")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Find debug_geometry section
    debug_section = re.search(r'if debug_geometry:.*?print\("=+"\)', content, re.DOTALL)
    if debug_section:
        debug_str = debug_section.group(0)
        
        if 'ear_left' in debug_str or 'ear_right' in debug_str:
            print("✗ FAILED: Ear references still in debug_geometry output")
            return False
        
        print("✓ Ear references removed from debug_geometry output")
    else:
        print("⚠ WARNING: Could not find debug_geometry section")
    
    print()
    return True


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("VALIDATION: Complete Ear Removal from ComfyUI Face Shaper")
    print("=" * 70 + "\n")
    
    tests = [
        ("FEMALE_FACE dictionary", check_female_face_dict),
        ("INPUT_TYPES parameters", check_input_types),
        ("draw_face signature", check_draw_face_signature),
        ("Ear rendering code", check_ear_rendering_code),
        ("Settings list handling", check_settings_list),
        ("Web extension", check_web_extension),
        ("Debug geometry output", check_debug_geometry),
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
        print("\nEar geometry and controls have been completely removed.")
        print("The node now has simplified controls with no ear-related UI.")
        return 0
    else:
        print("\n" + "=" * 70)
        print("✗✗✗ SOME VALIDATION TESTS FAILED ✗✗✗")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
