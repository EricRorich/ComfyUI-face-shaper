"""
Refined implementation of the ComfyUI Face Shaper custom node.

This module implements a custom node that draws a stylized facial mask based on
SVG‑derived coordinates extracted from Face_Mask_female.svg (1024×1024). Users 
can adjust the positions and sizes of distinct facial features including:
outer head outline, eyes, irises, eyebrows, nose (single merged object with 
integrated tip control), ears (left and right), lips (upper and lower with 
direction-specific scaling), chin, and cheeks. All coordinates are normalized 
to [0-1] range. Users can select a gender preset (currently both genders use 
the same coordinates), change the canvas size and camera distance, and control 
the line thickness. The output is black lines on either a white or transparent 
background as a tensor compatible with ComfyUI workflows.

Key improvements in this version:
- Updated ear geometry with refreshed SVG-derived coordinates
- Nose tip now integrated within nose polyline (no separate geometry)
- nose_tip_pos_y controls only the 3 middle-most, lowest-Y points of nose
- Removed obsolete nose_tip size controls (nose_tip_size_x, nose_tip_size_y)
- Lips split into upper and lower with independent y-scaling
- Direction-specific lip scaling keeps mouth midline anchored
- Nose simplified to 3 parameters: pos_y, size_x, size_y + integrated tip control
- All position parameters default to 0.0 (zero offsets by default)
- Per-feature scaling controls prevent distortion across unrelated features
- Camera translation controls (camera_pos_x, camera_pos_y) for panning the view
- Settings export/import via LIST output and input for saving/loading configurations
- Iris positions based on SVG viewBox coordinates for accurate defaults
- Finer iris position controls (2x finer offsets)
- Reset to defaults via client-side web extension button
- Maintains proper node structure with CATEGORY="face", INPUT_TYPES, RETURN_TYPES=("IMAGE", "LIST")
- Optional transparent background support for alpha-aware workflows
"""

from typing import Dict, List, Tuple
import math
import re

import numpy as np
import torch
from PIL import Image, ImageDraw


def _parse_svg_path_to_polylines(path_d: str, segments_per_curve: int = 32) -> List[List[Tuple[float, float]]]:
    """
    Parse an SVG path string into a list of polylines, preserving subpaths.
    
    Supports M/m, L/l, H/h, V/v, Z/z, C/c, Q/q commands.
    Curves (C, Q) are sampled to polylines with specified segments.
    
    Args:
        path_d: SVG path 'd' attribute string
        segments_per_curve: Number of line segments to use per curve (≥24 recommended)
        
    Returns:
        List of polylines, where each polyline is a list of (x, y) tuples.
        Each 'M' command starts a new subpath/polyline.
    """
    # Tokenize the path string - split on command letters while keeping them
    tokens = re.findall(r'[MmLlHhVvZzCcQqSsTtAa]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', path_d)
    
    polylines = []
    current_polyline = []
    current_pos = (0.0, 0.0)
    subpath_start = (0.0, 0.0)
    last_command = None
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        # Check if this is a command letter
        if token in 'MmLlHhVvZzCcQqSsTtAa':
            command = token
            i += 1
            
            # Process command
            if command in 'Mm':  # Move
                # M/m starts a new subpath
                if current_polyline:
                    polylines.append(current_polyline)
                current_polyline = []
                
                # Get coordinates
                x = float(tokens[i])
                y = float(tokens[i + 1])
                i += 2
                
                if command == 'm':  # relative
                    x += current_pos[0]
                    y += current_pos[1]
                
                current_pos = (x, y)
                subpath_start = current_pos
                current_polyline.append(current_pos)
                
            elif command in 'Ll':  # Line to
                x = float(tokens[i])
                y = float(tokens[i + 1])
                i += 2
                
                if command == 'l':  # relative
                    x += current_pos[0]
                    y += current_pos[1]
                
                current_pos = (x, y)
                current_polyline.append(current_pos)
                
            elif command in 'Hh':  # Horizontal line
                x = float(tokens[i])
                i += 1
                
                if command == 'h':  # relative
                    x += current_pos[0]
                
                current_pos = (x, current_pos[1])
                current_polyline.append(current_pos)
                
            elif command in 'Vv':  # Vertical line
                y = float(tokens[i])
                i += 1
                
                if command == 'v':  # relative
                    y += current_pos[1]
                
                current_pos = (current_pos[0], y)
                current_polyline.append(current_pos)
                
            elif command in 'Zz':  # Close path
                # Close the path by connecting to subpath start
                if current_polyline and current_polyline[-1] != subpath_start:
                    current_polyline.append(subpath_start)
                # Don't start a new polyline yet - Z might be followed by more commands
                
            elif command in 'Cc':  # Cubic Bezier
                # Get control points and end point
                x1 = float(tokens[i])
                y1 = float(tokens[i + 1])
                x2 = float(tokens[i + 2])
                y2 = float(tokens[i + 3])
                x = float(tokens[i + 4])
                y = float(tokens[i + 5])
                i += 6
                
                if command == 'c':  # relative
                    x1 += current_pos[0]
                    y1 += current_pos[1]
                    x2 += current_pos[0]
                    y2 += current_pos[1]
                    x += current_pos[0]
                    y += current_pos[1]
                
                # Sample the cubic Bezier curve
                p0 = current_pos
                p1 = (x1, y1)
                p2 = (x2, y2)
                p3 = (x, y)
                
                for j in range(1, segments_per_curve + 1):
                    t = j / segments_per_curve
                    # Cubic Bezier formula
                    t1 = 1 - t
                    bx = t1**3 * p0[0] + 3 * t1**2 * t * p1[0] + 3 * t1 * t**2 * p2[0] + t**3 * p3[0]
                    by = t1**3 * p0[1] + 3 * t1**2 * t * p1[1] + 3 * t1 * t**2 * p2[1] + t**3 * p3[1]
                    current_polyline.append((bx, by))
                
                current_pos = (x, y)
                
            elif command in 'Qq':  # Quadratic Bezier
                # Get control point and end point
                x1 = float(tokens[i])
                y1 = float(tokens[i + 1])
                x = float(tokens[i + 2])
                y = float(tokens[i + 3])
                i += 4
                
                if command == 'q':  # relative
                    x1 += current_pos[0]
                    y1 += current_pos[1]
                    x += current_pos[0]
                    y += current_pos[1]
                
                # Sample the quadratic Bezier curve
                p0 = current_pos
                p1 = (x1, y1)
                p2 = (x, y)
                
                for j in range(1, segments_per_curve + 1):
                    t = j / segments_per_curve
                    # Quadratic Bezier formula
                    t1 = 1 - t
                    bx = t1**2 * p0[0] + 2 * t1 * t * p1[0] + t**2 * p2[0]
                    by = t1**2 * p0[1] + 2 * t1 * t * p1[1] + t**2 * p2[1]
                    current_polyline.append((bx, by))
                
                current_pos = (x, y)
                
            else:
                # Unsupported command (S, T, A) - skip for now
                # Could implement if needed
                pass
            
            last_command = command
        else:
            # This shouldn't happen with proper tokenization
            i += 1
    
    # Add final polyline if any
    if current_polyline:
        polylines.append(current_polyline)
    
    return polylines


