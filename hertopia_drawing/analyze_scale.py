#!/usr/bin/env python3
import functools
import json
import math
import os
import sys

print = functools.partial(print, flush=True)
from PIL import Image


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])) ** 0.5


def find_blobs(img, target_color, tolerance=30):
    width, height = img.size
    pixels = img.load()
    matches = []
    for y in range(height):
        for x in range(width):
            if color_distance(pixels[x, y], target_color) < tolerance:
                matches.append((x, y))

    if not matches:
        # print(f"  No match for {target_color} with tolerance {tolerance}")
        return None

    print(f"  Found {len(matches)} pixels matching {target_color}")

    # Simple centroid
    avg_x = sum(x for x, y in matches) / len(matches)
    avg_y = sum(y for x, y in matches) / len(matches)
    return (avg_x, avg_y)


def main():
    base_dir = "."
    palette_path = os.path.join(base_dir, "palette.json")
    reference_img = os.path.join(base_dir, "atual.jpg")

    if not os.path.exists(palette_path) or not os.path.exists(reference_img):
        print("Error: Files missing.")
        sys.exit(1)

    data = load_json(palette_path)
    img = Image.open(reference_img).convert("RGB")

    print(f"Image size: {img.size}")

    # Extract Main Colors distinct enough to find
    main_colors = []
    for i, color in enumerate(data["colors"]):
        if color["type"] == "main":
            main_colors.append({"rgb": color["rgb"], "loc": color["loc"], "index": i})

    print(f"Found {len(main_colors)} main colors in JSON.")

    found_points = []

    for mc in main_colors:
        centroid = find_blobs(img, mc["rgb"], tolerance=30)
        if centroid:
            print(f"Color {mc['rgb']} (JSON {mc['loc']}) found at Image {centroid}")
            found_points.append(
                {"json_loc": mc["loc"], "img_loc": centroid, "rgb": mc["rgb"]}
            )
        else:
            print(f"Color {mc['rgb']} (JSON {mc['loc']}) NOT found.")

    if len(found_points) < 2:
        print("Not enough points found to estimate scale.")
        sys.exit(0)

    # Estimate Scale
    # Distance between P1 and P2 in JSON vs Image
    scales = []
    for i in range(len(found_points)):
        for j in range(i + 1, len(found_points)):
            p1 = found_points[i]
            p2 = found_points[j]

            dist_json = math.dist(p1["json_loc"], p2["json_loc"])
            dist_img = math.dist(p1["img_loc"], p2["img_loc"])

            if dist_json > 50:  # Ignore close points to avoid noise
                scale = dist_img / dist_json
                scales.append(scale)

    if scales:
        avg_scale = sum(scales) / len(scales)
        print(f"Estimated Scale: {avg_scale:.4f}")

        # Estimate Offset
        # img = (json * scale) + offset
        # offset = img - (json * scale)

        offsets_x = []
        offsets_y = []

        for p in found_points:
            ox = p["img_loc"][0] - (p["json_loc"][0] * avg_scale)
            oy = p["img_loc"][1] - (p["json_loc"][1] * avg_scale)
            offsets_x.append(ox)
            offsets_y.append(oy)

        avg_offset_x = sum(offsets_x) / len(offsets_x)
        avg_offset_y = sum(offsets_y) / len(offsets_y)

        print(f"Estimated Offset: ({avg_offset_x:.2f}, {avg_offset_y:.2f})")

        # Verify
        print("Verification:")
        for p in found_points:
            pred_x = p["json_loc"][0] * avg_scale + avg_offset_x
            pred_y = p["json_loc"][1] * avg_scale + avg_offset_y
            err = math.dist((pred_x, pred_y), p["img_loc"])
            print(
                f"  Point {p['json_loc']} -> Pred ({pred_x:.1f}, {pred_y:.1f}) | Actual {p['img_loc']} | Err {err:.1f}"
            )

    else:
        print("Could not estimate scale (points too close?).")


if __name__ == "__main__":
    main()
