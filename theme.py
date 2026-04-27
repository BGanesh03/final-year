import customtkinter as ctk

C = {
    "bg": "#F5F7FB",
    "surface": "#FFFFFF",
    "surface2": "#F1F3F6",
    "border": "#D6DCE5",
    "accent": "#2563EB",
    "accent2": "#7C3AED",
    "accent3": "#16A34A",
    "warn": "#F59E0B",
    "danger": "#DC2626",
    "text": "#111827",
    "text_dim": "#6B7280",
    "text_mid": "#374151",
    "sidebar": "#FFFFFF",
    "sidebar_sel": "#E8F0FE",
    "grid": "#F8FAFC"
}

FONT_TITLE  = ("Segoe UI", 32, "bold")
FONT_HEAD   = ("Segoe UI", 18, "bold")
FONT_SUB    = ("Segoe UI", 15)
FONT_LABEL  = ("Segoe UI", 16)
FONT_MONO   = ("Consolas", 14)
FONT_SMALL  = ("Segoe UI", 13)
FONT_BTN    = ("Segoe UI", 16, "bold")
FONT_METRIC = ("Segoe UI", 26, "bold")


def _darken(hex_color, factor=0.7):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(int(r*factor), int(g*factor), int(b*factor))


def _lighten(hex_color, factor=1.3):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(min(255, int(r*factor)), min(255, int(g*factor)), min(255, int(b*factor)))


def make_card(parent, **kw):
    defaults = dict(fg_color=C["surface"], corner_radius=12,
                    border_width=1, border_color=C["border"])
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def accent_label(parent, text, color=None, font=None, **kw):
    color = color or C["accent"]
    font  = font  or FONT_HEAD
    return ctk.CTkLabel(parent, text=text, text_color=color, font=font, **kw)


def dim_label(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text, text_color=C["text_dim"], font=FONT_SUB, **kw)


def primary_btn(parent, text, command, color=None, **kw):
    color = color or C["accent2"]
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=color, hover_color=_darken(color),
        text_color=C["text"], font=FONT_BTN,
        corner_radius=8, border_width=1,
        border_color=_lighten(color), **kw
    )


def ghost_btn(parent, text, command, color=None, **kw):
    color = color or C["accent"]
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color="transparent", hover_color=C["surface2"],
        text_color=color, font=FONT_BTN,
        corner_radius=8, border_width=1,
        border_color=color, **kw
    )


def separator(parent, color=None, pady=4):
    color = color or C["border"]
    f = ctk.CTkFrame(parent, height=1, fg_color=color, corner_radius=0)
    f.pack(fill="x", padx=20, pady=pady)
    return f
