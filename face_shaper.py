"""
Refined implementation of the ComfyUI Face Shaper custom node.

This module implements a custom node that draws a stylized facial mask based on
SVG‑derived coordinates extracted from Face_Mask_female.svg (1024×1024). Users 
can adjust the positions and sizes of distinct facial features including:
outer head outline, eyes, irises, eyebrows, nose (single merged object), 
nose tip, ears (left and right), lips (upper and lower with direction-specific 
scaling), chin, and cheeks. All coordinates are normalized to [0-1] range. 
Users can select a gender preset (currently both genders use the same 
coordinates), change the canvas size and camera distance, and control the line 
thickness. The output is black lines on either a white or transparent background 
as a tensor compatible with ComfyUI workflows.

Key improvements in this version:
- Updated to use merged nose (single object) from latest SVG
- Added ear_left and ear_right geometry with independent position/size controls
- Added nose_tip geometry with vertical position and size controls
- Lips now split into upper and lower with independent y-scaling
- Direction-specific lip scaling keeps mouth midline anchored
- Nose simplified to 3 parameters: pos_y, size_x, size_y
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

import numpy as np
import torch
from PIL import Image, ImageDraw

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
    # Nose - single merged object (updated from SVG path46, 11 points)
    "nose": [
        (0.455541, 0.542654),
        (0.428341, 0.619195),
        (0.430238, 0.648926),
        (0.455541, 0.655884),
        (0.449215, 0.636907),
        (0.500000, 0.671066),
        (0.550785, 0.636907),
        (0.544459, 0.655884),
        (0.569762, 0.648926),
        (0.571659, 0.619195),
        (0.544459, 0.542654),
    ],
    # Ears
    "ear_right": [
        (0.653864, 0.474606),
        (0.723844, 0.449786),
        (0.711775, 0.433240),
        (0.695229, 0.412257),
        (0.653864, 0.400148),
        (0.587679, 0.449786),
    ],
    "ear_left": [
        (0.288225, 0.433240),
        (0.276156, 0.449786),
        (0.346136, 0.474606),
        (0.412321, 0.449786),
        (0.346136, 0.400148),
        (0.304771, 0.412257),
    ],
    # Nose tip
    "nose_tip": [
        (0.455541, 0.542654),
        (0.428341, 0.619195),
        (0.430238, 0.648926),
        (0.455541, 0.655884),
        (0.449215, 0.636907),
        (0.500000, 0.671066),
        (0.550785, 0.636907),
        (0.544459, 0.655884),
        (0.569762, 0.648926),
        (0.571659, 0.619195),
        (0.544459, 0.542654),
    ],
}

# Iris data is kept separate because irises are drawn as circles.
# Extracted from Face_Mask_female.svg (1024x1024 file using viewBox 270.93331x270.93331)
# Normalized using SVG viewBox coordinates:
# - Right iris: cx=170.09473, cy=115.99001, r=7.36947 → normalized by viewBox dimensions
# - Left iris: cx=100.8386, cy=115.99001, r=7.36947 → normalized by viewBox dimensions
FEMALE_FACE_IRISES = {
    "iris_right": {"center": (0.6278103272, 0.4281127706), "radius": 0.0272003099},
    "iris_left": {"center": (0.3721897466, 0.4281127706), "radius": 0.0272003099},
}

# Number of parameters in settings_list (for import/export functionality)
# Set to 60 to allow for future expansion (currently 58 parameters are used)
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
                # Nose tip (near nose)
                "nose_tip_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.2, "max": 0.2, "step": 0.005},
                ),
                "nose_tip_size_x": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "nose_tip_size_y": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
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
        nose_tip_size_x: float,
        nose_tip_size_y: float,
        camera_distance: float,
        camera_pos_x: float,
        camera_pos_y: float,
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
            nose_tip_size_x = settings_list[50]
            nose_tip_size_y = settings_list[51]
            camera_distance = settings_list[52]
            camera_pos_x = settings_list[53]
            camera_pos_y = settings_list[54]
            line_thickness = settings_list[55]
            # Note: canvas_width/canvas_height (indices 56-57) are exported but not imported
            # as they are always provided as direct parameters to the method
            # Total: 58 parameters (56 feature controls + 2 canvas dimensions)
        
        face_points = _face_data_for_gender(gender)
        iris_data = _iris_data_for_gender(gender)

        # Create a blank canvas - RGBA for transparent background, RGB for white background.
        if transparent_background:
            img = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))
        else:
            img = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(img)
        # Pillow expects integer stroke widths; round and enforce a minimum of 1 so lines stay visible.
        stroke_width = max(1, int(round(line_thickness)))

        def to_pixel(point: Tuple[float, float]) -> Tuple[float, float]:
            """Convert relative coordinates in range [0,1] to pixel positions."""
            rx, ry = point
            x = (rx - 0.5 + camera_pos_x) * canvas_width * camera_distance + canvas_width / 2.0
            y = (ry - 0.5 + camera_pos_y) * canvas_height * camera_distance + canvas_height / 2.0
            return (x, y)

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

        # Draw nose (single merged object) with scaling and y-positioning
        if "nose" in face_points:
            nose = transform_polygon(
                face_points["nose"],
                nose_size_x,
                nose_size_y,
                0.0,
                nose_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in nose]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)
        
        # Draw nose tip with scaling and y-positioning (no x-positioning, no rotation)
        if "nose_tip" in face_points:
            nose_tip = transform_polygon(
                face_points["nose_tip"],
                nose_tip_size_x,
                nose_tip_size_y,
                0.0,
                nose_tip_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in nose_tip]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)
        
        # Draw ears with scaling and positioning (no rotation)
        if "ear_left" in face_points:
            ear_left = transform_polygon(
                face_points["ear_left"],
                ear_left_size_x,
                ear_left_size_y,
                ear_left_pos_x,
                ear_left_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in ear_left]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)
        
        if "ear_right" in face_points:
            ear_right = transform_polygon(
                face_points["ear_right"],
                ear_right_size_x,
                ear_right_size_y,
                ear_right_pos_x,
                ear_right_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in ear_right]
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
            nose_tip_size_x,
            nose_tip_size_y,
            camera_distance,
            camera_pos_x,
            camera_pos_y,
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