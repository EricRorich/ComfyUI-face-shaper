"""
Updated package initializer for the ComfyUI Face Shaper custom node.

This version adjusts the import to match the renamed module `face_shaper.py`.
Place this file as `__init__.py` in your `ComfyUI-face-shaper` folder to
register the node correctly.
"""

from .face_shaper import ComfyUIFaceShaper

# Mappings used by ComfyUI to locate and display the node.
NODE_CLASS_MAPPINGS = {
    "RORICH-AI": ComfyUIFaceShaper,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RORICH-AI": "Face Shaper",
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "ComfyUIFaceShaper",
]