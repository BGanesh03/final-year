import math
import os
import customtkinter as ctk
from tkinter import filedialog
from theme import C, FONT_SMALL, FONT_LABEL, FONT_MONO, FONT_METRIC, FONT_SUB, _darken, ghost_btn


class PulsingDot(ctk.CTkCanvas):
    """Animated status dot (green pulse when active)."""
    def __init__(self, parent, size=10, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=C["bg"], highlightthickness=0, **kw)
        self._size   = size
        self._phase  = 0
        self._active = False
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self._size
        if self._active:
            alpha = int(80 + 60 * math.sin(self._phase))
            pulse_color = f"#{alpha:02x}FF{alpha:02x}"
            self.create_oval(1, 1, s-1, s-1, fill=pulse_color, outline="")
            self._phase += 0.25
            self.after(60, self._draw)
        else:
            self.create_oval(2, 2, s-2, s-2, fill=C["text_dim"], outline="")

    def set_active(self, val: bool):
        was = self._active
        self._active = val
        if val and not was:
            self._draw()
        elif not val:
            self._draw()


class TagBadge(ctk.CTkLabel):
    """Colored pill badge."""
    def __init__(self, parent, text, color=None, **kw):
        color = color or C["accent"]
        super().__init__(parent, text=f" {text} ",
                         text_color=color, font=FONT_SMALL,
                         fg_color=_darken(color, 0.25),
                         corner_radius=6, **kw)


class MetricTile(ctk.CTkFrame):
    """Single KPI tile: label + big value."""
    def __init__(self, parent, label, value, color=None, **kw):
        color = color or C["accent"]
        super().__init__(parent, fg_color=C["surface2"],
                         corner_radius=10, border_width=1,
                         border_color=color, **kw)
        ctk.CTkLabel(self, text=label, text_color=C["text_dim"],
                     font=FONT_SMALL).pack(padx=12, pady=(10, 0), anchor="w")
        ctk.CTkLabel(self, text=value, text_color=color,
                     font=FONT_METRIC).pack(padx=12, pady=(0, 10), anchor="w")


class FilePickRow(ctk.CTkFrame):
    """Compact file-pick row: icon label + filename display + pick button."""
    def __init__(self, parent, label, filetypes, on_pick, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._on_pick   = on_pick
        self._filetypes = filetypes

        ctk.CTkLabel(self, text=label, text_color=C["text_mid"],
                     font=FONT_LABEL, width=220, anchor="w").pack(side="left", padx=(0, 8))

        self._name_lbl = ctk.CTkLabel(
            self, text="— not loaded —", text_color=C["text_dim"],
            font=FONT_MONO, fg_color=C["surface2"],
            corner_radius=6, width=280, anchor="w")
        self._name_lbl.pack(side="left", padx=(0, 8), ipady=4, ipadx=8)

        ghost_btn(self, "Browse", self._pick, color=C["accent"], width=90).pack(side="left")

    def _pick(self):
        path = filedialog.askopenfilename(filetypes=self._filetypes)
        if path:
            self._name_lbl.configure(
                text=f"  ✓  {os.path.basename(path)}",
                text_color=C["accent3"])
            self._on_pick(path)


class AnimatedProgressBar(ctk.CTkFrame):
    """Indeterminate progress bar that pulses while active."""
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C["surface2"],
                         corner_radius=4, height=4, **kw)
        self._bar = ctk.CTkProgressBar(self, height=4,
                                       progress_color=C["accent"],
                                       fg_color=C["surface2"],
                                       corner_radius=4, mode="indeterminate",
                                       indeterminate_speed=1.2)
        self._bar.pack(fill="x")
        self._running = False

    def start(self):
        self._running = True
        self._bar.start()

    def stop(self):
        self._running = False
        self._bar.stop()
        self._bar.set(0)


class NavButton(ctk.CTkFrame):
    """Custom sidebar navigation item with step number + icon + label."""
    def __init__(self, parent, step, icon, label, command, **kw):
        super().__init__(parent, fg_color="transparent",
                         corner_radius=10, cursor="hand2", **kw)
        self._command  = command
        self._selected = False

        self._bg = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10)
        self._bg.pack(fill="x", padx=8, pady=2)

        inner = ctk.CTkFrame(self._bg, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(inner, text=step, text_color=C["text_dim"],
                     font=FONT_SMALL, width=18).pack(side="left")
        ctk.CTkLabel(inner, text=icon, font=("Segoe UI Emoji", 16),
                     width=28).pack(side="left", padx=(4, 6))
        self._lbl = ctk.CTkLabel(inner, text=label, text_color=C["text_mid"],
                                  font=FONT_LABEL, anchor="w")
        self._lbl.pack(side="left", fill="x", expand=True)

        self._bar = ctk.CTkFrame(self._bg, fg_color=C["accent"], width=3, corner_radius=2)

        for w in (self, self._bg, inner, self._lbl):
            w.bind("<Button-1>", lambda e: self._command())

    def select(self):
        self._selected = True
        self._bg.configure(fg_color=C["sidebar_sel"])
        self._lbl.configure(text_color=C["accent"])
        self._bar.place(relx=0, rely=0.1, relheight=0.8)

    def deselect(self):
        self._selected = False
        self._bg.configure(fg_color="transparent")
        self._lbl.configure(text_color=C["text_mid"])
        self._bar.place_forget()
