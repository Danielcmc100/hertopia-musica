#!/usr/bin/env python3
import argparse
import json
import math
import os

from PIL import Image


def load_palette(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    palette_colors = []
    for item in data.get("colors", []):
        rgba = item["rgb"]
        # Skip fully transparent colors
        if len(rgba) > 3 and rgba[3] == 0:
            continue
        # Store as (r, g, b)
        palette_colors.append(tuple(rgba[:3]))
    return palette_colors


def get_closest_color(pixel, palette):
    r1, g1, b1 = pixel[:3]
    best_match = None
    min_dist = float("inf")

    for r2, g2, b2 in palette:
        dist = math.sqrt((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2)
        if dist < min_dist:
            min_dist = dist
            best_match = (r2, g2, b2)

    return best_match


def main():
    parser = argparse.ArgumentParser(
        description="Convert an image to 150x150 pixel art using the Hertopia palette."
    )
    parser.add_argument("input_image", help="Path to the input image")
    parser.add_argument(
        "output_image",
        help="Path to save the output image",
        nargs="?",
        default="pixelart_output.png",
    )
    parser.add_argument(
        "--palette", default="../palette.json", help="Path to palette.json"
    )

    args = parser.parse_args()

    # 1. Load Palette
    if not os.path.exists(args.palette):
        # Try local folder if ../ fails
        if os.path.exists("palette.json"):
            args.palette = "palette.json"
        else:
            print(f"Error: Palette file not found at {args.palette}")
            return

    print(f"Loading palette from {args.palette}...")
    palette = load_palette(args.palette)
    print(f"Loaded {len(palette)} valid colors.")

    # 2. Process Image
    print(f"Processing {args.input_image}...")
    try:
        img = Image.open(args.input_image).convert("RGB")
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Resize to 150x150
    # Using Bilinear for downscaling often preserves more detail than Nearest before quantization
    # But for pixel art look, sometimes Nearest is preferred.
    # Let's stick to typically good downsampling: Lanczos or Bilinear
    img = img.resize((150, 150), Image.Resampling.LANCZOS)

    # Create new image
    out_img = Image.new("RGB", (150, 150))
    pixels_in = img.load()
    pixels_out = out_img.load()

    print("Quantizing colors...")
    for y in range(150):
        for x in range(150):
            pixel = pixels_in[x, y]
            closest = get_closest_color(pixel, palette)
            pixels_out[x, y] = closest

    # 3. Save
    print(f"Saving to {args.output_image}...")
    out_img.save(args.output_image)

    # Optional: Scale up for visibility
    preview_size = 600
    display_img = out_img.resize((preview_size, preview_size), Image.Resampling.NEAREST)
    display_path = args.output_image.replace(".png", "_preview.png")
    display_img.save(display_path)
    print(f"Saved magnified preview to {display_path}")


if __name__ == "__main__":
    main()
