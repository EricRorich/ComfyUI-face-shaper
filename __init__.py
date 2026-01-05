"""
Package initializer for the ComfyUI Face Shaper custom node.

This module registers the `ComfyUIFaceShaper` node with ComfyUI. When the
`ComfyUI-face-shaper` directory is placed in ComfyUI’s `custom_nodes` folder,
ComfyUI will import this `__init__.py`, discover the node mappings, and make
the node available in the UI.
"""

from .face_shaper_fixed import ComfyUIFaceShaper

# Mappings used by ComfyUI to locate and display the node.
NODE_CLASS_MAPPINGS = {
    "ComfyUIFaceShaper": ComfyUIFaceShaper,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyUIFaceShaper": "Face Shaper",
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "ComfyUIFaceShaper",
]