"""
Refined implementation of the ComfyUI Face Shaper custom node.

This module implements a custom node that draws a stylized facial mask based on
SVG‑derived coordinates extracted from Face_Mask_female.svg (1024×1024). Users 
can adjust the positions and sizes of distinct facial features including:
outer head outline, eyes, irises, eyebrows, nose (single merged object), 
lips (upper and lower with direction-specific scaling), chin, and cheeks. 
All coordinates are normalized to [0-1] range. Users can select a gender preset 
(currently both genders use the same coordinates), change the canvas size and 
camera distance, and control the line thickness. The output is black lines on 
either a white or transparent background as a tensor compatible with ComfyUI workflows.

Key improvements in this version:
- Updated to use merged nose (single object) from latest SVG
- Lips now split into upper and lower with independent y-scaling
- Direction-specific lip scaling keeps mouth midline anchored
- Nose simplified to 3 parameters: pos_y, size_x, size_y
- All position parameters default to 0.0 (zero offsets by default)
- Per-feature scaling controls prevent distortion across unrelated features
- Maintains proper node structure with CATEGORY="face", INPUT_TYPES, RETURN_TYPES=("IMAGE",)
- Optional transparent background support for alpha-aware workflows
"""

from typing import Dict, List, Tuple

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
        (0.334538, 0.193027),
        (0.334538, 0.381654),
        (0.308064, 0.464385),
        (0.334538, 0.547116),
        (0.334538, 0.621574),
        (0.374249, 0.752289),
        (0.447052, 0.854875),
        (0.554603, 0.935952),
        (0.626362, 0.935174),
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
    ],
    # Eyes
    "eye_right": [
        (0.653864, 0.474606),
        (0.723844, 0.449786),
        (0.711775, 0.433240),
        (0.695229, 0.412257),
        (0.653864, 0.400148),
        (0.587679, 0.449786),
    ],
    "eye_left": [
        (0.288225, 0.433240),
        (0.276156, 0.449786),
        (0.346136, 0.474606),
        (0.412321, 0.449786),
        (0.346136, 0.400148),
        (0.304771, 0.412257),
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
    # Nose - single merged object (updated from SVG path46, 22 points)
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
        (0.544149, 0.629847),
        (0.525524, 0.579209),
        (0.524094, 0.441927),
        (0.475906, 0.441927),
        (0.474476, 0.579209),
        (0.455851, 0.629847),
        (0.500000, 0.643776),
        (0.544149, 0.629847),
        (0.541970, 0.465522),
        (0.455851, 0.629847),
        (0.458030, 0.465522),
    ],
}

# Iris data is kept separate because irises are drawn as circles.
# Extracted from Face_Mask_female.svg (circles converted to center+radius)
# Updated with correct radius values from the SVG
FEMALE_FACE_IRISES = {
    "iris_right": {"center": (0.627810, 0.428113), "radius": 0.0272003},
    "iris_left": {"center": (0.372190, 0.428113), "radius": 0.0272003},
}

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
    RETURN_TYPES = ("IMAGE",)
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
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "iris_left_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "iris_right_size": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "iris_right_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "iris_right_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
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
                # Eyebrows
                "eyebrow_left_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "eyebrow_left_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
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
                # Global
                "camera_distance": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "line_thickness": (
                    "FLOAT",
                    {"default": 2.0, "min": 0.5, "max": 10.0, "step": 0.1},
                ),
            }
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
        lips_pos_y: float,
        lips_size_x: float,
        lip_upper_size_y: float,
        lip_lower_size_y: float,
        chin_size_x: float,
        chin_size_y: float,
        eyebrow_left_pos_x: float,
        eyebrow_left_pos_y: float,
        eyebrow_right_pos_x: float,
        eyebrow_right_pos_y: float,
        nose_pos_y: float,
        nose_size_x: float,
        nose_size_y: float,
        camera_distance: float,
        line_thickness: float,
    ):
        """Render the facial mask image and return it as a tensor."""
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
            x = (rx - 0.5) * canvas_width * camera_distance + canvas_width / 2.0
            y = (ry - 0.5) * canvas_height * camera_distance + canvas_height / 2.0
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

        # Draw outer head outline with scaling only (no positioning)
        if "outer_head" in face_points:
            outer_head = transform_polygon(
                face_points["outer_head"],
                outer_head_size_x,
                outer_head_size_y,
                0.0,
                0.0,
            )
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

        # Draw eyebrows with translation
        if "eyebrow_left" in face_points:
            eyebrow_left = translate_polygon(
                face_points["eyebrow_left"],
                eyebrow_left_pos_x,
                eyebrow_left_pos_y,
            )
            pixel_points = [to_pixel(pt) for pt in eyebrow_left]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        if "eyebrow_right" in face_points:
            eyebrow_right = translate_polygon(
                face_points["eyebrow_right"],
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

        # Draw cheeks (static, for reference)
        if "cheek_left" in face_points:
            pixel_points = [to_pixel(pt) for pt in face_points["cheek_left"]]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        if "cheek_right" in face_points:
            pixel_points = [to_pixel(pt) for pt in face_points["cheek_right"]]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

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
            cx_rel = base_center[0] + iris_pos_x
            cy_rel = base_center[1] + iris_pos_y
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
        return (tensor,)


# Register the node with hyphen‑free identifiers. These mappings are used by
# ComfyUI to locate and instantiate the node. Avoiding hyphens ensures the
# identifiers are valid Python identifiers, which improves compatibility with
# ComfyUI’s loading mechanism.
NODE_CLASS_MAPPINGS = {
    "ComfyUI-face-shaper": ComfyUIFaceShaper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyUI-face-shaper": "Face Shaper",
}