def _normalize_svg_coordinates(polylines: List[List[Tuple[float, float]]], 
                               viewbox_x: float, viewbox_y: float, 
                               viewbox_w: float, viewbox_h: float) -> List[List[Tuple[float, float]]]:
    """
    Normalize SVG coordinates from viewBox space to [0, 1] range.
    
    Args:
        polylines: List of polylines in viewBox coordinates
        viewbox_x, viewbox_y: ViewBox origin (typically 0, 0)
        viewbox_w, viewbox_h: ViewBox dimensions
        
    Returns:
        List of polylines with normalized coordinates in [0, 1] range
    """
    normalized = []
    for polyline in polylines:
        norm_polyline = []
        for x, y in polyline:
            # Normalize to [0, 1] range
            norm_x = (x - viewbox_x) / viewbox_w
            norm_y = (y - viewbox_y) / viewbox_h
            norm_polyline.append((norm_x, norm_y))
        normalized.append(norm_polyline)
    return normalized


# relative coordinates for female face (0–1 range)
# Extracted from Face_Mask_female.svg (1024x1024 normalized coordinates)
FEMALE_FACE: Dict[str, List[Tuple[float, float]]] = {
    # Outer head outline
    "outer_head": [
        (0.571760, 0.935952),
        (0.679310, 0.854875),
        (0.752114, 0.752289),
        (0.791825, 0.621574),
        (0.791825, 0.547116),
        (0.818299, 0.464385),
        (0.791825, 0.381654),
        (0.791825, 0.193027),
        (0.626362, 0.072239),
        (0.500000, 0.072239),
        (0.373638, 0.072239),
        (0.208175, 0.193027),
        (0.208175, 0.381654),
        (0.181701, 0.464385),
        (0.208175, 0.547116),
        (0.208175, 0.621574),
        (0.247886, 0.752289),
        (0.320690, 0.854875),
        (0.428240, 0.935952),
        (0.500000, 0.935174),
        (0.571760, 0.935952),  # Close the polyline
    ],
    # Cheeks
    "cheek_right": [
        (0.654307, 0.695507),
        (0.818298, 0.464385),
        (0.773225, 0.603442),
        (0.683077, 0.729073),
    ],
    "cheek_left": [
        (0.345693, 0.695507),
        (0.181702, 0.464385),
        (0.226775, 0.603442),
        (0.316923, 0.729073),
    ],
    # Chin
    "chin": [
        (0.445406, 0.935787),
        (0.430974, 0.890426),
        (0.459156, 0.851369),
        (0.500000, 0.838925),
        (0.540844, 0.851369),
        (0.569026, 0.890426),
        (0.554594, 0.935787),
    ],
    # Lips - now split into upper and lower (single shapes each)
    # CORRECTED: lips_upper is now the actual upper lip (smaller y values)
    # and lips_lower is the actual lower lip (larger y values)
    "lips_upper": [
        (0.459189, 0.749262),
        (0.444298, 0.754226),
        (0.391922, 0.753943),
        (0.475736, 0.726097),
        (0.500000, 0.736025),
        (0.524265, 0.726097),
        (0.608079, 0.753943),
        (0.555702, 0.754226),
        (0.540811, 0.749262),
        (0.500000, 0.764153),
        (0.459189, 0.749262),  # Close the polyline
    ],
    "lips_lower": [
        (0.458618, 0.750634),
        (0.442072, 0.754981),
        (0.392433, 0.754258),
        (0.450345, 0.800273),
        (0.487500, 0.800000),
        (0.500000, 0.796875),
        (0.512500, 0.800000),
        (0.549655, 0.800273),
        (0.607567, 0.754258),
        (0.557928, 0.754981),
        (0.541382, 0.750634),
        (0.500001, 0.762932),
        (0.458618, 0.750634),  # Close the polyline
    ],
    # Eyes
    "eye_right": [
        (0.653864, 0.474606),
        (0.723844, 0.449786),
        (0.711775, 0.433240),
        (0.695229, 0.412257),
        (0.653864, 0.400148),
        (0.587679, 0.449786),
        (0.653864, 0.474606),  # Close the polyline
    ],
    "eye_left": [
        (0.288225, 0.433240),
        (0.276156, 0.449786),
        (0.346136, 0.474606),
        (0.412321, 0.449786),
        (0.346136, 0.400148),
        (0.304771, 0.412257),
        (0.288225, 0.433240),  # Close the polyline
    ],
    # Eyebrows
    "eyebrow_right": [
        (0.568969, 0.383450),
        (0.721171, 0.333225),
        (0.792342, 0.386617),
        (0.721472, 0.361798),
        (0.585515, 0.406908),
    ],
    "eyebrow_left": [
        (0.431031, 0.383450),
        (0.278829, 0.333225),
        (0.207658, 0.386617),
        (0.278528, 0.361798),
        (0.414485, 0.406908),
    ],
    # Nose - single merged object (updated from SVG path46, 13 points)
    # Tip points are indices 5, 6, 7 (middle-most, lowest Y points)
    "nose": [
        (0.455541, 0.542654),  # [0]
        (0.428341, 0.619195),  # [1]
        (0.430238, 0.648926),  # [2]
        (0.455541, 0.655884),  # [3]
        (0.459375, 0.634375),  # [4]
        (0.487500, 0.656250),  # [5] tip point (left)
        (0.500000, 0.659375),  # [6] tip point (center, lowest)
        (0.512500, 0.656250),  # [7] tip point (right)
        (0.540625, 0.634375),  # [8]
        (0.544459, 0.655884),  # [9]
        (0.569762, 0.648926),  # [10]
        (0.571659, 0.619195),  # [11]
        (0.544459, 0.542654),  # [12]
    ],
    # Ears (extracted from Face_Mask_female.svg: path184 contains both ears as 2 subpaths)
    # SVG path: "m 50.800012,131.23334 -4.233333,-29.63333 h -8.466667 l -4.233333,33.86667 8.466667,33.86666 h 8.466666 z m 169.333288,0 4.23333,-29.63333 h 8.46667 l 4.23333,33.86667 -8.46667,33.86666 h -8.46666 z"
    # Normalized using viewBox (270.93331x270.93331)
    # Each ear is stored as a list of polylines (subpaths)
    # ear_left bbox: minx=0.125000 (<0.5✓), maxx=0.187500, miny=0.375000, maxy=0.625000
    "ear_left": [
        [
            (0.187500, 0.484375),
            (0.171875, 0.375000),
            (0.140625, 0.375000),
            (0.125000, 0.500000),
            (0.156250, 0.625000),
            (0.187500, 0.625000),
            (0.187500, 0.484375),  # Closed path
        ]
    ],
    # ear_right bbox: minx=0.812500 (>0.5✓), maxx=0.875000, miny=0.515625, maxy=0.765625
    "ear_right": [
        [
            (0.812500, 0.625000),
            (0.828125, 0.515625),
            (0.859375, 0.515625),
            (0.875000, 0.640625),
            (0.843750, 0.765625),
            (0.812500, 0.765625),
            (0.812500, 0.625000),  # Closed path
        ]
    ],
}

