
"""
Circumference Measurement Utilities
Helper functions for 4-view circumference analysis and visualization
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple
from scipy.interpolate import interp1d

class CircumferenceAnalyzer:
    """Analyze and process circumference measurement data"""

    # Standard circumference ranges for adults (cm)
    CIRCUMFERENCE_STANDARDS = {
        "chest": {"min": 75, "max": 120, "target": 95},
        "waist": {"min": 60, "max": 110, "target": 80},
        "hip": {"min": 85, "max": 130, "target": 100},
        "arm_bicep": {"min": 22, "max": 38, "target": 30},
        "thigh_upper": {"min": 40, "max": 70, "target": 55},
        "calf": {"min": 30, "max": 45, "target": 38},
    }

    @staticmethod
    def load_circumference_data(filepath: str) -> Dict:
        """Load circumference measurement data"""
        with open(filepath, 'r') as f:
            return json.load(f)

    @staticmethod
    def validate_circumference(measurement_name: str, value_cm: float) -> Dict:
        """Validate circumference against standards"""
        if measurement_name not in CircumferenceAnalyzer.CIRCUMFERENCE_STANDARDS:
            return {"valid": True, "message": "No standard available"}

        standard = CircumferenceAnalyzer.CIRCUMFERENCE_STANDARDS[measurement_name]

        if value_cm < standard["min"]:
            return {
                "valid": False,
                "message": f"Below minimum ({standard['min']} cm)",
                "status": "too_small"
            }
        elif value_cm > standard["max"]:
            return {
                "valid": False,
                "message": f"Above maximum ({standard['max']} cm)",
                "status": "too_large"
            }
        else:
            diff_from_target = value_cm - standard["target"]
            if abs(diff_from_target) < 5:
                status = "ideal"
            elif diff_from_target > 0:
                status = "above_target"
            else:
                status = "below_target"

            return {
                "valid": True,
                "message": f"Within range ({standard['min']}-{standard['max']} cm)",
                "status": status,
                "diff_from_target": round(diff_from_target, 2)
            }

    @staticmethod
    def compare_circumferences(current: Dict, previous: Dict) -> Dict:
        """Compare two sets of circumference measurements"""
        comparison = {
            "improvements": [],
            "deterioration": [],
            "stable": []
        }

        for measurement_name in current.get("circumferences", {}):
            if measurement_name not in previous.get("circumferences", {}):
                continue

            current_val = current["circumferences"][measurement_name]
            previous_val = previous["circumferences"][measurement_name]
            change = current_val - previous_val
            change_pct = (change / previous_val * 100) if previous_val != 0 else 0

            result = {
                "measurement": measurement_name,
                "previous": round(previous_val, 2),
                "current": round(current_val, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2)
            }

            if abs(change) < 1:
                comparison["stable"].append(result)
            elif change < 0:
                comparison["improvements"].append(result)
            else:
                comparison["deterioration"].append(result)

        return comparison

    @staticmethod
    def calculate_body_fat_proxy(circumferences: Dict, height_cm: float, gender: str = "M") -> Dict:
        """
        Estimate body fat percentage using circumference measurements
        Using simplified Navy circumference formula

        For Men: BF% = 495 / (1.0324 - 0.19077 * log10(waist-neck) + 0.15456 * log10(height)) - 450
        For Women: BF% = 495 / (1.29579 - 0.35004 * log10(waist+hip-neck) + 0.22100 * log10(height)) - 450
        """
        try:
            waist = circumferences.get("waist", 0)
            hip = circumferences.get("hip", 0)
            neck = circumferences.get("arm_bicep", 0) * 0.85  # Approximation

            if not waist or not hip:
                return {"error": "Missing required measurements"}

            if gender.upper() == "M":
                # Men's formula
                bf_percentage = 495 / (1.0324 - 0.19077 * np.log10(waist - neck) 
                                      + 0.15456 * np.log10(height_cm)) - 450
            else:
                # Women's formula
                bf_percentage = 495 / (1.29579 - 0.35004 * np.log10(waist + hip - neck)
                                      + 0.22100 * np.log10(height_cm)) - 450

            return {
                "body_fat_percentage": round(max(0, min(100, bf_percentage)), 2),
                "method": "circumference_based_estimation",
                "accuracy_note": "±5-10% accuracy"
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def plot_circumferences(data: Dict, output_file: str = None):
        """Plot circumference measurements"""
        circumferences = data.get("circumferences", {})

        if not circumferences:
            print("No circumference data available")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Bar chart
        names = list(circumferences.keys())
        values = list(circumferences.values())

        bars = ax1.bar(names, values, color='steelblue', edgecolor='navy', alpha=0.7)
        ax1.set_ylabel('Circumference (cm)', fontsize=12)
        ax1.set_title('Body Circumference Measurements', fontsize=14, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=9)

        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Validation status
        validation_status = {}
        for name, value in circumferences.items():
            validation = CircumferenceAnalyzer.validate_circumference(name, value)
            validation_status[name] = validation["status"]

        status_colors = []
        status_labels = []
        for status in validation_status.values():
            if status == "ideal":
                status_colors.append('green')
                status_labels.append('Ideal')
            elif status == "above_target":
                status_colors.append('orange')
                status_labels.append('Above Target')
            elif status == "below_target":
                status_colors.append('lightblue')
                status_labels.append('Below Target')
            else:
                status_colors.append('red')
                status_labels.append('Out of Range')

        ax2.bar(names, values, color=status_colors, edgecolor='black', alpha=0.7)
        ax2.set_ylabel('Circumference (cm)', fontsize=12)
        ax2.set_title('Circumference Status', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=150)
            print(f"Chart saved to: {output_file}")
        else:
            plt.show()

    @staticmethod
    def generate_report(data: Dict, height_cm: float, gender: str = "M") -> str:
        """Generate comprehensive circumference report"""
        circumferences = data.get("circumferences", {})
        timestamp = data.get("timestamp", "Unknown")

        report = f"""
