# ComfyUI-face-shaper

A custom ComfyUI node that draws a parametric facial mask with black lines on a white background. The node provides extensive control over individual facial features including eyes, irises, head outline, lips, eyebrows, and nose parts, all derived from SVG coordinates.

## Features

- **Separated iris controls**: Independent size and position controls for left and right irises
- **Head outline scaling**: Adjust head width and height independently
- **Lips sizing**: Control upper and lower lip dimensions separately
- **Eyebrow positioning**: Fine-tune left and right eyebrow positions
- **Nose part positioning**: Adjust nose bridge, sidewalls, and aler (nostrils) independently
- **Eye controls**: Scale and position each eye independently
- **Canvas customization**: Configurable canvas size (256-2048px)
- **Camera distance**: Global zoom control (0.5-2.0x)
- **Line thickness**: Adjustable stroke width (0.5-10.0)
- **Gender presets**: Female and male options (currently both use female coordinates)

## Installation

1. Clone or download this repository into your `ComfyUI/custom_nodes/` directory:
   ```bash
   cd ComfyUI/custom_nodes/
   git clone https://github.com/EricRorich/ComfyUI-face-shaper.git
   ```

2. Restart ComfyUI. The node will appear under the `face` category as **Face Shaper**.

## Node Parameters

All parameters are exposed under the **required** section:

### Canvas Settings
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `canvas_width` | INT | 1024 | 256–2048 | Output width in pixels |
| `canvas_height` | INT | 1024 | 256–2048 | Output height in pixels |
| `gender` | ENUM | `female` | `female`/`male` | Gender preset (male currently uses female data) |

### Eye Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `eye_left_size_x` | FLOAT | 1.0 | 0.5–2.0 | Scale left eye width |
| `eye_left_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale left eye height |
| `eye_left_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate left eye horizontally |
| `eye_left_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate left eye vertically |
| `eye_right_size_x` | FLOAT | 1.0 | 0.5–2.0 | Scale right eye width |
| `eye_right_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale right eye height |
| `eye_right_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate right eye horizontally |
| `eye_right_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate right eye vertically |

### Iris Controls (Separated)
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `iris_left_size` | FLOAT | 1.0 | 0.5–2.0 | Scale left iris radius |
| `iris_left_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate left iris horizontally |
| `iris_left_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate left iris vertically |
| `iris_right_size` | FLOAT | 1.0 | 0.5–2.0 | Scale right iris radius |
| `iris_right_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate right iris horizontally |
| `iris_right_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate right iris vertically |

### Head Outline Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `head_size_x` | FLOAT | 1.0 | 0.5–2.0 | Scale head outline width |
| `head_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale head outline height |

### Lips Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `lips_upper_size_x` | FLOAT | 1.0 | 0.5–2.0 | Scale upper lip width |
| `lips_upper_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale upper lip height |
| `lips_lower_size_x` | FLOAT | 1.0 | 0.5–2.0 | Scale lower lip width |
| `lips_lower_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale lower lip height |

### Eyebrow Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `eyebrow_left_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate left eyebrow horizontally |
| `eyebrow_left_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate left eyebrow vertically |
| `eyebrow_right_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate right eyebrow horizontally |
| `eyebrow_right_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate right eyebrow vertically |

### Nose Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `nose_aler_left_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate left nostril/aler horizontally |
| `nose_aler_left_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate left nostril/aler vertically |
| `nose_aler_right_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate right nostril/aler horizontally |
| `nose_aler_right_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate right nostril/aler vertically |
| `nose_sidewall_left_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate left nose sidewall horizontally |
| `nose_sidewall_left_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate left nose sidewall vertically |
| `nose_sidewall_right_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate right nose sidewall horizontally |
| `nose_sidewall_right_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate right nose sidewall vertically |
| `nose_bridge_left_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate left nose bridge horizontally |
| `nose_bridge_left_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate left nose bridge vertically |
| `nose_bridge_right_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate right nose bridge horizontally |
| `nose_bridge_right_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate right nose bridge vertically |

### Global Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `camera_distance` | FLOAT | 1.0 | 0.5–2.0 | Global zoom factor for all features |
| `line_thickness` | FLOAT | 2.0 | 0.5–10.0 | Stroke width for all lines |

## Output

The node outputs a single `IMAGE` tensor with shape `[1, H, W, 3]`, featuring:
- **White background** (RGB 255, 255, 255)
- **Black line drawings** (RGB 0, 0, 0)
- **Float32 format** normalized to 0.0-1.0 range

This output can be used as:
- Conditioning input for other nodes
- Masking or guide images
- Base for further image processing in ComfyUI workflows

## Usage Example

1. Add the **Face Shaper** node from the `face` category
2. Connect the output to any node that accepts IMAGE tensors
3. Adjust parameters to customize the facial features:
   - Increase `iris_left_size` and `iris_right_size` for larger irises
   - Adjust `eyebrow_left_pos_y` and `eyebrow_right_pos_y` to raise/lower eyebrows
   - Scale `lips_upper_size_x` for wider lips
   - Modify `head_size_x` and `head_size_y` for different face shapes

## Coordinate System

All position parameters use a relative coordinate system:
- **0.0** = center position (no translation)
- **Positive values** = move right (x) or down (y)
- **Negative values** = move left (x) or up (y)
- Position values are fractions of canvas dimensions

All size parameters are multipliers:
- **1.0** = original size
- **< 1.0** = smaller
- **> 1.0** = larger

## Technical Details

- **Coordinate transform**: Relative coordinates (0-1 range) are converted to pixel coordinates using: 
  - `x = (rx - 0.5) * canvas_width * camera_distance + canvas_width / 2`
  - `y = (ry - 0.5) * canvas_height * camera_distance + canvas_height / 2`
- **Feature transforms**: Each feature group (eyes, lips, nose parts, etc.) has its own transformation applied before pixel conversion
- **Drawing method**: Uses PIL (Pillow) to draw polylines and circles, then converts to PyTorch tensor

## Future Improvements

- [ ] Add dedicated male coordinate data (currently uses female coordinates for both genders)
- [ ] Add more granular control over additional facial features
- [ ] Support for custom color schemes (currently fixed to black on white)
- [ ] Animation support with keyframe interpolation
- [ ] Export/import custom face templates

## Requirements

- ComfyUI
- Python packages (typically included with ComfyUI):
  - `torch`
  - `numpy`
  - `PIL` (Pillow)

## License

This project follows the same license as ComfyUI.

## Credits

Coordinates derived from SVG face mask templates. This is a custom node implementation for the ComfyUI framework.
