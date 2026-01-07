/**
 * ComfyUI Face Shaper Reset Extension
 * 
 * This extension adds a "Reset to Defaults" button to the Face Shaper node
 * that resets all widget values back to their INPUT_TYPES default values.
 */

import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "RORICH.FaceShaper.Reset",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Only register for the Face Shaper node (display name: "Face Shaper")
        if (nodeData.display_name === "Face Shaper" || nodeData.name === "RORICH-AI") {
            // Store the original onNodeCreated callback
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function() {
                // Call the original onNodeCreated if it exists
                const result = onNodeCreated?.apply(this, arguments);
                
                // Add a reset button to the node
                this.addWidget("button", "Reset to Defaults", null, () => {
                    // Define the default values according to INPUT_TYPES
                    const defaults = {
                        "canvas_width": 1024,
                        "canvas_height": 1024,
                        "gender": "female",
                        "transparent_background": false,
                        "eye_left_size_x": 1.0,
                        "eye_left_size_y": 1.0,
                        "eye_left_pos_x": 0.0,
                        "eye_left_pos_y": 0.0,
                        "eye_right_size_x": 1.0,
                        "eye_right_size_y": 1.0,
                        "eye_right_pos_x": 0.0,
                        "eye_right_pos_y": 0.0,
                        "iris_left_size": 1.0,
                        "iris_left_pos_x": 0.0,
                        "iris_left_pos_y": 0.0,
                        "iris_right_size": 1.0,
                        "iris_right_pos_x": 0.0,
                        "iris_right_pos_y": 0.0,
                        "outer_head_size_x": 1.0,
                        "outer_head_size_y": 1.0,
                        "jaw_size_x": 1.0,
                        "forehead_size_x": 1.0,
                        "lips_pos_y": 0.0,
                        "lips_size_x": 1.0,
                        "lip_upper_size_y": 1.0,
                        "lip_lower_size_y": 1.0,
                        "chin_size_x": 1.0,
                        "chin_size_y": 1.0,
                        "cheek_left_pos_x": 0.0,
                        "cheek_left_pos_y": 0.0,
                        "cheek_right_pos_x": 0.0,
                        "cheek_right_pos_y": 0.0,
                        "eyebrow_left_size_x": 1.0,
                        "eyebrow_left_size_y": 1.0,
                        "eyebrow_left_rotation": 0.0,
                        "eyebrow_left_pos_x": 0.0,
                        "eyebrow_left_pos_y": 0.0,
                        "eyebrow_right_size_x": 1.0,
                        "eyebrow_right_size_y": 1.0,
                        "eyebrow_right_rotation": 0.0,
                        "eyebrow_right_pos_x": 0.0,
                        "eyebrow_right_pos_y": 0.0,
                        "nose_pos_y": 0.0,
                        "nose_size_x": 1.0,
                        "nose_size_y": 1.0,
                        "camera_distance": 1.0,
                        "camera_pos_x": 0.0,
                        "camera_pos_y": 0.0,
                        "line_thickness": 2.0,
                    };
                    
                    // Reset all widgets to their default values
                    for (const widget of this.widgets) {
                        if (widget.name in defaults) {
                            widget.value = defaults[widget.name];
                        }
                    }
                    
                    // Trigger a graph update to refresh the canvas
                    if (this.onResize) {
                        this.onResize(this.size);
                    }
                    
                    // Mark the graph as changed so ComfyUI knows to re-execute
                    app.graph.setDirtyCanvas(true, true);
                });
                
                return result;
            };
        }
    }
});
