
"""
Advanced Configuration for 4-View Body Measurement System
Customizable parameters for circumference measurements and auto-capture
"""

# ============================================================================
# CAPTURE SETTINGS
# ============================================================================

# Number of views
VIEWS = ["front", "left", "back", "right"]  # 4-view capture

# Frames per view (more = better averaging)
FRAMES_PER_VIEW = 30  # Increased for better accuracy
AUTO_CAPTURE_STABILIZATION_TIME = 0.5  # seconds (15 frames at 30fps)

# Camera settings
CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# ============================================================================
# POSE DETECTION & AUTO-CAPTURE GUIDELINES
# ============================================================================

# Minimum pose quality threshold (0.0 - 1.0)
MIN_VISIBILITY_SCORE = 0.75  # Each joint must be 75% visible
MIN_JOINTS_VISIBLE = 28  # Minimum 28 out of 33 landmarks

# Body positioning guidelines (auto-capture triggers when met)
POSE_GUIDELINES = {
    "body_centered": {
        "enabled": True,
        "description": "Body must be centered in frame",
        "min_x": 100,  # pixels from left
        "max_x": 540   # pixels from right (640-100)
    },
    "body_upright": {
        "enabled": True,
        "description": "Torso must be upright, not bent",
        "min_torso_length": 50  # pixels
    },
    "arms_at_sides": {
        "enabled": True,
        "description": "Arms must be at sides",
        "min_x": 150,
        "max_x": 490  # for 640px width
    },
    "no_rotation": {
        "enabled": True,
        "description": "Body should face camera (not rotated)",
        "max_rotation_deviation": 15  # degrees
    }
}

# ============================================================================
# CAMERA INTRINSICS (Advanced)
# ============================================================================

# Camera focal length (adjust based on your camera)
FOCAL_LENGTH = 1000  # pixels (estimated for standard webcam)

# Principal point (image center)
PRINCIPAL_POINT_X = 320  # Frame center X (for 640px width)
PRINCIPAL_POINT_Y = 240  # Frame center Y (for 480px height)

# ============================================================================
# POSE DETECTION MODEL
# ============================================================================

POSE_MODEL_COMPLEXITY = 1  # 0=lite (fast), 1=full (balanced), 2=heavy (accurate)
SMOOTH_LANDMARKS = True    # Smooth landmarks across frames
MIN_DETECTION_CONFIDENCE = 0.75
MIN_TRACKING_CONFIDENCE = 0.75

# ============================================================================
# CIRCUMFERENCE MEASUREMENT CONFIGURATION
# ============================================================================

# Calibrated ratios for converting width to circumference
CIRCUMFERENCE_RATIOS = {
    "chest": 1.30,      # Width × 1.30 = Circumference
    "waist": 1.35,      # More oval shape at waist
    "hip": 1.35,        # Similar to waist
    "arm": 1.15,        # Arms are more cylindrical
    "thigh": 1.20,      # Thighs are slightly oval
    "calf": 1.15        # Similar to arms
}

# Measurement tolerance (for validation)
MEASUREMENT_TOLERANCE = {
    "chest": (5, 200),      # (min, max) in cm
    "waist": (5, 200),
    "hip": (5, 200),
    "arm": (5, 100),
    "thigh": (5, 150),
    "calf": (5, 120)
}

# ============================================================================
# BODY LANDMARKS (MediaPipe indices)
# ============================================================================

BODY_LANDMARKS = {
    0: "head_top",
    1: "nose",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
    29: "left_foot_index"
}

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

OUTPUT_DIRECTORY = "./measurements"
SAVE_JSON_RESULTS = True
SAVE_LANDMARKS_3D = True
SAVE_DEBUG_FRAMES = False  # Set True to save frames with skeleton overlay

# Output file naming
OUTPUT_FILENAME_FORMAT = "body_measurements_{timestamp}.json"
# {timestamp} will be replaced with ISO format timestamp

# ============================================================================
# DISPLAY & USER INTERFACE
# ============================================================================

SHOW_LIVE_PREVIEW = True       # Show camera feed during capture
SHOW_SKELETON_OVERLAY = True   # Draw skeleton on preview
SHOW_QUALITY_METRICS = True    # Display pose quality score
SHOW_POSITIONING_HINTS = True  # Show guidelines for correct positioning

