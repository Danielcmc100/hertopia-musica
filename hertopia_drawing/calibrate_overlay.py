#!/usr/bin/env python3
import json
import os
import tkinter as tk

# File path
GRID_FILE = "grid.json"


def load_config():
    if os.path.exists(GRID_FILE):
        try:
            with open(GRID_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Defaults
    return {
        "resolution": {"width": 1920, "height": 1080},
        "grid": {
            "top_left": {"x": 100, "y": 100},
            "bottom_right": {"x": 800, "y": 800},
            "width": 150,
            "height": 150,
        },
    }


class OverlayCalibrator:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.grid_cfg = config["grid"]

        # Coordinates
        self.x1 = self.grid_cfg["top_left"]["x"]
        self.y1 = self.grid_cfg["top_left"]["y"]
        self.x2 = self.grid_cfg["bottom_right"]["x"]
        self.y2 = self.grid_cfg["bottom_right"]["y"]
        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()

        # --- Control Window ---
        self.root.title("Calibrator Controls")
        self.root.geometry("400x150+10+10")
        self.root.attributes("-topmost", True)
        self.root.bind("<Escape>", self.close)
        self.root.bind("<Return>", self.save)

        # Instructions Label
        self.lbl_status = tk.Label(
            self.root,
            text="Initializing...",
            font=("Arial", 10),
            justify="left",
            bg="black",
            fg="white",
        )
        self.lbl_status.pack(fill="both", expand=True)

        # Bind Keys to Root
        self.root.bind("w", lambda e: self.move_tl(0, -1))
        self.root.bind("s", lambda e: self.move_tl(0, 1))
        self.root.bind("a", lambda e: self.move_tl(-1, 0))
        self.root.bind("d", lambda e: self.move_tl(1, 0))
        self.root.bind("W", lambda e: self.move_tl(0, -10))
        self.root.bind("S", lambda e: self.move_tl(0, 10))
        self.root.bind("A", lambda e: self.move_tl(-10, 0))
        self.root.bind("D", lambda e: self.move_tl(10, 0))

        self.root.bind("<Up>", lambda e: self.move_br(0, -1))
        self.root.bind("<Down>", lambda e: self.move_br(0, 1))
        self.root.bind("<Left>", lambda e: self.move_br(-1, 0))
        self.root.bind("<Right>", lambda e: self.move_br(1, 0))
        self.root.bind("<Shift-Up>", lambda e: self.move_br(0, -10))
        self.root.bind("<Shift-Down>", lambda e: self.move_br(0, 10))
        self.root.bind("<Shift-Left>", lambda e: self.move_br(-10, 0))
        self.root.bind("<Shift-Right>", lambda e: self.move_br(10, 0))

        # --- Borders (4 Windows) ---
        self.borders = []
        for _ in range(4):
            w = tk.Toplevel(self.root)
            w.overrideredirect(True)  # No decorations
            w.attributes("-topmost", True)
            w.configure(bg="cyan")
            self.borders.append(w)

        self.update_ui()

    def move_tl(self, dx, dy):
        self.x1 += dx
        self.y1 += dy
        self.update_ui()

    def move_br(self, dx, dy):
        self.x2 += dx
        self.y2 += dy
        self.update_ui()

    def update_ui(self):
        # Calc dims
        x1, y1 = min(self.x1, self.x2), min(self.y1, self.y2)
        x2, y2 = max(self.x1, self.x2), max(self.y1, self.y2)
        w, h = x2 - x1, y2 - y1
        thick = 4

        # Top
        self.borders[0].geometry(f"{w}x{thick}+{x1}+{y1}")
        # Bottom
        self.borders[1].geometry(f"{w}x{thick}+{x1}+{y2 - thick}")
        # Left
        self.borders[2].geometry(f"{thick}x{h}+{x1}+{y1}")
        # Right
        self.borders[3].geometry(f"{thick}x{h}+{x2 - thick}+{y1}")

        # Stats
        ppp_x = w / 150.0
        ppp_y = h / 150.0
        valid_x = abs(ppp_x - round(ppp_x)) < 0.05
        valid_y = abs(ppp_y - round(ppp_y)) < 0.05

        color = "#00ff00" if (valid_x and valid_y) else "red"
        for b in self.borders:
            b.configure(bg=color)

        msg = (
            f"CONTROLS: Click this window to focus!\n"
            f"WASD: Top-Left  |  Arrows: Bottom-Right\n\n"
            f"Grid: {x1},{y1} -> {x2},{y2} ({w}x{h})\n"
            f"Pixels/Dot: X={ppp_x:.3f}  Y={ppp_y:.3f}\n"
            f"Aligned? {'YES ✅' if (valid_x and valid_y) else 'NO ❌'}\n\n"
            f"[ENTER] Save & Quit"
        )
        self.lbl_status.config(text=msg, fg=color)

    def save(self, event=None):
        self.config["resolution"]["width"] = self.sw
        self.config["resolution"]["height"] = self.sh
        self.config["grid"]["top_left"]["x"] = self.x1
        self.config["grid"]["top_left"]["y"] = self.y1
        self.config["grid"]["bottom_right"]["x"] = self.x2
        self.config["grid"]["bottom_right"]["y"] = self.y2

        with open(GRID_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

        print("Saved Grid!")
        self.root.quit()

    def close(self, event=None):
        print("Cancelled.")
        self.root.quit()


if __name__ == "__main__":
    print("Launching Overlay Calibration...")
    print("Please focus the overlay window if controls don't work immediately.")

    cfg = load_config()
    root = tk.Tk()
    app = OverlayCalibrator(root, cfg)
    root.mainloop()