╔════════════════════════════════════════════════════════════════╗
║           BODY CIRCUMFERENCE MEASUREMENT REPORT                ║
╚════════════════════════════════════════════════════════════════╝

Date: {timestamp}
Height: {height_cm} cm
Measurement Type: 4-View Circumference Analysis

─────────────────────────────────────────────────────────────────
CIRCUMFERENCE MEASUREMENTS
─────────────────────────────────────────────────────────────────

"""

        for measurement_name, value in sorted(circumferences.items()):
            validation = CircumferenceAnalyzer.validate_circumference(measurement_name, value)
            status_symbol = "✓" if validation["valid"] else "✗"
            status_text = validation.get("status", "unknown")

            report += f"{status_symbol} {measurement_name:20s}: {value:6.2f} cm [{status_text}]\n"

        # Body fat estimation
        bf_data = CircumferenceAnalyzer.calculate_body_fat_proxy(circumferences, height_cm, gender)

        if "body_fat_percentage" in bf_data:
            report += f"""
─────────────────────────────────────────────────────────────────
BODY COMPOSITION ESTIMATE
─────────────────────────────────────────────────────────────────

Body Fat Percentage: {bf_data['body_fat_percentage']}%
Method: {bf_data['method']}
Note: {bf_data['accuracy_note']}
"""

        report += """
─────────────────────────────────────────────────────────────────
STANDARDS & RECOMMENDATIONS
─────────────────────────────────────────────────────────────────

Standard Circumference Ranges (Adult Average):
  • Chest:      75-120 cm (Target: 95 cm)
  • Waist:      60-110 cm (Target: 80 cm)
  • Hip:        85-130 cm (Target: 100 cm)
  • Arm Bicep:  22-38 cm  (Target: 30 cm)
  • Thigh:      40-70 cm  (Target: 55 cm)
  • Calf:       30-45 cm  (Target: 38 cm)

─────────────────────────────────────────────────────────────────
TIPS FOR IMPROVEMENT
─────────────────────────────────────────────────────────────────