# Iris data is kept separate because irises are drawn as circles.
# Extracted from Face_Mask_female.svg (1024x1024 file using viewBox 270.93331x270.93331)
# Normalized using SVG viewBox coordinates:
# - Right iris: cx=170.09473, cy=115.99001, r=7.36947 → normalized by viewBox dimensions
# - Left iris: cx=100.8386, cy=115.99001, r=7.36947 → normalized by viewBox dimensions
# Baked offsets: left iris -0.020 (from -0.040*0.5), right iris +0.020 (from +0.040*0.5)
# to achieve correct visual alignment with iris_pos_x defaults at 0.0
FEMALE_FACE_IRISES = {
    "iris_right": {"center": (0.6478103272, 0.4281127706), "radius": 0.0272003099},
    "iris_left": {"center": (0.3521897466, 0.4281127706), "radius": 0.0272003099},
}

# Number of parameters in settings_list (for import/export functionality)
# Set to 60 to allow for future expansion (currently 57 parameters are used)
SETTINGS_LIST_LENGTH = 60

# Cheek connection points (hardcoded from SVG coordinates)
CHEEK_LEFT_END_POINT = (0.316923, 0.729073)
CHEEK_LEFT_OUTER_HEAD_POINT = (0.320690, 0.854875)
CHEEK_RIGHT_END_POINT = (0.683077, 0.729073)
CHEEK_RIGHT_OUTER_HEAD_POINT = (0.679310, 0.854875)

def _face_data_for_gender(gender: str):
    """Return the polyline coordinates for the requested gender preset."""
    # TODO: replace with male‑specific coordinates once available; currently both
    # genders use the female mask.
    return FEMALE_FACE


def _iris_data_for_gender(gender: str):
    """Return the iris data for the requested gender preset."""
    # TODO: replace with male‑specific coordinates once available; currently both
    # genders use the female mask.
    return FEMALE_FACE_IRISES


