"""Tkinter-based GUI display manager for the drone detection app.

This provides a simple window with a live video canvas, FPS label, Start/Stop and Switch Camera buttons.
It wraps the existing DisplayManager functionality by converting frames for Tkinter display.
"""

import logging
import threading
import time
from typing import Optional, List

try:
    import tkinter as tk
    from PIL import Image, ImageTk
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False

import cv2
import numpy as np
from .models import DetectionResult
from .display_manager import DisplayManager as BaseDisplayManager


class TkDisplayManager(BaseDisplayManager):
    def __init__(self, window_title: str = "Drone Human Detection GUI"):
        super().__init__()
        self.window_title = window_title
        self._tk_root: Optional[tk.Tk] = None
        self._canvas = None
        self._image_on_canvas = None
        self._running = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._last_key = None
        self.logger = logging.getLogger(__name__)

        if not TK_AVAILABLE:
            self.logger.warning("Tkinter or PIL not available; falling back to headless DisplayManager")

    def _start_tk(self):
        if not TK_AVAILABLE:
            return
        self._tk_root = tk.Tk()
        self._tk_root.title(self.window_title)
        self._canvas = tk.Label(self._tk_root)
        self._canvas.pack()

        # Control buttons
        control_frame = tk.Frame(self._tk_root)
        control_frame.pack(fill=tk.X)
        tk.Button(control_frame, text="Quit", command=self._on_quit).pack(side=tk.LEFT)
        tk.Button(control_frame, text="Switch Camera", command=self._on_switch).pack(side=tk.LEFT)
        # Fullscreen toggle
        self._tk_fullscreen = False
        tk.Button(control_frame, text="Fullscreen", command=self._tk_toggle_fullscreen).pack(side=tk.LEFT)

        # Bind 'f' key to toggle fullscreen
        try:
            self._tk_root.bind('<f>', lambda e: self._tk_toggle_fullscreen())
            self._tk_root.bind('<F>', lambda e: self._tk_toggle_fullscreen())
        except Exception:
            pass

        # FPS label
        self._fps_label = tk.Label(control_frame, text="FPS: 0.0")
        self._fps_label.pack(side=tk.RIGHT)

        # Run the Tk mainloop in a separate thread to avoid blocking
        self._thread = threading.Thread(target=self._tk_root.mainloop, daemon=True)
        self._thread.start()

    def _on_quit(self):
        self._running = False
        try:
            if self._tk_root:
                self._tk_root.quit()
        except Exception:
            pass

    def _on_switch(self):
        # expose a key equivalent for the main loop to see
        self.last_key = ord('c')

    def _tk_toggle_fullscreen(self) -> None:
        """Toggle fullscreen for the Tk root window."""
        try:
            if not self._tk_root:
                return
            self._tk_fullscreen = not getattr(self, '_tk_fullscreen', False)
            # wm_attributes('-fullscreen', True/False) works across platforms
            self._tk_root.wm_attributes('-fullscreen', self._tk_fullscreen)
        except Exception as e:
            self.logger.debug(f"Failed to toggle Tk fullscreen: {e}")

    def display_frame(self, frame: np.ndarray, detections: Optional[List[DetectionResult]] = None) -> bool:
        with self._lock:
            if not TK_AVAILABLE:
                # fallback to base implementation
                return super().display_frame(frame, detections)

            if self._tk_root is None:
                self._start_tk()

            # Draw overlays using base class
            display_frame = frame.copy()
            if detections:
                display_frame = self.draw_detections(display_frame, detections)
            display_frame = self._draw_fps_counter(display_frame)

            # Convert BGR->RGB and to PIL Image
            try:
                img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(img)
                tkimg = ImageTk.PhotoImage(pil)
                self._canvas.configure(image=tkimg)
                self._canvas.image = tkimg
            except Exception as e:
                self.logger.error(f"Failed to update Tk canvas: {e}")
                return super().display_frame(frame, detections)

            # update fps label
            try:
                if hasattr(self, '_fps_label'):
                    self._fps_label.config(text=f"FPS: {self.get_fps():.1f}")
            except Exception:
                pass

            # Clear last_key after reporting it
            self.last_key = None
            return True

    def cleanup(self) -> None:
        try:
            if self._tk_root:
                self._tk_root.quit()
        except Exception:
            pass
        super().cleanup()
