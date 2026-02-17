#!/usr/bin/env python3
import argparse
import json
import math
import os
import select
import sys
import threading
import time
from collections import defaultdict

from evdev import AbsInfo, InputDevice, UInput, list_devices
from evdev import ecodes as e
from PIL import Image
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.style import Style

# Global Control
PAUSED = False
RUNNING = True


def monitor_keyboard():
    global PAUSED, RUNNING
    keyboards = []

    # 1. Scan for all potential keyboards
    try:
        for path in list_devices():
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                if e.EV_KEY in caps:
                    keys = caps[e.EV_KEY]
                    # Check for KEY_P or KEY_ESC to confirm it's a keyboard-like device
                    if e.KEY_P in keys or e.KEY_ESC in keys:
                        print(f"  [Input Monitor] Added: {dev.name} ({dev.path})")
                        keyboards.append(dev)
            except Exception:
                pass
    except Exception:
        pass

    if not keyboards:
        print("Warning: Could not detect ANY physical keyboard for Global Pause/Exit.")
        return

    print(f"Listening for Global Input on {len(keyboards)} devices...")
    print("  [P]   = Pause/Resume")
    print("  [ESC] = Emergency Stop")

    # 2. Monitor Loop
    try:
        while RUNNING:
            # Wait for any device to have data
            r, w, x = select.select(
                keyboards, [], [], 1.0
            )  # 1s timeout to check RUNNING

            for dev in r:
                try:
                    for event in dev.read():
                        if event.type == e.EV_KEY and event.value == 1:  # Key Down
                            if event.code == e.KEY_P:
                                PAUSED = not PAUSED
                                if PAUSED:
                                    print(
                                        "\n>>> PAUSED (Press 'P' to resume) <<<",
                                        end="",
                                        flush=True,
                                    )
                                else:
                                    print("\n>>> RESUMED <<<", end="", flush=True)
                            elif event.code == e.KEY_ESC:
                                print("\n>>> EMERGENCY STOP <<<")
                                RUNNING = False
                                os._exit(0)
                except OSError:
                    # Device might have disconnected
                    pass
    except Exception as ex:
        print(f"Input Monitor Error: {ex}")


def load_config():
    try:
        with open("grid.json", "r") as f:
            grid_config = json.load(f)
        with open("palette.json", "r") as f:
            pal_config = json.load(f)
        return grid_config, pal_config
    except Exception:
        print("Error: Config files missing.")
        sys.exit(1)


