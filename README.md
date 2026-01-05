# ComfyUI-face-shaper

A custom ComfyUI node that draws a stylized facial mask (black on white) from SVG-derived coordinates. It lets you resize and reposition the eyes and irises, switch gender presets (currently the female mask is reused for both), change canvas size, camera distance, and line thickness. The output is a single `IMAGE` tensor suitable for further ComfyUI processing.

## Installation

1. Place `face_shaper.py` in your `ComfyUI/custom_nodes/ComfyUI-face-shaper/` folder (or clone this repository into `custom_nodes`).
2. Restart ComfyUI. The node will appear under the `face` category as **Face Shaper**.

## Node inputs

All parameters are exposed under **required**:

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `canvas_width` | INT | 1024 | 256–2048 | Output width in pixels. |
| `canvas_height` | INT | 1024 | 256–2048 | Output height in pixels. |
| `gender` | ENUM | `female` | `female`/`male` | Gender preset (male currently mirrors female data). |
| `eye_left_size_x`, `eye_left_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale left eye width/height. |
| `eye_left_pos_x`, `eye_left_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate left eye relative to its center. |
| `eye_right_size_x`, `eye_right_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale right eye width/height. |
| `eye_right_pos_x`, `eye_right_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate right eye relative to its center. |
| `iris_size` | FLOAT | 1.0 | 0.5–2.0 | Uniform iris radius scaling. |
| `iris_pos_x`, `iris_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate both irises together. |
| `camera_distance` | FLOAT | 1.0 | 0.5–2.0 | Global zoom (scales all features). |
| `line_thickness` | FLOAT | 2.0 | 0.5–10.0 | Stroke width for all lines. |

## Output

A single `IMAGE` tensor shaped `[1, H, W, 3]`, with black lines on a white background. Use it as conditioning, masking, or as a guide image in your ComfyUI workflows. Future updates may add dedicated male coordinates and more feature controls.
