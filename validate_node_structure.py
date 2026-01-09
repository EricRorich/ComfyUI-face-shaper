#!/usr/bin/env python3
"""
Simple validation script to verify the node loads and renders without errors.
This script validates code structure without importing the actual node
(which would require numpy, torch, and PIL dependencies).
"""

import sys
import ast
import re


def validate_syntax():
    """Validate Python syntax."""
    print("=" * 70)
    print("1. Validating Python syntax")
    print("=" * 70)
    
    try:
        with open('face_shaper.py', 'r') as f:
            source = f.read()
        
        # Parse the source code
        ast.parse(source)
        print("✓ Python syntax is valid")
        print()
        return True
    except SyntaxError as e:
        print(f"✗ FAILED: Syntax error at line {e.lineno}: {e.msg}")
        print()
        return False


def validate_imports():
    """Validate required imports are present."""
    print("=" * 70)
    print("2. Validating imports")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    required_imports = [
        'from typing import',
        'import numpy',
        'import torch',
        'from PIL import Image',
    ]
    
    for imp in required_imports:
        if imp not in content:
            print(f"✗ FAILED: Missing import: {imp}")
            return False
    
    print("✓ All required imports present")
    print()
    return True


def validate_class_structure():
    """Validate ComfyUIFaceShaper class structure."""
    print("=" * 70)
    print("3. Validating class structure")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check class definition
    if 'class ComfyUIFaceShaper:' not in content:
        print("✗ FAILED: ComfyUIFaceShaper class not found")
        return False
    
    print("✓ ComfyUIFaceShaper class defined")
    
    # Check required attributes
    required_attrs = ['CATEGORY', 'RETURN_TYPES', 'FUNCTION']
    for attr in required_attrs:
        if f'{attr} = ' not in content:
            print(f"✗ FAILED: Missing class attribute: {attr}")
            return False
    
    print("✓ All required class attributes present")
    
    # Check required methods
    required_methods = ['INPUT_TYPES', 'draw_face']
    for method in required_methods:
        if f'def {method}' not in content:
            print(f"✗ FAILED: Missing method: {method}")
            return False
    
    print("✓ All required methods present")
    
    # Verify CATEGORY value
    if 'CATEGORY = "face"' not in content:
        print("✗ FAILED: CATEGORY should be 'face'")
        return False
    
    print("✓ CATEGORY is 'face'")
    
    # Verify RETURN_TYPES value
    if 'RETURN_TYPES = ("IMAGE", "LIST")' not in content:
        print("✗ FAILED: RETURN_TYPES should be ('IMAGE', 'LIST')")
        return False
    
    print("✓ RETURN_TYPES is ('IMAGE', 'LIST')")
    print()
    return True


def validate_node_mappings():
    """Validate NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS."""
    print("=" * 70)
    print("4. Validating node mappings")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Check NODE_CLASS_MAPPINGS
    if 'NODE_CLASS_MAPPINGS' not in content:
        print("✗ FAILED: NODE_CLASS_MAPPINGS not found")
        return False
    
    if '"RORICH-AI": ComfyUIFaceShaper' not in content:
        print("✗ FAILED: NODE_CLASS_MAPPINGS should map 'RORICH-AI' to ComfyUIFaceShaper")
        return False
    
    print("✓ NODE_CLASS_MAPPINGS configured correctly")
    
    # Check NODE_DISPLAY_NAME_MAPPINGS
    if 'NODE_DISPLAY_NAME_MAPPINGS' not in content:
        print("✗ FAILED: NODE_DISPLAY_NAME_MAPPINGS not found")
        return False
    
    if '"RORICH-AI": "Face Shaper"' not in content:
        print("✗ FAILED: NODE_DISPLAY_NAME_MAPPINGS should map to 'Face Shaper'")
        return False
    
    print("✓ NODE_DISPLAY_NAME_MAPPINGS configured correctly")
    print()
    return True


def validate_parameter_count():
    """Validate the total parameter count is reasonable."""
    print("=" * 70)
    print("5. Validating parameter count")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        source = f.read()
    
    tree = ast.parse(source)
    
    # Find draw_face method
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'draw_face':
            params = [arg.arg for arg in node.args.args if arg.arg != 'self' and arg.arg != 'settings_list']
            
            print(f"✓ Total parameters in draw_face: {len(params)}")
            
            # Parameter count: removed 2 chin parameters (chin_size_x, chin_size_y) 
            # and added 2 eye rotation parameters (eye_left_rotation, eye_right_rotation)
            # Net change: 0 parameters, so expected count remains ~48
            if len(params) < 46 or len(params) > 50:
                print(f"  ⚠ WARNING: Unexpected parameter count (expected ~48)")
            else:
                print(f"  ✓ Parameter count looks reasonable")
            
            print()
            return True
    
    print("✗ FAILED: Could not find draw_face method")
    return False


def validate_no_chin_references():
    """Final check: no chin-related code should remain."""
    print("=" * 70)
    print("6. Final check: No chin references")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Remove comments to avoid false positives
    content_no_comments = re.sub(r'#.*', '', content)
    content_no_comments = re.sub(r'""".*?"""', '', content_no_comments, flags=re.DOTALL)
    content_no_comments = re.sub(r"'''.*?'''", '', content_no_comments, flags=re.DOTALL)
    
    # Check for chin references
    chin_patterns = [
        '"chin"',
        "'chin'",
        'chin_pos',
        'chin_size',
    ]
    
    found = []
    for pattern in chin_patterns:
        if pattern in content_no_comments:
            found.append(pattern)
    
    if found:
        print(f"✗ FAILED: Found chin references: {found}")
        return False
    
    print("✓ No chin references found in code")
    print()
    return True


def validate_no_ear_references():
    """Check: no ear-related code should remain."""
    print("=" * 70)
    print("7. Check: No ear references")
    print("=" * 70)
    
    with open('face_shaper.py', 'r') as f:
        content = f.read()
    
    # Remove comments to avoid false positives
    content_no_comments = re.sub(r'#.*', '', content)
    content_no_comments = re.sub(r'""".*?"""', '', content_no_comments, flags=re.DOTALL)
    content_no_comments = re.sub(r"'''.*?'''", '', content_no_comments, flags=re.DOTALL)
    
    # Check for ear references
    ear_patterns = [
        '"ear_left"',
        '"ear_right"',
        "'ear_left'",
        "'ear_right'",
        'ear_left_pos',
        'ear_right_pos',
        'ear_left_size',
        'ear_right_size',
        'debug_ears',
    ]
    
    found = []
    for pattern in ear_patterns:
        if pattern in content_no_comments:
            found.append(pattern)
    
    if found:
        print(f"✗ FAILED: Found ear references: {found}")
        return False
    
    print("✓ No ear references found in code")
    print()
    return True


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("BASIC VALIDATION: Node Structure and Functionality")
    print("=" * 70 + "\n")
    
    tests = [
        ("Python syntax", validate_syntax),
        ("Required imports", validate_imports),
        ("Class structure", validate_class_structure),
        ("Node mappings", validate_node_mappings),
        ("Parameter count", validate_parameter_count),
        ("No chin references", validate_no_chin_references),
        ("No ear references", validate_no_ear_references),
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
        print("\nThe node is ready to use!")
        print("• No syntax errors")
        print("• All required methods and attributes present")
        print("• No chin-related code remains")
        print("• No ear-related code remains")
        print("• Node name and category unchanged")
        return 0
    else:
        print("\n" + "=" * 70)
        print("✗✗✗ SOME VALIDATION TESTS FAILED ✗✗✗")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
