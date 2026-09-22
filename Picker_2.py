import tkinter as tk
import json
import os
from PIL import Image, ImageGrab, ImageDraw
from pynput import mouse, keyboard
from threading import Thread
import pystray
from colorsys import rgb_to_hsv


class ColorNameOverlay:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Color Picker Overlay")
        self.window.attributes('-alpha', 0.95)
        self.window.attributes("-topmost", True)
        self.window.geometry("280x110")
        self.window.resizable(False, False)

        try:
            self.window.attributes('-type', 'splash')
        except:
            pass

        self.mouse_x = 0
        self.mouse_y = 0

        self.drag_start_x = 0
        self.drag_start_y = 0
        self.window_x = 0
        self.window_y = 0

        self.settings_file = "color_picker_overlay_settings.json"
        self.load_settings()

        self.create_overlay()
        self.setup_tray()

        self.listener = mouse.Listener(on_move=self.on_mouse_move)
        self.listener.start()

        self.key_listener = keyboard.Listener(on_press=self.on_key_press)
        self.key_listener.start()

        self.window.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.window.bind("<Button-1>", self.start_drag)
        self.window.bind("<B1-Motion>", self.do_drag)

        self.update_color()

    def load_settings(self):
        default_settings = {
            "window_x": None,
            "window_y": None,
        }

        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = default_settings
        else:
            self.settings = default_settings

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def set_window_position(self):
        self.window.update_idletasks()

        if self.settings["window_x"] is not None and self.settings["window_y"] is not None:
            self.window.geometry(f"+{self.settings['window_x']}+{self.settings['window_y']}")
        else:
            self.window.update_idletasks()
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()

            x = screen_width - 300
            y = 10

            self.window.geometry(f"+{x}+{y}")
            self.settings["window_x"] = x
            self.settings["window_y"] = y
            self.save_settings()

    def create_overlay(self):
        self.window.config(bg="#1a1a1a")

        main_frame = tk.Frame(self.window, bg="#1a1a1a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.color_name_label = tk.Label(
            main_frame,
            text="Detecting...",
            font=("Arial", 22, "bold"),
            bg="#1a1a1a",
            fg="white"
        )
        self.color_name_label.pack(pady=3)

        self.hex_label = tk.Label(
            main_frame,
            text="#000000",
            font=("Arial", 16, "bold"),
            bg="#1a1a1a",
            fg="#ffff00"
        )
        self.hex_label.pack(pady=3)

        self.rgb_info_label = tk.Label(
            main_frame,
            text="RGB: (0, 0, 0)",
            font=("Arial", 9),
            bg="#1a1a1a",
            fg="#cccccc"
        )
        self.rgb_info_label.pack(pady=2)

        info = tk.Label(
            main_frame,
            text="Drag to move • ESC to exit",
            font=("Arial", 7),
            bg="#1a1a1a",
            fg="#888888"
        )
        info.pack(pady=2)

    def start_drag(self, event):
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.window_x = self.window.winfo_x()
        self.window_y = self.window.winfo_y()

    def do_drag(self, event):
        delta_x = event.x_root - self.drag_start_x
        delta_y = event.y_root - self.drag_start_y

        new_x = self.window_x + delta_x
        new_y = self.window_y + delta_y

        self.window.geometry(f"+{new_x}+{new_y}")

        self.settings["window_x"] = new_x
        self.settings["window_y"] = new_y
        self.save_settings()

    def on_mouse_move(self, x, y):
        self.mouse_x = x
        self.mouse_y = y

    def on_key_press(self, key):
        try:
            if key == keyboard.Key.esc:
                self.quit_app()
        except AttributeError:
            pass



    def get_general_color_name(self, r, g, b):
        h, s, v = rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        h = h * 360
        s = s * 100
        v = v * 100

        if s < 15:
            if v < 15:
                return "Black"
            elif v < 50:
                return "Dark Gray"
            elif v < 85:
                return "Gray"
            else:
                return "White"

        if h < 15 or h >= 345:
            return "Red"
        elif h < 45:
            return "Orange"
        elif h < 65:
            return "Yellow"
        elif h < 150:
            return "Green"
        elif h < 200:
            return "Cyan"
        elif h < 270:
            return "Blue"
        elif h < 300:
            return "Purple"
        elif h < 330:
            return "Magenta"
        else:
            return "Red"

    def update_color(self):
        try:
            pixel = ImageGrab.grab(bbox=(self.mouse_x, self.mouse_y,
                                         self.mouse_x + 1, self.mouse_y + 1))
            rgb = pixel.getpixel((0, 0))

            if isinstance(rgb, tuple):
                r, g, b = rgb[0], rgb[1], rgb[2]
            else:
                r = g = b = rgb

            color_name = self.get_general_color_name(r, g, b)
            self.color_name_label.config(text=color_name)

            hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
            self.hex_label.config(text=hex_color)

            self.rgb_info_label.config(text=f"RGB: ({r}, {g}, {b})")

        except Exception as e:
            pass

        self.window.after(100, self.update_color)

    def create_tray_icon(self):
        """Create a simple tray icon image"""
        image = Image.new('RGB', (64, 64), color=(44, 62, 80))
        draw = ImageDraw.Draw(image)

        draw.ellipse([10, 10, 54, 54], fill=(100, 180, 200), outline=(255, 255, 255))

        return image

    def setup_tray(self):
        icon_image = self.create_tray_icon()

        menu = pystray.Menu(
            pystray.MenuItem("Show", self.restore_from_tray),
            pystray.MenuItem("Exit", self.quit_app)
        )

        self.tray_icon = pystray.Icon(
            "Color Picker Overlay",
            icon_image,
            "Color Picker Overlay",
            menu
        )

    def minimize_to_tray(self):
        self.window.withdraw()

        if not hasattr(self, 'tray_running'):
            self.tray_running = True
            tray_thread = Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()

    def restore_from_tray(self, icon=None, item=None):
        self.window.deiconify()
        self.window.lift()
        self.window.attributes("-topmost", True)

    def quit_app(self, icon=None, item=None):
        try:
            self.tray_icon.stop()
        except:
            pass
        self.listener.stop()
        self.key_listener.stop()
        self.window.quit()
        self.window.destroy()

    def run(self):
        self.set_window_position()
        self.window.mainloop()
        self.quit_app()


if __name__ == "__main__":
    overlay = ColorNameOverlay()
    overlay.run()