import matplotlib
matplotlib.use("Agg")

import customtkinter as ctk
import os
import warnings

from theme import C, FONT_SMALL, FONT_SUB, FONT_TITLE
from theme import make_card, accent_label, dim_label, separator
from widgets import PulsingDot, AnimatedProgressBar, NavButton
from preprocessing import PreprocessingMixin
from manual_analysis import ManualAnalysisMixin
from ml_analysis import MLAnalysisMixin

warnings.filterwarnings("ignore", category=UserWarning, module="pywt")


class WaveletApp(PreprocessingMixin, ManualAnalysisMixin, MLAnalysisMixin, ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WaveletAI  ·  Op-Amp Signal Intelligence Platform")
        self.geometry("1340x920")
        self.minsize(1100, 760)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=C["bg"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sig_path    = None
        self.excel_path  = None
        self.raw_hw_path = None

        self._build_sidebar()
        self._build_main()
        self._nav_btns[0].select()
        self.setup_pre()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0,
                                    fg_color=C["sidebar"],
                                    border_width=1, border_color=C["border"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(28, 20))
        ctk.CTkLabel(logo_frame, text="◈ WAVELET", font=("Consolas", 22, "bold"),
                     text_color=C["accent"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="AI SIGNAL PLATFORM", font=FONT_SMALL,
                     text_color=C["text_dim"]).pack(anchor="w")

        separator(self.sidebar, color=C["border"], pady=2)

        nav_items = [
            ("01", "⚙",  "Preprocessing",  self._nav_pre),
            ("02", "🔬", "Manual Analysis", self._nav_manual),
            ("03", "🤖", "AI / ML Mode",    self._nav_ml),
        ]
        self._nav_btns = []
        for step, icon, label, cmd in nav_items:
            btn = NavButton(self.sidebar, step, icon, label, cmd)
            btn.pack(fill="x", padx=4, pady=2)
            self._nav_btns.append(btn)

        separator(self.sidebar, color=C["border"], pady=8)

        status_card = make_card(self.sidebar)
        status_card.pack(fill="x", padx=12, pady=8)

        sh = ctk.CTkFrame(status_card, fg_color="transparent")
        sh.pack(fill="x", padx=12, pady=(10, 6))
        dim_label(sh, "SYSTEM STATUS").pack(side="left")
        self._dot = PulsingDot(sh, size=10)
        self._dot.pack(side="right", pady=2)

        self._status_lbl = ctk.CTkLabel(status_card, text="Ready",
                                         text_color=C["accent3"], font=FONT_SUB)
        self._status_lbl.pack(padx=12, pady=(0, 10), anchor="w")

        self._prog = AnimatedProgressBar(self.sidebar)
        self._prog.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(self.sidebar, text="v2.1.0  ·  2025",
                     text_color=C["text_dim"], font=FONT_SMALL).pack(side="bottom", pady=14)

    def _nav_pre(self):
        self._select_nav(0)
        self.setup_pre()

    def _nav_manual(self):
        self._select_nav(1)
        self.setup_manual()

    def _nav_ml(self):
        self._select_nav(2)
        self.setup_ml()

    def _select_nav(self, idx):
        for i, b in enumerate(self._nav_btns):
            b.select() if i == idx else b.deselect()

    def _build_main(self):
        self.main_frame = ctk.CTkScrollableFrame(
            self, corner_radius=0, fg_color=C["bg"],
            scrollbar_fg_color=C["surface"],
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent2"])
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

    def clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    def set_status(self, text, color=None):
        color = color or C["text_mid"]
        self._status_lbl.configure(text=text, text_color=color)

    def _page_header(self, title, subtitle, icon=""):
        hdr = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        hdr.pack(fill="x", padx=32, pady=(32, 4))
        row = ctk.CTkFrame(hdr, fg_color="transparent")
        row.pack(fill="x")
        if icon:
            ctk.CTkLabel(row, text=icon, font=("Segoe UI Emoji", 28)).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row, text=title, text_color=C["text"], font=FONT_TITLE).pack(side="left")
        if subtitle:
            ctk.CTkLabel(hdr, text=subtitle, text_color=C["text_dim"],
                         font=FONT_SUB).pack(anchor="w", pady=(4, 0))
        separator(self.main_frame, color=C["border"], pady=0)
        return hdr


if __name__ == "__main__":
    os.makedirs("tool/output", exist_ok=True)
    os.makedirs("tool/models", exist_ok=True)
    app = WaveletApp()
    app.mainloop()