# Text display settings
FONT_FACE = "HERSHEY_SIMPLEX"
FONT_SCALE = 0.7
FONT_COLOR = (0, 255, 0)       # Green for good pose
FONT_COLOR_WARNING = (0, 165, 255)  # Orange for warnings
FONT_COLOR_ERROR = (0, 0, 255)      # Red for errors

# ============================================================================
# AUTO-CAPTURE BEHAVIOR
# ============================================================================

# Auto-capture mode settings
AUTO_CAPTURE_ENABLED = True
AUTO_CAPTURE_TIMEOUT = 60  # seconds (give up if no valid pose in 60s)
AUTO_CAPTURE_RETRY_COUNT = 2  # Retry if capture fails

# Stabilization requirements before capturing
STABILITY_REQUIRED_FRAMES = 15  # 0.5 seconds at 30fps
STABILITY_MIN_QUALITY = 0.75    # Quality must be above this

# ============================================================================
# ADVANCED: TRIANGULATION SETTINGS
# ============================================================================

# 4-view camera positioning (virtual camera arrangement)
CAMERA_POSITIONS = {
    "front": {
        "rotation_y": 0,
        "position": [0, 0, 0]
    },
    "left": {
        "rotation_y": 90,
        "position": [200, 0, 100]
    },
    "back": {
        "rotation_y": 180,
        "position": [0, 0, 200]
    },
    "right": {
        "rotation_y": -90,
        "position": [-200, 0, 100]
    }
}

# DLT triangulation settings
TRIANGULATION_METHOD = "dlt"  # Direct Linear Transform
OUTLIER_REJECTION = True
OUTLIER_THRESHOLD = 0.5  # pixels

# ============================================================================
# MEASUREMENT VALIDATION
# ============================================================================

# Plausibility checks
VALIDATE_MEASUREMENTS = True

ANTHROPOMETRIC_RATIOS = {
    "shoulder_to_height": (0.35, 0.50),   # Shoulders should be 35-50% of height
    "chest_to_height": (0.35, 0.50),
    "waist_to_height": (0.25, 0.45),
    "hip_to_height": (0.30, 0.55),
    "arm_to_height": (0.25, 0.35),
    "thigh_to_height": (0.35, 0.45),
    "calf_to_height": (0.20, 0.30)
}

# ============================================================================
# DEBUG & LOGGING
# ============================================================================

DEBUG_MODE = False              # Enable verbose logging
VERBOSE_OUTPUT = True           # Print detailed status messages
LOG_POSE_QUALITY = True         # Log pose quality scores
LOG_LANDMARKS = False           # Log landmark coordinates
SAVE_DEBUG_LOG = False          # Save debug information to file

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Threading
USE_THREADING = False  # Process frames in separate thread

# Memory management
CACHE_FRAMES = True    # Cache frames for averaging
MAX_CACHE_SIZE = 100   # Maximum frames to cache

# GPU acceleration (if available)
USE_GPU = False  # Set True if you have CUDA/GPU support

# ============================================================================
# KEYBOARD CONTROLS
# ============================================================================

KEY_CONTINUE = ord('c')  # Press 'c' to skip to next view
KEY_SKIP = ord('s')      # Press 's' to skip view
KEY_QUIT = ord('q')      # Press 'q' to quit

# ============================================================================
# POSITIONING INSTRUCTIONS
# ============================================================================

POSITIONING_INSTRUCTIONS = {
    "front": {
        "position": "Stand facing camera",
        "pose": "Arms at sides, shoulders relaxed",
        "distance": "3-5 feet from camera",
        "duration": "Hold pose for auto-capture (visible for ~3 seconds)"
    },
    "left": {
        "position": "Turn left, show left side to camera",
        "pose": "Arms at sides, shoulders relaxed",
        "distance": "3-5 feet from camera",
        "duration": "Hold pose for auto-capture"
    },
    "back": {
        "position": "Turn around, show back to camera",
        "pose": "Arms at sides, shoulders relaxed",
        "distance": "3-5 feet from camera",
        "duration": "Hold pose for auto-capture"
    },
    "right": {
        "position": "Turn right, show right side to camera",
        "pose": "Arms at sides, shoulders relaxed",
        "distance": "3-5 feet from camera",
        "duration": "Hold pose for auto-capture"
    }
}