class ComfyUIFaceShaper:
    """Custom node that draws a parametric facial mask."""

    CATEGORY = "face"
    RETURN_TYPES = ("IMAGE", "LIST")
    FUNCTION = "draw_face"

    @classmethod
    def INPUT_TYPES(cls):
        """Define adjustable parameters for the node."""
        return {
            "required": {
                "canvas_width": ("INT", {"default": 1024, "min": 256, "max": 2048}),
                "canvas_height": ("INT", {"default": 1024, "min": 256, "max": 2048}),
                "gender": (["female", "male"],),
                "transparent_background": ("BOOLEAN", {"default": False}),
                "debug_geometry": ("BOOLEAN", {"default": False}),
                "debug_ears": ("BOOLEAN", {"default": False}),
                # Eyes
                "eye_left_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "eye_left_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "eye_left_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "eye_left_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "eye_right_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "eye_right_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "eye_right_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "eye_right_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                # Irises (separated)
                "iris_left_size": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "iris_left_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.25, "max": 0.25, "step": 0.005},
                ),
                "iris_left_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.25, "max": 0.25, "step": 0.005},
                ),
                "iris_right_size": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "iris_right_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.25, "max": 0.25, "step": 0.005},
                ),
                "iris_right_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.25, "max": 0.25, "step": 0.005},
                ),
                # Outer head outline
                "outer_head_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "outer_head_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "jaw_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "forehead_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                # Lips (shared controls for both upper and lower)
                "lips_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "lips_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "lip_upper_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "lip_lower_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                # Chin
                "chin_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "chin_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                # Cheeks
                "cheek_left_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.3, "max": 0.3, "step": 0.005},
                ),
                "cheek_left_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.3, "max": 0.3, "step": 0.005},
                ),
                "cheek_right_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.3, "max": 0.3, "step": 0.005},
                ),
                "cheek_right_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.3, "max": 0.3, "step": 0.005},
                ),
                # Ears (near cheeks/eyebrows)
                "ear_left_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.3, "max": 0.3, "step": 0.005},
                ),
                "ear_left_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.3, "max": 0.3, "step": 0.005},
                ),
                "ear_left_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "ear_left_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "ear_right_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.3, "max": 0.3, "step": 0.005},
                ),
                "ear_right_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.3, "max": 0.3, "step": 0.005},
                ),
                "ear_right_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "ear_right_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                # Eyebrows
                "eyebrow_left_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "eyebrow_left_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "eyebrow_left_rotation": (
                    "FLOAT",
                    {"default": 0.0, "min": -45.0, "max": 45.0, "step": 0.1},
                ),
                "eyebrow_left_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "eyebrow_left_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "eyebrow_right_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "eyebrow_right_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "eyebrow_right_rotation": (
                    "FLOAT",
                    {"default": 0.0, "min": -45.0, "max": 45.0, "step": 0.1},
                ),
                "eyebrow_right_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "eyebrow_right_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                # Nose (single merged object)
                "nose_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "nose_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "nose_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                # Nose tip (integrated within nose polyline)
                "nose_tip_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.2, "max": 0.2, "step": 0.005},
                ),
                # Global
                "camera_distance": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "camera_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "camera_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "fov_mm": (
                    "FLOAT",
                    {"default": 80.0, "min": 16.0, "max": 200.0, "step": 1.0},
                ),
                "line_thickness": (
                    "FLOAT",
                    {"default": 2.0, "min": 0.5, "max": 10.0, "step": 0.1},
                ),
            },
            "optional": {
                "settings_list": ("LIST", {"default": None}),
            },
        }

    def draw_face(
        self,
        canvas_width: int,
        canvas_height: int,
        gender: str,
        transparent_background: bool,
        debug_geometry: bool,
        debug_ears: bool,
        eye_left_size_x: float,
        eye_left_size_y: float,
        eye_left_pos_x: float,
        eye_left_pos_y: float,
        eye_right_size_x: float,
        eye_right_size_y: float,
        eye_right_pos_x: float,
        eye_right_pos_y: float,
        iris_left_size: float,
        iris_left_pos_x: float,
        iris_left_pos_y: float,
        iris_right_size: float,
        iris_right_pos_x: float,
        iris_right_pos_y: float,
        outer_head_size_x: float,
        outer_head_size_y: float,
        jaw_size_x: float,
        forehead_size_x: float,
        lips_pos_y: float,
        lips_size_x: float,
        lip_upper_size_y: float,
        lip_lower_size_y: float,
        chin_size_x: float,
        chin_size_y: float,
        cheek_left_pos_x: float,
        cheek_left_pos_y: float,
        cheek_right_pos_x: float,
        cheek_right_pos_y: float,
        ear_left_pos_x: float,
        ear_left_pos_y: float,
        ear_left_size_x: float,
        ear_left_size_y: float,
        ear_right_pos_x: float,
        ear_right_pos_y: float,
        ear_right_size_x: float,
        ear_right_size_y: float,
        eyebrow_left_size_x: float,
        eyebrow_left_size_y: float,
        eyebrow_left_rotation: float,
        eyebrow_left_pos_x: float,
        eyebrow_left_pos_y: float,
        eyebrow_right_size_x: float,
        eyebrow_right_size_y: float,
        eyebrow_right_rotation: float,
        eyebrow_right_pos_x: float,
        eyebrow_right_pos_y: float,
        nose_pos_y: float,
        nose_size_x: float,
        nose_size_y: float,
        nose_tip_pos_y: float,
        camera_distance: float,
        camera_pos_x: float,
        camera_pos_y: float,
        fov_mm: float,
        line_thickness: float,
        settings_list=None,
    ):
        """Render the facial mask image and return it as a tensor."""
        # Handle settings_list import: override all adjustable parameters if provided
        if settings_list is not None and len(settings_list) >= SETTINGS_LIST_LENGTH:
            eye_left_size_x = settings_list[0]
            eye_left_size_y = settings_list[1]
            eye_left_pos_x = settings_list[2]
            eye_left_pos_y = settings_list[3]
            eye_right_size_x = settings_list[4]
            eye_right_size_y = settings_list[5]
            eye_right_pos_x = settings_list[6]
            eye_right_pos_y = settings_list[7]
            iris_left_size = settings_list[8]
            iris_left_pos_x = settings_list[9]
            iris_left_pos_y = settings_list[10]
            iris_right_size = settings_list[11]
            iris_right_pos_x = settings_list[12]
            iris_right_pos_y = settings_list[13]
            outer_head_size_x = settings_list[14]
            outer_head_size_y = settings_list[15]
            jaw_size_x = settings_list[16]
            forehead_size_x = settings_list[17]
            lips_pos_y = settings_list[18]
            lips_size_x = settings_list[19]
            lip_upper_size_y = settings_list[20]
            lip_lower_size_y = settings_list[21]
            chin_size_x = settings_list[22]
            chin_size_y = settings_list[23]
            cheek_left_pos_x = settings_list[24]
            cheek_left_pos_y = settings_list[25]
            cheek_right_pos_x = settings_list[26]
            cheek_right_pos_y = settings_list[27]
            ear_left_pos_x = settings_list[28]
            ear_left_pos_y = settings_list[29]
            ear_left_size_x = settings_list[30]
            ear_left_size_y = settings_list[31]
            ear_right_pos_x = settings_list[32]
            ear_right_pos_y = settings_list[33]
            ear_right_size_x = settings_list[34]
            ear_right_size_y = settings_list[35]
            eyebrow_left_size_x = settings_list[36]
            eyebrow_left_size_y = settings_list[37]
            eyebrow_left_rotation = settings_list[38]
            eyebrow_left_pos_x = settings_list[39]
            eyebrow_left_pos_y = settings_list[40]
            eyebrow_right_size_x = settings_list[41]
            eyebrow_right_size_y = settings_list[42]
            eyebrow_right_rotation = settings_list[43]
            eyebrow_right_pos_x = settings_list[44]
            eyebrow_right_pos_y = settings_list[45]
            nose_pos_y = settings_list[46]
            nose_size_x = settings_list[47]
            nose_size_y = settings_list[48]
            nose_tip_pos_y = settings_list[49]
            camera_distance = settings_list[50]
            camera_pos_x = settings_list[51]
            camera_pos_y = settings_list[52]
            fov_mm = settings_list[53]
            line_thickness = settings_list[54]
            # Note: canvas_width/canvas_height (indices 55-56) are exported but not imported
            # as they are always provided as direct parameters to the method
            # Total: 57 parameters (55 feature controls + 2 canvas dimensions)
        
        face_points = _face_data_for_gender(gender)
        iris_data = _iris_data_for_gender(gender)

        # Debug geometry output
        if debug_geometry:
            print("\n=== Debug Geometry Summary ===")
            for feature_name in ["ear_left", "ear_right", "nose"]:
                if feature_name in face_points:
                    points = face_points[feature_name]
                    count = len(points)
                    xs = [x for x, y in points]
                    ys = [y for x, y in points]
                    minx, maxx = min(xs), max(xs)
                    miny, maxy = min(ys), max(ys)
                    print(f"{feature_name}: count={count}, bbox=(minx={minx:.6f}, maxx={maxx:.6f}, miny={miny:.6f}, maxy={maxy:.6f})")
            print("==============================\n")

        # Create a blank canvas - RGBA for transparent background, RGB for white background.
        if transparent_background:
            img = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))
        else:
            img = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(img)
        # Pillow expects integer stroke widths; round and enforce a minimum of 1 so lines stay visible.
        stroke_width = max(1, int(round(line_thickness)))

        # Calculate radial distortion coefficient based on fov_mm
        # Neutral at 80mm => k1=0
        # For fov_mm < 80 (wide) use negative k1 (barrel distortion)
        # For fov_mm > 80 use positive k1 (pincushion distortion)
        t = fov_mm - 80.0
        if t < 0:
            tn = t / (80.0 - 16.0)  # [-1, 0]
        else:
            tn = t / (200.0 - 80.0)  # [0, 1]
        k1 = tn * 0.18

        def apply_distortion(x: float, y: float) -> Tuple[float, float]:
            """Apply radial distortion to pixel coordinates."""
            if k1 == 0:
                return (x, y)
            cx = canvas_width / 2.0
            cy = canvas_height / 2.0
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            r2 = dx * dx + dy * dy
            factor = 1.0 + k1 * r2
            x_distorted = cx + dx * factor * cx
            y_distorted = cy + dy * factor * cy
            return (x_distorted, y_distorted)

        def to_pixel(point: Tuple[float, float]) -> Tuple[float, float]:
            """Convert relative coordinates in range [0,1] to pixel positions with distortion."""
            rx, ry = point
            x = (rx - 0.5 + camera_pos_x) * canvas_width * camera_distance + canvas_width / 2.0
            y = (ry - 0.5 + camera_pos_y) * canvas_height * camera_distance + canvas_height / 2.0
            return apply_distortion(x, y)

        # Helper to scale and translate polygons.
        def transform_polygon(
            points: List[Tuple[float, float]],
            scale_x: float,
            scale_y: float,
            offset_x: float,
            offset_y: float,
        ) -> List[Tuple[float, float]]:
            if not points:
                return []
            cx = sum(px for px, _ in points) / len(points)
            cy = sum(py for _, py in points) / len(points)
            transformed = []
            for rx, ry in points:
                dx = (rx - cx) * scale_x
                dy = (ry - cy) * scale_y
                transformed.append((cx + dx + offset_x, cy + dy + offset_y))
            return transformed

        # Helper to translate polygons.
        def translate_polygon(
            points: List[Tuple[float, float]],
            offset_x: float,
            offset_y: float,
        ) -> List[Tuple[float, float]]:
            return [(rx + offset_x, ry + offset_y) for rx, ry in points]

        # Helper to rotate points around a center by angle in degrees.
        def rotate_polygon(
            points: List[Tuple[float, float]],
            angle_degrees: float,
            cx: float,
            cy: float,
        ) -> List[Tuple[float, float]]:
            """Rotate points around (cx, cy) by angle_degrees using 2D rotation."""
            if angle_degrees == 0.0:
                return points
            angle_rad = math.radians(angle_degrees)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            rotated = []
            for rx, ry in points:
                # Translate to origin
                dx = rx - cx
                dy = ry - cy
                # Rotate
                new_x = dx * cos_a - dy * sin_a
                new_y = dx * sin_a + dy * cos_a
                # Translate back
                rotated.append((cx + new_x, cy + new_y))
            return rotated

        # Helper to transform eyebrow: scale → rotate → translate
        def transform_eyebrow(
            points: List[Tuple[float, float]],
            size_x: float,
            size_y: float,
            rotation_degrees: float,
            pos_x: float,
            pos_y: float,
        ) -> List[Tuple[float, float]]:
            """Apply scale, rotation, and translation to eyebrow points."""
            # Calculate centroid
            cx = sum(px for px, _ in points) / len(points)
            cy = sum(py for _, py in points) / len(points)
            
            # Step 1: Scale around centroid
            scaled = []
            for rx, ry in points:
                dx = (rx - cx) * size_x
                dy = (ry - cy) * size_y
                scaled.append((cx + dx, cy + dy))
            
            # Step 2: Rotate around centroid
            rotated = rotate_polygon(scaled, rotation_degrees, cx, cy)
            
            # Step 3: Apply positional offset
            return translate_polygon(rotated, pos_x, pos_y)

        # Draw outer head outline with per-region horizontal scaling
        if "outer_head" in face_points:
            # Calculate centroid for scaling
            cx = sum(px for px, _ in face_points["outer_head"]) / len(face_points["outer_head"])
            cy = sum(py for _, py in face_points["outer_head"]) / len(face_points["outer_head"])
            
            outer_head = []
            for rx, ry in face_points["outer_head"]:
                # Determine which horizontal scale to use based on y position
                if ry > 0.7:
                    # Jaw region (bottom)
                    scale_x = jaw_size_x
                elif ry < 0.3:
                    # Forehead region (top)
                    scale_x = forehead_size_x
                else:
                    # Mid region
                    scale_x = outer_head_size_x
                
                # Apply scaling
                dx = (rx - cx) * scale_x
                dy = (ry - cy) * outer_head_size_y
                outer_head.append((cx + dx, cy + dy))
            
            pixel_points = [to_pixel(pt) for pt in outer_head]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        # Draw ears with scaling and positioning (no rotation)
        # Ears are drawn after head_outline and before cheeks for proper layering
        # Ears are now stored as lists of polylines to preserve subpaths from SVG
        if "ear_left" in face_points and isinstance(face_points["ear_left"], list):
            ear_polylines = face_points["ear_left"]
            
            # Debug logging
            if debug_ears:
                total_points = sum(len(poly) for poly in ear_polylines)
                xs = [x for poly in ear_polylines for x, y in poly]
                ys = [y for poly in ear_polylines for x, y in poly]
                print(f"ear_left: {len(ear_polylines)} subpath(s), {total_points} points total, "
                      f"bbox=(minx={min(xs):.6f}, maxx={max(xs):.6f}, miny={min(ys):.6f}, maxy={max(ys):.6f})")
            
            # Transform and draw each subpath
            for polyline in ear_polylines:
                if len(polyline) < 2:
                    continue
                    
                # Transform this polyline
                transformed = transform_polygon(
                    polyline,
                    ear_left_size_x,
                    ear_left_size_y,
                    ear_left_pos_x,
                    ear_left_pos_y,
                )
                
                # Convert to pixels
                pixel_points = [to_pixel(pt) for pt in transformed]
                
                # Draw with optional debug coloring
                if debug_ears:
                    draw.line(pixel_points, fill=(255, 0, 0), width=max(stroke_width, 3))
                else:
                    draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)
        
        if "ear_right" in face_points and isinstance(face_points["ear_right"], list):
            ear_polylines = face_points["ear_right"]
            
            # Debug logging
            if debug_ears:
                total_points = sum(len(poly) for poly in ear_polylines)
                xs = [x for poly in ear_polylines for x, y in poly]
                ys = [y for poly in ear_polylines for x, y in poly]
                print(f"ear_right: {len(ear_polylines)} subpath(s), {total_points} points total, "
                      f"bbox=(minx={min(xs):.6f}, maxx={max(xs):.6f}, miny={min(ys):.6f}, maxy={max(ys):.6f})")
            
            # Transform and draw each subpath
            for polyline in ear_polylines:
                if len(polyline) < 2:
                    continue
                    
                # Transform this polyline
                transformed = transform_polygon(
                    polyline,
                    ear_right_size_x,
                    ear_right_size_y,
                    ear_right_pos_x,
                    ear_right_pos_y,
                )
                
                # Convert to pixels
                pixel_points = [to_pixel(pt) for pt in transformed]
                
                # Draw with optional debug coloring
                if debug_ears:
                    draw.line(pixel_points, fill=(0, 0, 255), width=max(stroke_width, 3))
                else:
                    draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        # Draw chin with scaling only (no positioning)
        if "chin" in face_points:
            chin = transform_polygon(
                face_points["chin"],
                chin_size_x,
                chin_size_y,
                0.0,
                0.0,
            )
            pixel_points = [to_pixel(pt) for pt in chin]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        # Draw eyebrows with scale → rotation → translation transform order
        if "eyebrow_left" in face_points:
            eyebrow_left = transform_eyebrow(
                face_points["eyebrow_left"],
                eyebrow_left_size_x,
                eyebrow_left_size_y,
                eyebrow_left_rotation,
                eyebrow_left_pos_x,
                eyebrow_left_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in eyebrow_left]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        if "eyebrow_right" in face_points:
            eyebrow_right = transform_eyebrow(
                face_points["eyebrow_right"],
                eyebrow_right_size_x,
                eyebrow_right_size_y,
                eyebrow_right_rotation,
                eyebrow_right_pos_x,
                eyebrow_right_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in eyebrow_right]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        # Draw nose (single merged object) with scaling, y-positioning, and integrated tip control
        if "nose" in face_points:
            # First apply scaling and main y-positioning
            nose = transform_polygon(
                face_points["nose"],
                nose_size_x,
                nose_size_y,
                0.0,
                nose_pos_y,
            )
            
            # Algorithmically select the 3 tip points (lowest on face, most central)
            # Sort by: 1) ry descending (lowest on face first), then 2) abs(rx-0.5) ascending (most central)
            face_center_x = 0.5
            indexed_points = [(idx, x, y) for idx, (x, y) in enumerate(nose)]
            sorted_points = sorted(indexed_points, key=lambda p: (-p[2], abs(p[1] - face_center_x)))
            nose_tip_indices = {p[0] for p in sorted_points[:3]}
            
            # Apply nose_tip_pos_y to the selected 3 tip points only
            nose_with_tip = []
            for idx, (x, y) in enumerate(nose):
                if idx in nose_tip_indices:
                    # Apply tip position offset (positive moves down in y-down coordinate system)
                    nose_with_tip.append((x, y + nose_tip_pos_y))
                else:
                    nose_with_tip.append((x, y))
            
            # Draw the nose
            pixel_points = [to_pixel(pt) for pt in nose_with_tip]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)
            
            # Optional: Mark nose tip points when debug_geometry is enabled
            if debug_geometry:
                for idx, (x, y) in enumerate(nose_with_tip):
                    if idx in nose_tip_indices:
                        px, py = to_pixel((x, y))
                        # Draw a small circle marker (radius 3 pixels)
                        marker_radius = 3
                        draw.ellipse(
                            [px - marker_radius, py - marker_radius, px + marker_radius, py + marker_radius],
                            fill=(255, 0, 0),  # Red marker
                            outline=(255, 0, 0)
                        )

        # Draw lips (upper and lower) with direction-specific scaling
        # Mouth midline is approximately at y = 0.757394
        mouth_midline_y = 0.757394
        
        # Upper lip - scale upward (decreasing y, toward top of image)
        if "lips_upper" in face_points:
            lips_upper_scaled = []
            for rx, ry in face_points["lips_upper"]:
                # Apply horizontal scaling around center
                cx = sum(px for px, _ in face_points["lips_upper"]) / len(face_points["lips_upper"])
                dx = (rx - cx) * lips_size_x
                new_x = cx + dx
                
                # Apply vertical scaling only in upward direction from midline
                # Upper lip is above midline, so we scale away from midline (decreasing y)
                dy_from_midline = ry - mouth_midline_y  # negative for upper lip
                scaled_dy = dy_from_midline * lip_upper_size_y
                new_y = mouth_midline_y + scaled_dy + lips_pos_y
                
                lips_upper_scaled.append((new_x, new_y))
            
            pixel_points = [to_pixel(pt) for pt in lips_upper_scaled]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)
        
        # Lower lip - scale downward (increasing y, toward bottom of image)
        if "lips_lower" in face_points:
            lips_lower_scaled = []
            for rx, ry in face_points["lips_lower"]:
                # Apply horizontal scaling around center
                cx = sum(px for px, _ in face_points["lips_lower"]) / len(face_points["lips_lower"])
                dx = (rx - cx) * lips_size_x
                new_x = cx + dx
                
                # Apply vertical scaling only in downward direction from midline
                # Lower lip is below midline, so we scale away from midline (increasing y)
                dy_from_midline = ry - mouth_midline_y  # positive for lower lip
                scaled_dy = dy_from_midline * lip_lower_size_y
                new_y = mouth_midline_y + scaled_dy + lips_pos_y
                
                lips_lower_scaled.append((new_x, new_y))
            
            pixel_points = [to_pixel(pt) for pt in lips_lower_scaled]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        # Draw cheeks with position offsets and connect them to outer head
        if "cheek_left" in face_points:
            cheek_left = translate_polygon(
                face_points["cheek_left"],
                cheek_left_pos_x,
                cheek_left_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in cheek_left]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)
            # Connect cheek_left last point to outer head point
            cheek_left_end = to_pixel((CHEEK_LEFT_END_POINT[0] + cheek_left_pos_x,
                                       CHEEK_LEFT_END_POINT[1] + cheek_left_pos_y))
            outer_head_point = to_pixel(CHEEK_LEFT_OUTER_HEAD_POINT)
            draw.line([cheek_left_end, outer_head_point], fill=(0, 0, 0), width=stroke_width)

        if "cheek_right" in face_points:
            cheek_right = translate_polygon(
                face_points["cheek_right"],
                cheek_right_pos_x,
                cheek_right_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in cheek_right]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)
            # Connect cheek_right last point to outer head point
            cheek_right_end = to_pixel((CHEEK_RIGHT_END_POINT[0] + cheek_right_pos_x,
                                        CHEEK_RIGHT_END_POINT[1] + cheek_right_pos_y))
            outer_head_point = to_pixel(CHEEK_RIGHT_OUTER_HEAD_POINT)
            draw.line([cheek_right_end, outer_head_point], fill=(0, 0, 0), width=stroke_width)

        # Transform and draw both eyes.
        eye_right = transform_polygon(
            face_points["eye_right"],
            eye_right_size_x,
            eye_right_size_y,
            eye_right_pos_x,
            eye_right_pos_y,
        )
        eye_left = transform_polygon(
            face_points["eye_left"],
            eye_left_size_x,
            eye_left_size_y,
            eye_left_pos_x,
            eye_left_pos_y,
        )
        draw.line([to_pixel(pt) for pt in eye_right], fill=(0, 0, 0), width=stroke_width)
        draw.line([to_pixel(pt) for pt in eye_left], fill=(0, 0, 0), width=stroke_width)

        # Draw irises as circles with separate controls for each.
        def draw_iris_with_params(center_key: str, iris_size: float, iris_pos_x: float, iris_pos_y: float):
            base_center = iris_data[center_key]["center"]
            base_radius = iris_data[center_key]["radius"]
            # Apply 0.5 multiplier to make iris position controls 2x finer
            cx_rel = base_center[0] + (iris_pos_x * 0.5)
            cy_rel = base_center[1] + (iris_pos_y * 0.5)
            cx, cy = to_pixel((cx_rel, cy_rel))
            # Use the smaller canvas dimension so the iris remains round across aspect ratios.
            radius_px = (
                base_radius * iris_size * min(canvas_width, canvas_height) * camera_distance
            )
            bbox = [
                cx - radius_px,
                cy - radius_px,
                cx + radius_px,
                cy + radius_px,
            ]
            draw.ellipse(bbox, outline=(0, 0, 0), width=stroke_width)

        draw_iris_with_params("iris_right", iris_right_size, iris_right_pos_x, iris_right_pos_y)
        draw_iris_with_params("iris_left", iris_left_size, iris_left_pos_x, iris_left_pos_y)

        # Convert the PIL image to a tensor of shape [B, H, W, C] (B=1).
        # The image is already in the correct format (RGB or RGBA) based on how it was created.
        # For white background: RGB mode → 3 channels
        # For transparent background: RGBA mode → 4 channels
        arr = np.array(img).astype(np.float32) / 255.0
        tensor = torch.from_numpy(arr).unsqueeze(0)
        
        # Create settings list with all adjustable parameters in consistent order
        settings_export = [
            eye_left_size_x,
            eye_left_size_y,
            eye_left_pos_x,
            eye_left_pos_y,
            eye_right_size_x,
            eye_right_size_y,
            eye_right_pos_x,
            eye_right_pos_y,
            iris_left_size,
            iris_left_pos_x,
            iris_left_pos_y,
            iris_right_size,
            iris_right_pos_x,
            iris_right_pos_y,
            outer_head_size_x,
            outer_head_size_y,
            jaw_size_x,
            forehead_size_x,
            lips_pos_y,
            lips_size_x,
            lip_upper_size_y,
            lip_lower_size_y,
            chin_size_x,
            chin_size_y,
            cheek_left_pos_x,
            cheek_left_pos_y,
            cheek_right_pos_x,
            cheek_right_pos_y,
            ear_left_pos_x,
            ear_left_pos_y,
            ear_left_size_x,
            ear_left_size_y,
            ear_right_pos_x,
            ear_right_pos_y,
            ear_right_size_x,
            ear_right_size_y,
            eyebrow_left_size_x,
            eyebrow_left_size_y,
            eyebrow_left_rotation,
            eyebrow_left_pos_x,
            eyebrow_left_pos_y,
            eyebrow_right_size_x,
            eyebrow_right_size_y,
            eyebrow_right_rotation,
            eyebrow_right_pos_x,
            eyebrow_right_pos_y,
            nose_pos_y,
            nose_size_x,
            nose_size_y,
            nose_tip_pos_y,
            camera_distance,
            camera_pos_x,
            camera_pos_y,
            fov_mm,
            line_thickness,
            canvas_width,
            canvas_height,
        ]
        
        return (tensor, settings_export)


# Register the node with hyphen‑free identifiers. These mappings are used by
# ComfyUI to locate and instantiate the node. Avoiding hyphens ensures the
# identifiers are valid Python identifiers, which improves compatibility with
# ComfyUI’s loading mechanism.
NODE_CLASS_MAPPINGS = {
    "RORICH-AI": ComfyUIFaceShaper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RORICH-AI": "Face Shaper",
}