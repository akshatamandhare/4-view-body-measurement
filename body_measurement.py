
"""
Optimized 4-View Body Measurement System - Circumference Only
Stores ONLY: Chest, Waist, Hip (seat), Biceps, Forearms, Thighs, Calfs
Minimal, focused measurement system for body tracking
"""

import cv2
import numpy as np
import json
import time
from pathlib import Path
from datetime import datetime
from collections import deque
import mediapipe as mp

class CircumferenceOnlyReconstructor:
    """
    Optimized body measurement system - circumference measurements only
    Captures: Front, Left, Back, Right
    Stores: chest, waist, hip, biceps, forearm, thigh, calf (both sides)
    """

    def __init__(self, user_height_cm: float, output_dir: str = "./measurements"):
        self.user_height_cm = user_height_cm
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75
        )

        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(
            thickness=2, circle_radius=1, color=(0, 255, 0)
        )

        # 4-View capture
        self.views = ["front", "left", "back", "right"]
        self.frames_per_view = 30
        self.landmarks_buffer = {
            "front": None,
            "left": None,
            "back": None,
            "right": None
        }

        # Camera intrinsics
        self.focal_length = 1000
        self.principal_point = None

        # Pose quality
        self.min_visibility_score = 0.75
        self.min_joints_visible = 28

        # CIRCUMFERENCE MEASUREMENTS ONLY - Simplified
        self.CIRCUMFERENCE_POINTS = {
            "chest": {
                "indices": (11, 12),        # Left & right shoulder
                "ratio": 1.30,              # Width to circumference
                "description": "Chest (shoulders)"
            },
            "waist": {
                "indices": (23, 24),        # Left & right hip
                "ratio": 1.35,
                "description": "Waist (hips)"
            },
            "hip": {
                "indices": (23, 24),        # Same as waist (seat)
                "ratio": 1.35,
                "description": "Hip/Seat"
            },
            "biceps_left": {
                "indices": (11, 13),        # Left shoulder to elbow (approx)
                "ratio": 1.2,
                "description": "Biceps (left arm)"
            },
            "biceps_right": {
                "indices": (12, 14),        # Right shoulder to elbow
                "ratio": 1.2,
                "description": "Biceps (right arm)"
            },
            "forearm_left": {
                "indices": (13, 15),        # Left elbow to wrist
                "ratio": 1.15,
                "description": "Forearm (left)"
            },
            "forearm_right": {
                "indices": (14, 16),        # Right elbow to wrist
                "ratio": 1.15,
                "description": "Forearm (right)"
            },
            "thigh_left": {
                "indices": (23, 25),        # Left hip to knee
                "ratio": 1.20,
                "description": "Thigh (left)"
            },
            "thigh_right": {
                "indices": (24, 26),        # Right hip to knee
                "ratio": 1.20,
                "description": "Thigh (right)"
            },
            "calf_left": {
                "indices": (25, 27),        # Left knee to ankle
                "ratio": 1.15,
                "description": "Calf (left)"
            },
            "calf_right": {
                "indices": (26, 28),        # Right knee to ankle
                "ratio": 1.15,
                "description": "Calf (right)"
            }
        }

        # Final measurements (circumference only)
        self.measurements = {}
        self.capture_complete = False

    def detect_pose(self, frame):
        """Detect pose landmarks"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        return results

    def extract_landmarks_2d(self, results, frame_shape):
        """Extract 2D landmarks from pose"""
        if not results.pose_landmarks:
            return None

        height, width = frame_shape[:2]
        landmarks_2d = []

        for landmark in results.pose_landmarks.landmark:
            if landmark.visibility > self.min_visibility_score:
                landmarks_2d.append({
                    "x": landmark.x * width,
                    "y": landmark.y * height,
                    "z": landmark.z,
                    "visibility": landmark.visibility
                })
            else:
                landmarks_2d.append(None)

        return landmarks_2d

    def assess_pose_quality(self, landmarks_2d):
        """Quick pose quality check"""
        if landmarks_2d is None:
            return False, 0.0, ["No landmarks detected"]

        issues = []
        valid_landmarks = sum(1 for l in landmarks_2d if l is not None)

        if valid_landmarks < self.min_joints_visible:
            issues.append(f"Not enough joints: {valid_landmarks}/{self.min_joints_visible}")
            return False, 0.0, issues

        # Check if body centered
        if landmarks_2d[0] is not None:
            head_x = landmarks_2d[0]["x"]
            if head_x < 100 or head_x > 540:
                issues.append("Head not centered")

        # Check if torso upright
        if landmarks_2d[11] and landmarks_2d[23]:
            shoulder_y = landmarks_2d[11]["y"]
            hip_y = landmarks_2d[23]["y"]
            if abs(shoulder_y - hip_y) < 50:
                issues.append("Stand upright")

        visibility_scores = [l["visibility"] for l in landmarks_2d if l is not None]
        quality_score = np.mean(visibility_scores) if visibility_scores else 0.0

        is_valid = len(issues) == 0 and quality_score > 0.7

        return is_valid, quality_score, issues

    def auto_capture_view(self, view_name, cap):
        """Auto-capture single view"""
        print(f"\n{'='*70}")
        print(f"CAPTURING {view_name.upper()} VIEW")
        print(f"{'='*70}")

        instructions = {
            "front": "Stand facing camera, arms at sides",
            "left": "Turn left 90°, show left side",
            "back": "Turn around, show back to camera",
            "right": "Turn right 90°, show right side"
        }

        print(f"Position: {instructions.get(view_name, '')}")
        print(f"Waiting for correct pose... (auto-capture in ~3 seconds)\n")

        frame_count = 0
        valid_landmarks_list = []
        pose_stable_count = 0
        pose_stable_threshold = 15
        auto_capture_started = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            self.principal_point = (frame.shape[1] / 2, frame.shape[0] / 2)

            results = self.detect_pose(frame)
            landmarks_2d = self.extract_landmarks_2d(results, frame.shape)
            is_valid, quality_score, issues = self.assess_pose_quality(landmarks_2d)

            # Draw skeleton
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                    self.drawing_spec, self.drawing_spec
                )

            # Update stability
            if is_valid:
                pose_stable_count += 1
                if not auto_capture_started and pose_stable_count >= pose_stable_threshold:
                    auto_capture_started = True
                    print(f"✓ Pose stable! Starting auto-capture...")
                    print(f"  Capturing {self.frames_per_view} frames...", end="", flush=True)
            else:
                if auto_capture_started:
                    auto_capture_started = False
                    frame_count = 0
                    valid_landmarks_list = []
                    print(f"\n✗ Pose moved. Restarting...\n")
                pose_stable_count = 0

            # Auto-capture frames
            if auto_capture_started:
                if landmarks_2d and all(l is not None for l in landmarks_2d):
                    valid_landmarks_list.append(landmarks_2d)
                    frame_count += 1
                    if frame_count % 10 == 0:
                        print(".", end="", flush=True)

                    if frame_count >= self.frames_per_view:
                        print(f" Done!")
                        print(f"✓ {view_name.upper()} captured: {len(valid_landmarks_list)} frames")
                        break

            # Display status
            status_text = f"Quality: {quality_score:.1%}"
            color = (0, 255, 0) if is_valid else (0, 0, 255)
            cv2.putText(frame, status_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            if auto_capture_started:
                progress = int((frame_count / self.frames_per_view) * 100)
                cv2.putText(frame, f"Capturing: {progress}%", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            elif issues:
                y_pos = 70
                for issue in issues[:2]:
                    cv2.putText(frame, f"⚠ {issue}", (10, y_pos),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
                    y_pos += 25

            cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0]-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.imshow(f"Body Measurement - {view_name.upper()}", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                cv2.destroyAllWindows()
                self.capture_complete = True
                return False, None
            elif key == ord('s'):
                break

        cv2.destroyAllWindows()

        if valid_landmarks_list:
            averaged = self._average_landmarks(valid_landmarks_list)
            return True, averaged
        else:
            return False, None

    def _average_landmarks(self, landmarks_list):
        """Average landmarks across frames"""
        if not landmarks_list:
            return None

        num_landmarks = len(landmarks_list[0])
        averaged = []

        for idx in range(num_landmarks):
            valid_points = [
                frame[idx] for frame in landmarks_list
                if frame[idx] is not None
            ]

            if valid_points:
                avg_x = np.mean([p["x"] for p in valid_points])
                avg_y = np.mean([p["y"] for p in valid_points])
                avg_z = np.mean([p["z"] for p in valid_points])
                avg_visibility = np.mean([p["visibility"] for p in valid_points])

                averaged.append({
                    "x": float(avg_x),
                    "y": float(avg_y),
                    "z": float(avg_z),
                    "visibility": float(avg_visibility)
                })
            else:
                averaged.append(None)

        return averaged

    def triangulate_4view(self, front, left, back, right):
        """Simple 4-view triangulation"""
        if not all([front, left, back, right]):
            return None

        landmarks_3d = []
        num_landmarks = len(front)

        for idx in range(num_landmarks):
            p_front = front[idx]
            p_left = left[idx]
            p_back = back[idx]
            p_right = right[idx]

            if all([p_front, p_left, p_back, p_right]):
                # Simple average of 4-view positions (basic triangulation)
                x = (p_front["x"] + p_left["x"] + p_back["x"] + p_right["x"]) / 4
                y = (p_front["y"] + p_left["y"] + p_back["y"] + p_right["y"]) / 4
                z = (p_front["z"] + p_left["z"] + p_back["z"] + p_right["z"]) / 4

                landmarks_3d.append({"x": x, "y": y, "z": z})
            else:
                landmarks_3d.append(None)

        return landmarks_3d

    def calculate_circumference_only(self, landmarks_3d):
        """Calculate ONLY circumference measurements"""
        if landmarks_3d is None:
            return None

        measurements = {}

        # Get scale factor from height
        if landmarks_3d[0] and landmarks_3d[29]:
            height_pixels = np.sqrt(
                (landmarks_3d[0]["x"] - landmarks_3d[29]["x"])**2 +
                (landmarks_3d[0]["y"] - landmarks_3d[29]["y"])**2 +
                (landmarks_3d[0]["z"] - landmarks_3d[29]["z"])**2
            )
            scale_factor = self.user_height_cm / height_pixels if height_pixels > 0 else 1.0
        else:
            scale_factor = 1.0

        # Calculate ONLY circumference for specified body parts
        for measurement_name, config in self.CIRCUMFERENCE_POINTS.items():
            idx1, idx2 = config["indices"]
            ratio = config["ratio"]

            if idx1 < len(landmarks_3d) and idx2 < len(landmarks_3d):
                p1 = landmarks_3d[idx1]
                p2 = landmarks_3d[idx2]

                if p1 and p2:
                    width = np.sqrt(
                        (p1["x"] - p2["x"])**2 +
                        (p1["y"] - p2["y"])**2 +
                        (p1["z"] - p2["z"])**2
                    )

                    circumference = width * ratio * scale_factor
                    measurements[measurement_name] = round(circumference, 2)

        return measurements

    def run_full_capture(self):
        """Complete capture and measurement"""
        print("\n" + "="*70)
        print("CIRCUMFERENCE-ONLY MEASUREMENT SYSTEM - 4-VIEW AUTO-CAPTURE")
        print("="*70)
        print(f"User Height: {self.user_height_cm} cm")
        print(f"\nMeasurements: CIRCUMFERENCE ONLY")
        print("  • Chest, Waist, Hip (seat)")
        print("  • Biceps (left & right)")
        print("  • Forearms (left & right)")
        print("  • Thighs (left & right)")
        print("  • Calfs (left & right)")
        print("="*70 + "\n")

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        # Capture all 4 views
        landmarks_dict = {}
        for view in self.views:
            if self.capture_complete:
                break

            success, landmarks = self.auto_capture_view(view, cap)
            if success:
                landmarks_dict[view] = landmarks
            else:
                print(f"\n✗ Failed to capture {view} view")
                cap.release()
                cv2.destroyAllWindows()
                return False

        cap.release()
        cv2.destroyAllWindows()

        if self.capture_complete:
            print("\n⚠ Capture cancelled by user")
            return False

        # Reconstruct 3D from 4 views
        print("\n" + "="*70)
        print("RECONSTRUCTING 3D LANDMARKS")
        print("="*70)

        landmarks_3d = self.triangulate_4view(
            landmarks_dict.get("front"),
            landmarks_dict.get("left"),
            landmarks_dict.get("back"),
            landmarks_dict.get("right")
        )

        if landmarks_3d is None:
            print("✗ Failed to reconstruct 3D landmarks")
            return False

        # Calculate circumference measurements ONLY
        print("\nCalculating circumference measurements...")
        self.measurements = self.calculate_circumference_only(landmarks_3d)

        if not self.measurements:
            print("✗ Failed to calculate measurements")
            return False

        # Save measurements
        self._save_measurements()

        print("\n✓ CAPTURE COMPLETE")
        print("="*70)
        self._display_measurements()

        return True

    def _save_measurements(self):
        """Save CIRCUMFERENCE measurements ONLY to JSON"""
        timestamp = datetime.now().isoformat()

        # STORE ONLY CIRCUMFERENCE
        output_data = {
            "timestamp": timestamp,
            "user_height_cm": self.user_height_cm,
            "measurements": self.measurements,
            "capture_type": "4-view_auto-capture_circumference_only"
        }

        output_file = self.output_dir / f"body_measurements_{timestamp.replace(':', '-')}.json"

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✓ Measurements saved to: {output_file}")
        return output_file

    def _display_measurements(self):
        """Display circumference measurements"""
        print("\n" + "="*70)
        print("BODY CIRCUMFERENCE MEASUREMENTS (cm)")
        print("="*70)

        if not self.measurements:
            print("No measurements available")
            return

        # Organize by category
        core_measurements = ["chest", "waist", "hip"]
        arm_measurements = ["biceps_left", "biceps_right", "forearm_left", "forearm_right"]
        leg_measurements = ["thigh_left", "thigh_right", "calf_left", "calf_right"]

        print("\nCORE MEASUREMENTS:")
        print("-" * 70)
        for name in core_measurements:
            if name in self.measurements:
                print(f"  {name:20s}: {self.measurements[name]:7.2f} cm")

        print("\nARM MEASUREMENTS:")
        print("-" * 70)
        for name in arm_measurements:
            if name in self.measurements:
                side = "(Left)" if "left" in name else "(Right)"
                part = "Biceps" if "biceps" in name else "Forearm"
                print(f"  {part} {side:15s}: {self.measurements[name]:7.2f} cm")

        print("\nLEG MEASUREMENTS:")
        print("-" * 70)
        for name in leg_measurements:
            if name in self.measurements:
                side = "(Left)" if "left" in name else "(Right)"
                part = "Thigh" if "thigh" in name else "Calf"
                print(f"  {part} {side:15s}: {self.measurements[name]:7.2f} cm")

        print("="*70 + "\n")


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("CIRCUMFERENCE-ONLY MEASUREMENT SYSTEM")
    print("="*70)

    try:
        user_height = float(input("\nEnter your height (cm): ").strip())
        if user_height <= 0:
            print("Invalid height")
            return
    except ValueError:
        print("Invalid input")
        return

    reconstructor = CircumferenceOnlyReconstructor(
        user_height_cm=user_height,
        output_dir="./measurements"
    )

    success = reconstructor.run_full_capture()

    if success:
        print("✓ Measurement capture completed!")
    else:
        print("✗ Measurement capture failed")


if __name__ == "__main__":
    main()