def get_closest_color(pixel_rgb: tuple, palette: list) -> dict:
    best_match = None
    min_dist = float("inf")
    r1, g1, b1 = pixel_rgb[:3]
    for color in palette:
        # Skip transparent palette entries (Alpha = 0)
        if len(color["rgb"]) > 3 and color["rgb"][3] == 0:
            continue

        r2, g2, b2 = color["rgb"][:3]
        dist = math.sqrt((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2)
        if dist < min_dist:
            min_dist = dist
            best_match = color
    return best_match


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    grid_cfg, pal_cfg = load_config()
    RES = grid_cfg.get("resolution", {})
    WIDTH = RES.get("width", 1920)
    HEIGHT = RES.get("height", 1080)

    # Init Abs Mouse
    cap = {
        e.EV_KEY: [e.BTN_LEFT],
        e.EV_ABS: [
            (e.ABS_X, AbsInfo(value=0, min=0, max=WIDTH, fuzz=0, flat=0, resolution=0)),
            (
                e.ABS_Y,
                AbsInfo(value=0, min=0, max=HEIGHT, fuzz=0, flat=0, resolution=0),
            ),
        ],
    }
    ui = UInput(cap, name="Hertopia-Tablet-Mouse")

    # Start Keyboard Monitor
    kb_thread = threading.Thread(target=monitor_keyboard, daemon=True)
    kb_thread.start()

    time.sleep(1)

    current_x = WIDTH // 2
    current_y = HEIGHT // 2

    def move_to(x, y):
        nonlocal current_x, current_y
        x = int(max(0, min(WIDTH, x)))
        y = int(max(0, min(HEIGHT, y)))

        ui.write(e.EV_ABS, e.ABS_X, x)
        ui.write(e.EV_ABS, e.ABS_Y, y)
        ui.syn()
        current_x = x
        current_y = y
        time.sleep(0.0001)

    def click():
        # Double Click for focus (Slow & Safe)
        ui.write(e.EV_KEY, e.BTN_LEFT, 1)
        ui.syn()
        time.sleep(0.05)
        ui.write(e.EV_KEY, e.BTN_LEFT, 0)
        ui.syn()
        time.sleep(0.05)

        # Second click to act
        ui.write(e.EV_KEY, e.BTN_LEFT, 1)
        ui.syn()
        time.sleep(0.05)
        ui.write(e.EV_KEY, e.BTN_LEFT, 0)
        ui.syn()
        time.sleep(0.05)

    # Process Image
    img = Image.open(args.image).convert("RGBA")
    img = img.resize((150, 150), Image.Resampling.NEAREST)
    pixels = img.load()

    colors_list = pal_cfg["colors"]
    buttons = pal_cfg["buttons"]
    sub_positions = pal_cfg.get("sub_positions", [])

    draw_plan = defaultdict(list)
    width, height = img.size

    print("Designing execution plan...")
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            # Skip transparent pixels in input image
            if a < 128:
                continue

            rgb = (r, g, b)
            match = get_closest_color(rgb, colors_list)
            if match:
                k = tuple(match["rgb"])
                draw_plan[k].append({"grid_pos": (x, y), "color_data": match})

    # --- Background Optimization ---
    total_pixels = sum(len(v) for v in draw_plan.values())
    if total_pixels > 0:
        most_common_color = max(draw_plan.keys(), key=lambda k: len(draw_plan[k]))
        count = len(draw_plan[most_common_color])
        percentage = (count / total_pixels) * 100

        mc_data = draw_plan[most_common_color][0]["color_data"]

        console = Console()
        r, g, b = most_common_color[:3]
        color_style = Style(bgcolor=f"rgb({r},{g},{b})")

        print("\n--- BACKGROUND OPTIMIZATION ---")
        console.print(
            f"Most frequent color: RGB{most_common_color}", style=f"rgb({r},{g},{b})"
        )

        # Print a color block
        console.print("                 ", style=color_style)
        console.print(
            "    COLOR PREVIEW    ",
            style=Style(color="white", bgcolor=f"rgb({r},{g},{b})", bold=True),
        )
        console.print("                 ", style=color_style)

        print(f"Count: {count} pixels ({percentage:.1f}%)")

        info = "MAIN Color"
        if mc_data["type"] == "sub":
            info = f"SUB-Color #{mc_data['sub_index'] + 1}"
        print(f"Location info: {info}")

        print("\nSUGGESTION: Paint the entire canvas with this color manually!")
        print("If you do this, I can skip drawing these pixels.")

        try:
            choice = input("Skip drawing this color? (Y/n): ").strip().lower()
        except EOFError:
            choice = "y"

        if choice not in ("n", "no"):
            del draw_plan[most_common_color]
            print(f"Optimization detected: Skipping {count} pixels.")
        else:
            print("Drawing FULL image (no optimization).")
    # -------------------------------

    g = grid_cfg["grid"]
    gx1 = g["top_left"]["x"]
    gy1 = g["top_left"]["y"]
    gx2 = g["bottom_right"]["x"]
    gy2 = g["bottom_right"]["y"]
    gw = (gx2 - gx1) / 150
    gh = (gy2 - gy1) / 150

    def get_pos(c, r):
        return (gx1 + c * gw + gw / 2, gy1 + r * gh + gh / 2)

    sorted_keys = sorted(
        draw_plan.keys(), key=lambda k: draw_plan[k][0]["color_data"]["loc"][1]
    )  # Sort by Y pos

    print(f"Starting... {len(sorted_keys)} color groups. SWITCH WINDOW!")
    time.sleep(3)

    # Count total for progress
    total_to_draw = sum(len(draw_plan[k]) for k in sorted_keys)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
    ) as progress:
        overall_task = progress.add_task("[cyan]Drawing...", total=total_to_draw)

        for k in sorted_keys:
            items = draw_plan[k]
            color_data = items[0]["color_data"]
            # print(f"Color: {color_data['rgb']}") # Replaced by progress bar desc

            # Update desc
            r, g, b = color_data["rgb"][:3]
            progress.update(overall_task, description=f"[cyan]Drawing RGB({r},{g},{b})")

            main_loc = color_data["loc"]
            print(color_data)
            input()

            # 1. Main
            move_to(main_loc[0], main_loc[1])
            click()
            time.sleep(0.2)

            while PAUSED:
                time.sleep(0.1)
            if not RUNNING:
                return

            # 2. Sub
            if color_data["type"] == "sub":
                # Palette Icon
                px, py = buttons["palette_icon"]
                move_to(px, py)
                click()
                time.sleep(0.6)

                # Sub Index
                idx = color_data["sub_index"]
                sx, sy = sub_positions[idx]
                move_to(sx, sy)
                click()
                time.sleep(0.2)

                # Back
                bx, by = buttons["back"]
                move_to(bx, by)
                click()
                time.sleep(0.4)

            # 3. Draw
            for p in items:
                c, r = p["grid_pos"]
                tx, ty = get_pos(c, r)
                move_to(tx, ty)

                if not RUNNING:
                    return

                if not args.dry_run:
                    click()

                if PAUSED:
                    while PAUSED:
                        time.sleep(0.1)
                    move_to(tx, ty)
                    time.sleep(0.1)

                progress.advance(overall_task)


if __name__ == "__main__":
    main()
