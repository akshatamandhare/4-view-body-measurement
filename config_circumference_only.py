
"""
Circumference-Only Configuration
Minimal config for storing ONLY the 7 key circumference measurements
"""

# MEASUREMENT SETTINGS
MEASUREMENTS_TO_CAPTURE = [
    "chest",         # Full around chest
    "waist",         # Full around waist
    "hip",           # Full around hip/seat
    "biceps_left",   # Full around left bicep
    "biceps_right",  # Full around right bicep
    "forearm_left",  # Full around left forearm
    "forearm_right", # Full around right forearm
    "thigh_left",    # Full around left thigh
    "thigh_right",   # Full around right thigh
    "calf_left",     # Full around left calf
    "calf_right"     # Full around right calf
]

# CAPTURE SETTINGS
FRAMES_PER_VIEW = 30              # Frames per view for averaging
VIEWS = ["front", "left", "back", "right"]  # 4-view capture

# CAMERA SETTINGS
CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# POSE DETECTION
MIN_VISIBILITY_SCORE = 0.75       # Joint visibility threshold
MIN_JOINTS_VISIBLE = 28           # Minimum landmarks required (out of 33)

# AUTO-CAPTURE STABILIZATION
AUTO_CAPTURE_STABILIZATION_TIME = 0.5  # seconds (15 frames at 30fps)

# CIRCUMFERENCE RATIOS - CRITICAL SETTINGS
# Width × Ratio = Circumference
CIRCUMFERENCE_RATIOS = {
    "chest": 1.30,         # Width between shoulders × 1.30
    "waist": 1.35,         # Width at waist × 1.35
    "hip": 1.35,           # Width at hips × 1.35
    "biceps": 1.2,         # Arm measurements
    "forearm": 1.15,       # Forearm measurements
    "thigh": 1.20,         # Thigh measurements
    "calf": 1.15           # Calf measurements
}

# OUTPUT SETTINGS
OUTPUT_DIRECTORY = "./measurements"
SAVE_FORMAT = "json"               # JSON only, compact format

# DISPLAY SETTINGS
SHOW_LIVE_PREVIEW = True
SHOW_SKELETON_OVERLAY = True
SHOW_QUALITY_METRICS = True

# DEBUG
DEBUG_MODE = False
VERBOSE_OUTPUT = True
