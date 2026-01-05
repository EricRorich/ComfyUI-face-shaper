from typing import Dict, List, Tuple

import numpy as np
import torch
from PIL import Image, ImageDraw

# relative coordinates for female face (0–1 range)
FEMALE_FACE: Dict[str, List[Tuple[float, float]]] = {
    "eye_right": [
        (0.587679, 0.449786),
        (0.653864, 0.474606),
        (0.723844, 0.449786),
        (0.695229, 0.412257),
        (0.711775, 0.43324),
        (0.723844, 0.449786),
        (0.587679, 0.449786),
        (0.653864, 0.400148),
        (0.695229, 0.412257),
    ],
    "eye_left": [
        (0.412321, 0.449786),
        (0.346136, 0.474606),
        (0.276156, 0.449786),
        (0.304771, 0.412257),
        (0.288225, 0.43324),
        (0.276156, 0.449786),
        (0.412321, 0.449786),
        (0.346136, 0.400148),
        (0.304771, 0.412257),
    ],
    "brow_right": [
        (0.568969, 0.38345),
        (0.721171, 0.333225),
        (0.792342, 0.386617),
        (0.721472, 0.361798),
        (0.585515, 0.406908),
    ],
    "brow_left": [
        (0.431031, 0.38345),
        (0.278829, 0.333225),
        (0.207658, 0.386617),
        (0.278528, 0.361798),
        (0.414485, 0.406908),
    ],
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
    "jaw_right": [
        (0.608616, 0.82843),
        (0.532223, 0.800273),
        (0.5, 0.800273),
        (0.611373, 0.904394),
        (0.625626, 0.852528),
        (0.608616, 0.82843),
        (0.559464, 0.828789),
        (0.58201, 0.926529),
        (0.594625, 0.880454),
        (0.559464, 0.828789),
        (0.5, 0.828789),
        (0.554594, 0.935787),
        (0.569026, 0.890426),
        (0.540844, 0.851369),
        (0.5, 0.838925),
    ],
    "jaw_left": [
        (0.391384, 0.82843),
        (0.467777, 0.800273),
        (0.5, 0.800273),
        (0.388628, 0.904394),
        (0.374374, 0.852528),
        (0.391384, 0.82843),
        (0.440536, 0.828789),
        (0.41799, 0.926529),
        (0.405375, 0.880454),
        (0.440536, 0.828789),
        (0.5, 0.828789),
        (0.445406, 0.935787),
        (0.430974, 0.890426),
        (0.459156, 0.851369),
        (0.5, 0.838925),
    ],
    "mouth_top_right": [
        (0.5, 0.736025),
        (0.524265, 0.726097),
        (0.608079, 0.753943),
        (0.555702, 0.754226),
        (0.540811, 0.749262),
        (0.5, 0.764153),
    ],
    "mouth_top_left": [
        (0.5, 0.736025),
        (0.475736, 0.726097),
        (0.391922, 0.753943),
        (0.444298, 0.754226),
        (0.459189, 0.749262),
        (0.5, 0.764153),
    ],
    "mouth_bottom_right": [
        (0.499984, 0.762932),
        (0.541349, 0.750634),
        (0.557895, 0.754981),
        (0.541349, 0.750634),
        (0.549622, 0.800273),
        (0.607534, 0.754258),
        (0.557895, 0.754981),
        (0.499984, 0.800273),
        (0.549622, 0.800273),
    ],
    "mouth_bottom_left": [
        (0.499984, 0.762932),
        (0.458618, 0.750634),
        (0.442072, 0.754981),
        (0.458618, 0.750634),
        (0.450345, 0.800273),
        (0.392433, 0.754258),
        (0.442072, 0.754981),
        (0.499984, 0.800273),
        (0.450345, 0.800273),
    ],
    "nose_bridge_right": [
        (0.544149, 0.629847),
        (0.525524, 0.579209),
        (0.524094, 0.441927),
        (0.546532, 0.412688),
        (0.568969, 0.38345),
    ],
    "nose_bridge_left": [
        (0.455851, 0.629847),
        (0.474476, 0.579209),
        (0.475906, 0.441927),
        (0.453468, 0.412688),
        (0.431031, 0.38345),
    ],
    "nose_side_right": [
        (0.544149, 0.629847),
        (0.54197, 0.465522),
        (0.585515, 0.406908),
    ],
    "nose_side_left": [
        (0.455851, 0.629847),
        (0.45803, 0.465522),
        (0.414485, 0.406908),
    ],
    "nose_bottom_right": [
        (0.5, 0.671066),
        (0.550785, 0.636907),
        (0.544459, 0.655884),
        (0.569762, 0.648926),
        (0.571659, 0.619195),
        (0.544459, 0.542654),
    ],
    "nose_bottom_left": [
        (0.5, 0.671066),
        (0.449215, 0.636907),
        (0.455541, 0.655884),
        (0.430238, 0.648926),
        (0.428341, 0.619195),
        (0.455541, 0.542654),
    ],
    "nostrils": [
        (0.5, 0.643776),
        (0.455851, 0.629847),
        (0.5, 0.643776),
        (0.544149, 0.629847),
    ],
}