✓ Regular strength training (3-4x/week)
✓ Cardiovascular exercise (150+ min/week)
✓ Balanced nutrition with adequate protein
✓ Consistent measurements monthly
✓ Progressive goal setting

"""

        return report

    @staticmethod
    def export_to_csv(data: Dict, output_file: str):
        """Export circumference data to CSV"""
        import csv

        circumferences = data.get("circumferences", {})

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Measurement', 'Value (cm)'])

            for name, value in circumferences.items():
                writer.writerow([name, round(value, 2)])

        print(f"CSV exported to: {output_file}")

    @staticmethod
    def batch_compare_measurements(measurement_files: List[str]) -> Dict:
        """Compare multiple measurement sessions"""
        measurements = []

        for file_path in measurement_files:
            try:
                data = CircumferenceAnalyzer.load_circumference_data(file_path)
                measurements.append(data)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        if len(measurements) < 2:
            return {"error": "Need at least 2 measurements"}

        # Compare consecutive measurements
        comparison_results = []

        for i in range(1, len(measurements)):
            comparison = CircumferenceAnalyzer.compare_circumferences(
                measurements[i], measurements[i-1]
            )
            comparison_results.append({
                "session": i,
                "timestamp_previous": measurements[i-1].get("timestamp"),
                "timestamp_current": measurements[i].get("timestamp"),
                "comparison": comparison
            })

        return {"results": comparison_results}


# Helper functions for quick analysis
def quick_circumference_analysis(json_file: str):
    """Quick analysis of circumference measurement file"""
    data = CircumferenceAnalyzer.load_circumference_data(json_file)
    circumferences = data.get("circumferences", {})
    height = data.get("user_height_cm", 0)

    print(f"\nCircumference Analysis - {json_file}")
    print("=" * 60)

    for measurement, value in circumferences.items():
        validation = CircumferenceAnalyzer.validate_circumference(measurement, value)
        status = "✓" if validation["valid"] else "✗"
        print(f"{status} {measurement:20s}: {value:6.2f} cm - {validation['message']}")

    # Body fat estimate
    bf = CircumferenceAnalyzer.calculate_body_fat_proxy(circumferences, height)
    if "body_fat_percentage" in bf:
        print(f"\nEstimated Body Fat: {bf['body_fat_percentage']}%")

    print("=" * 60)


def generate_progress_report(json_files: List[str], gender: str = "M"):
    """Generate progress report across multiple sessions"""

    if len(json_files) < 2:
        print("Need at least 2 measurement files")
        return

    print("\nGenerating Progress Report...")
    print("=" * 60)

    # Load first measurement
    first_data = CircumferenceAnalyzer.load_circumference_data(json_files[0])
    height = first_data.get("user_height_cm", 0)

    print(f"Measurement Period: {json_files[0]} to {json_files[-1]}")
    print(f"Height: {height} cm\n")

    # Compare first and last
    last_data = CircumferenceAnalyzer.load_circumference_data(json_files[-1])
    comparison = CircumferenceAnalyzer.compare_circumferences(last_data, first_data)

    print("IMPROVEMENTS (Circumference Decreased):")
    for item in comparison["improvements"]:
        print(f"  {item['measurement']:20s}: {item['previous']:6.2f} → {item['current']:6.2f} "
              f"(-{abs(item['change']):5.2f} cm, {item['change_percent']:+.1f}%)")

    print("\nDETERIOATION (Circumference Increased):")
    for item in comparison["deterioration"]:
        print(f"  {item['measurement']:20s}: {item['previous']:6.2f} → {item['current']:6.2f} "
              f"(+{item['change']:5.2f} cm, {item['change_percent']:+.1f}%)")

    print("\nSTABLE (No significant change):")
    for item in comparison["stable"]:
        print(f"  {item['measurement']:20s}: {item['previous']:6.2f} → {item['current']:6.2f} "
              f"(±{abs(item['change']):5.2f} cm)")

    print("\n" + "=" * 60)
