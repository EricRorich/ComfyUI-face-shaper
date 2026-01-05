# ComfyUI-face-shaper

A custom ComfyUI node that draws a parametric facial mask with black lines on either a white or transparent background. The node provides extensive control over individual facial features including outer head outline, eyes, irises, eyebrows, nose parts, lips, chin, and cheeks. All coordinates are derived from an SVG face mask template with normalized [0-1] relative positioning.

## Features

- **21 distinct facial features** extracted from Face_Mask_female.svg (1024×1024)
- **Transparent background option**: Choose between black lines on white background (default) or black lines on transparent background (RGBA output)
- **Outer head outline**: Full face contour with independent scaling (no positioning controls)
- **Lips controls**: 4 separate lips shapes (upper/lower, left/right) with unified size and y-position controls
- **Chin polygon**: Dedicated chin shape with scaling only (no positioning controls)
- **Separated iris controls**: Independent size and position controls for left and right irises
- **Eye controls**: Scale and position each eye independently
- **Eyebrow positioning**: Fine-tune left and right eyebrow positions
- **Nose part positioning**: Adjust nose bridge, sidewalls, alae (nostril wings), and tip independently
- **Canvas customization**: Configurable canvas size (256-2048px)
- **Camera distance**: Global zoom control (0.5-2.0x)
- **Line thickness**: Adjustable stroke width (0.5-10.0)
- **Gender presets**: Female and male options (currently both use female coordinates)
- **Per-feature scaling**: Each feature group has its own scaling controls to prevent distortion
- **Zero default offsets**: All position parameters default to 0.0 for neutral alignment

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
| `transparent_background` | BOOLEAN | `false` | `true`/`false` | Use transparent background instead of white |

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

### Outer Head Outline Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `outer_head_size_x` | FLOAT | 1.0 | 0.5–2.0 | Scale outer head width |
| `outer_head_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale outer head height |

### Lips Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `lips_size_x` | FLOAT | 1.0 | 0.5–2.0 | Scale lips width (applies to all 4 parts) |
| `lips_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale lips height (applies to all 4 parts) |
| `lips_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate lips vertically |

### Chin Controls
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `chin_size_x` | FLOAT | 1.0 | 0.5–2.0 | Scale chin width |
| `chin_size_y` | FLOAT | 1.0 | 0.5–2.0 | Scale chin height |

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
| `nose_aler_left_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate left nostril alae horizontally |
| `nose_aler_left_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate left nostril alae vertically |
| `nose_aler_right_pos_x` | FLOAT | 0.0 | -0.5–0.5 | Translate right nostril alae horizontally |
| `nose_aler_right_pos_y` | FLOAT | 0.0 | -0.5–0.5 | Translate right nostril alae vertically |
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

The node outputs a single `IMAGE` tensor with shape `[1, H, W, C]`, featuring:
- **White or transparent background** (RGB 255,255,255 or RGBA 255,255,255,0 depending on `transparent_background` setting)
- **Black line drawings** (RGB/RGBA 0,0,0 with full opacity)
- **Float32 format** normalized to 0.0-1.0 range
- **3 channels (RGB)** when `transparent_background` is false
- **4 channels (RGBA)** when `transparent_background` is true

This output can be used as:
- Conditioning input for other nodes
- Masking or guide images
- Base for further image processing in ComfyUI workflows
- Alpha-aware compositing when using transparent background

## Usage Example

1. Add the **Face Shaper** node from the `face` category
2. Connect the output to any node that accepts IMAGE tensors
3. Adjust parameters to customize the facial features:
   - Enable `transparent_background` for RGBA output with alpha channel
   - Increase `iris_left_size` and `iris_right_size` for larger irises
   - Adjust `eyebrow_left_pos_y` and `eyebrow_right_pos_y` to raise/lower eyebrows
   - Scale `lips_size_x` and `lips_size_y` for different lips sizes
   - Modify `outer_head_size_x` and `outer_head_size_y` for different head shapes
   - Adjust `lips_pos_y` to move the lips up or down

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

- **Coordinate extraction**: All 21 paths extracted from Face_Mask_female.svg (1024×1024) with coordinates normalized to [0-1] range
- **Coordinate transform**: Relative coordinates (0-1 range) are converted to pixel coordinates using: 
  - `x = (rx - 0.5) * canvas_width * camera_distance + canvas_width / 2`
  - `y = (ry - 0.5) * canvas_height * camera_distance + canvas_height / 2`
- **Feature transforms**: Each feature group (eyes, moustache, chin, outer_head, etc.) has its own transformation applied before pixel conversion to avoid cross-feature distortion
- **Drawing method**: Uses PIL (Pillow) to draw polylines and circles, then converts to PyTorch tensor
- **Per-feature scaling**: Scaling parameters are scoped to their respective features only

## Facial Features Included

The node renders 21 distinct SVG paths organized into feature groups:

1. **Outer head** (20 points) - Full face outline contour with scaling only
2. **Cheeks** (left: 4 points, right: 4 points) - Static cheek contours
3. **Chin** (7 points) - Lower jaw polygon with scaling only
4. **Lips** (4 shapes: upper-left, upper-right, lower-left, lower-right; 6 points each) - Mouth/lips area
5. **Eyes** (left: 6 points, right: 6 points) - Eye outlines
6. **Irises** (left: circle, right: circle) - Pupil/iris circles
7. **Eyebrows** (left: 5 points, right: 5 points) - Eyebrow curves
8. **Nose bridge** (left: 5 points, right: 5 points) - Upper nose lines
9. **Nose sidewalls** (left: 3 points, right: 3 points) - Side of nose
10. **Nose alae** (left: 6 points, right: 6 points) - Nostril wing areas
11. **Nose tip** (4 points) - Nose bottom connector

## Future Improvements

- [ ] Add dedicated male coordinate data (currently uses female coordinates for both genders)
- [ ] Add more granular control over additional facial features
- [ ] Animation support with keyframe interpolation
- [ ] Export/import custom face templates

## Recent Changes

### Version with Transparent Background and Lips Renaming
- Added `transparent_background` boolean parameter to choose between white (RGB) or transparent (RGBA) background
- Renamed "moustache" features to "lips" for more accurate naming (lips_upper_left, lips_upper_right, lips_lower_left, lips_lower_right)
- Removed `moustache_pos_x` parameter (only y-position control retained for lips)
- Removed `outer_head_pos_x` and `outer_head_pos_y` parameters (scaling only)
- Removed `chin_pos_x` and `chin_pos_y` parameters (scaling only)
- Simplified parameter set while maintaining essential controls for eyes, irises, eyebrows, and nose parts

## Requirements

- ComfyUI
- Python packages (typically included with ComfyUI):
  - `torch`
  - `numpy`
  - `PIL` (Pillow)

## License

This project follows the same license as ComfyUI.

## Credits

Coordinates derived from Face_Mask_female.svg template (1024×1024). This is a custom node implementation for the ComfyUI framework.