FEMALE_FACE_IRISES = {
    "iris_right": {"center": (0.6278103, 0.4281128), "radius": 0.0272003},
    "iris_left": {"center": (0.3721897, 0.4281128), "radius": 0.0272003},
}

# TODO: replace with male-specific coordinates once available; currently reuses female data.
MALE_FACE = FEMALE_FACE
MALE_FACE_IRISES = FEMALE_FACE_IRISES


class ComfyUIFaceShaper:
    CATEGORY = "face"
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "draw_face"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "canvas_width": ("INT", {"default": 1024, "min": 256, "max": 2048}),
                "canvas_height": ("INT", {"default": 1024, "min": 256, "max": 2048}),
                "gender": (["female", "male"],),
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
                "iris_size": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01},
                ),
                "iris_pos_x": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
                "iris_pos_y": (
                    "FLOAT",
                    {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01},
                ),
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
        eye_left_size_x: float,
        eye_left_size_y: float,
        eye_left_pos_x: float,
        eye_left_pos_y: float,
        eye_right_size_x: float,
        eye_right_size_y: float,
        eye_right_pos_x: float,
        eye_right_pos_y: float,
        iris_size: float,
        iris_pos_x: float,
        iris_pos_y: float,
        camera_distance: float,
        line_thickness: float,
    ):
        face_points = FEMALE_FACE if gender == "female" else MALE_FACE
        iris_data = FEMALE_FACE_IRISES if gender == "female" else MALE_FACE_IRISES

        img = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(img)
        # Pillow line/ellipse drawing uses integer stroke widths; round and enforce a minimum of 1 so lines stay visible.
        stroke_width = max(1, int(round(line_thickness)))

        def to_pixel(point: Tuple[float, float]) -> Tuple[float, float]:
            rx, ry = point
            x = (rx - 0.5) * canvas_width * camera_distance + canvas_width / 2.0
            y = (ry - 0.5) * canvas_height * camera_distance + canvas_height / 2.0
            return (x, y)

        skip_prefixes = ("eye", "iris")
        static_keys = [
            key
            for key in face_points.keys()
            if not any(key.startswith(prefix) for prefix in skip_prefixes)
        ]

        for key in static_keys:
            polyline = face_points[key]
            pixel_points = [to_pixel(pt) for pt in polyline]
            draw.line(pixel_points, fill=(0, 0, 0), width=stroke_width)

        def transform_eye(
            points: List[Tuple[float, float]],
            scale_x: float,
            scale_y: float,
            offset_x: float,
            offset_y: float,
        ) -> List[Tuple[float, float]]:
            # Feature point counts are tiny; simple mean math avoids extra numpy overhead.
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

        eye_right = transform_eye(
            face_points["eye_right"],
            eye_right_size_x,
            eye_right_size_y,
            eye_right_pos_x,
            eye_right_pos_y,
        )
        eye_left = transform_eye(
            face_points["eye_left"],
            eye_left_size_x,
            eye_left_size_y,
            eye_left_pos_x,
            eye_left_pos_y,
        )

        draw.line([to_pixel(pt) for pt in eye_right], fill=(0, 0, 0), width=stroke_width)
        draw.line([to_pixel(pt) for pt in eye_left], fill=(0, 0, 0), width=stroke_width)

        def draw_iris(center_key: str):
            base_center = iris_data[center_key]["center"]
            base_radius = iris_data[center_key]["radius"]
            cx_rel = base_center[0] + iris_pos_x
            cy_rel = base_center[1] + iris_pos_y
            cx, cy = to_pixel((cx_rel, cy_rel))
            # Use the smaller canvas dimension so the circular iris stays round across aspect ratios.
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

        draw_iris("iris_right")
        draw_iris("iris_left")

        # ComfyUI expects a [B, H, W, C] float tensor in RGB order (B=1 here); simple numpy→torch keeps the data contiguous.
        arr = np.array(img).astype(np.float32) / 255.0
        tensor = torch.from_numpy(arr).unsqueeze(0)
        return (tensor,)


NODE_CLASS_MAPPINGS = {
    "ComfyUI-face-shaper": ComfyUIFaceShaper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyUI-face-shaper": "Face Shaper",
}
