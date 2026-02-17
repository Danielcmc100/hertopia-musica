#!/usr/bin/env python3
import json
import os
import subprocess
import sys

import cv2


def get_screenshot(output_path="/tmp/pixel_auto.png"):
    """Captures the screenshot using gnome-screenshot."""
    try:
        subprocess.run(
            ["gnome-screenshot", "-f", output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not os.path.exists(output_path):
            print(f"Error: Screenshot not found at {output_path}")
            sys.exit(1)
        return output_path
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        sys.exit(1)


def find_grid(image_path):
    """
    Analyzes the image to find the large drawing grid (150x150).
    The grid is usually a large white/light area surrounded by UI.
    """
    print(f"Analyzing {image_path}...")
    img = cv2.imread(image_path)
    if img is None:
        print("Failed to load image.")
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Threshold to find the bright canvas area (white)
    # The canvas is likely very bright (near 255).
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by size and shape
    # We expect a large square-ish region.
    # 150x150 pixels * (scale ~3-6) => Width ~450px to ~900px

    candidates = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / h
        area = w * h

        # Grid is square: Aspect Ratio ~1.0 (+- 0.1 tolerance)
        # Size: At least 300x300 pixels
        if 0.9 < aspect_ratio < 1.1 and w > 300 and h > 300:
            candidates.append((x, y, w, h))

    if not candidates:
        print("No exact grid candidate found. Trying looser constraints...")
        # Looser check in case of shadows or UI overlap
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Just ignore tiny stuff
            if w > 200 and h > 200:
                candidates.append((x, y, w, h))

    if not candidates:
        print(
            "Still no candidates. Check if the game is visible and canvas is clear/white."
        )
        return None

    # Pick the largest candidate
    candidates.sort(key=lambda c: c[2] * c[3], reverse=True)
    x, y, w, h = candidates[0]

    print("\n--- GRID DETECTED ---")
    print(f"Region: Top-Left=({x}, {y}), Size={w}x{h}")

    # Calculate Pixels per Dot
    ppd_x = w / 150.0
    ppd_y = h / 150.0

    print(f"Pixels per Dot: X={ppd_x:.4f}, Y={ppd_y:.4f}")

    # Auto-Correction Recommendation
    best_ppd = round((ppd_x + ppd_y) / 2)
    print(f"Closest Integer Scale: {best_ppd}.0")

    print(f"Is it perfect? {abs(ppd_x - best_ppd) < 0.05}")

    return {"x1": x, "y1": y, "x2": x + w, "y2": y + h, "width": w, "height": h}


def update_config(grid_data):
    """Updates grid.json with found coordinates."""
    file = "grid.json"

    # Load existing or default
    if os.path.exists(file):
        with open(file, "r") as f:
            cfg = json.load(f)
    else:
        cfg = {"resolution": {"width": 1920, "height": 1080}}

    cfg["grid"] = {
        "top_left": {"x": int(grid_data["x1"]), "y": int(grid_data["y1"])},
        "bottom_right": {"x": int(grid_data["x2"]), "y": int(grid_data["y2"])},
        "width": 150,
        "height": 150,
    }

    with open(file, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"\nSuccessfully updated {file}!")
    print("\nNext Steps:")
    print("1. Run 'python3 calibrate_overlay.py' to double-check visually.")
    print("2. If the box perfectly aligns with the canvas edges, you are good to go!")


if __name__ == "__main__":
    print("=== Auto-Calibration Tool ===")
    print("1. Open the game.")
    print("2. Ensure the drawing canvas is visible and CLEAR (mostly white/empty).")
    if "--no-wait" not in sys.argv:
        input("Press ENTER to take a screenshot and analyze...")

    path = get_screenshot()
    grid = find_grid(path)

    if grid:
        update_config(grid)
    else:
        print("Calibration failed. Please try manual calibration.")
