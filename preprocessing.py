import os
import threading
import numpy as np
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox
from theme import C, FONT_SMALL, FONT_MONO
from widgets import FilePickRow, MetricTile, TagBadge
from theme import make_card, accent_label, dim_label, primary_btn, ghost_btn, separator


class PreprocessingMixin:

    def setup_pre(self):
        self.clear_main()
        self._page_header("Preprocessing", "Convert raw hardware CSV → training-ready Excel", "⚙")

        up_card = make_card(self.main_frame)
        up_card.pack(fill="x", padx=32, pady=16)

        accent_label(up_card, "  DATA INGESTION", color=C["text_dim"],
                     font=FONT_SMALL).pack(anchor="w", padx=16, pady=(14, 4))
        separator(up_card, color=C["border"], pady=0)

        pick_row = ctk.CTkFrame(up_card, fg_color="transparent")
        pick_row.pack(fill="x", padx=16, pady=16)
        self._pre_pick = FilePickRow(
            pick_row,
            label="⊕  Raw Hardware CSV",
            filetypes=[("CSV Files", "*.csv")],
            on_pick=self._set_raw_hw)
        self._pre_pick.pack(anchor="w")

        pills = ctk.CTkFrame(up_card, fg_color="transparent")
        pills.pack(fill="x", padx=16, pady=(0, 14))
        for tag, col in [("gain dB→linear", C["accent"]),
                         ("del_t / delay / shift_courage", C["accent2"]),
                         ("Phase_2 / avg_shift", C["accent3"]),
                         ("avg_gain block-avg", C["warn"])]:
            TagBadge(pills, tag, color=col).pack(side="left", padx=4)

        run_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        run_row.pack(fill="x", padx=32, pady=4)
        self._pre_run_btn = primary_btn(
            run_row, "⚡  GENERATE PROCESSED DATA",
            self._run_pre_thread, color=C["accent2"], height=48, width=300)
        self._pre_run_btn.pack(side="left")

        self._pre_preview = make_card(self.main_frame)
        self._pre_preview.pack(fill="x", padx=32, pady=16)
        dim_label(self._pre_preview,
                  "Output preview will appear here after processing.").pack(pady=24)

    def _set_raw_hw(self, path):
        self.raw_hw_path = path

    def _run_pre_thread(self):
        if not self.raw_hw_path:
            return messagebox.showerror("Error", "Please select a CSV file first.")
        self._pre_run_btn.configure(state="disabled")
        self._prog.start()
        self._dot.set_active(True)
        self.set_status("Processing…", C["warn"])
        threading.Thread(target=self.execute_preprocessing, daemon=True).start()

    def execute_preprocessing(self):
        try:
            df = pd.read_csv(self.raw_hw_path)

            gain_cols = [c for c in df.columns
                         if "db20" in c.lower() or "gain" in c.lower()]
            if not gain_cols:
                raise ValueError("No gain column found (need 'db20' or 'gain' in name).")
            g_col      = gain_cols[0]
            df["gain"] = 10 ** (df[g_col] / 20)

            df["del_t"]         = (df["Phase"] / 360) * (1 / df["freq"])
            df["delay"]         = df["del_t"] * 1_000_000_000
            df["shift_courage"] = df["delay"].round()

            df["Phase_2"]   = df["Phase"] / 2
            df["del_t2"]    = (df["Phase_2"] / 360) * (1 / df["freq"])
            df["delay2"]    = df["del_t2"] * 1_000_000_000
            df["avg_shift"] = df["delay2"].round()

            df["avg_gain"] = np.nan
            total_rows     = len(df)
            n, cur         = 0, 0
            while cur < total_rows:
                bs   = 2 ** n
                s, e = cur, min(cur + bs, total_rows)
                avg  = df["gain"].iloc[s:e].mean()
                df.loc[s:e - 1, "avg_gain"] = avg
                cur, n = e, n + 1

            out_path = self.raw_hw_path.replace(".csv", "_processed.xlsx")
            df.to_excel(out_path, index=False)

            preview_cols = [g_col, "gain", "del_t", "delay", "shift_courage",
                            "Phase_2", "del_t2", "delay2", "avg_shift", "avg_gain"]
            preview_cols = [c for c in preview_cols if c in df.columns]
            pv_df        = df[preview_cols].tail(20).reset_index(drop=True)
            records      = pv_df.round(6).to_dict("records")
            headers      = list(pv_df.columns)
            row_count    = len(df)

            self.after(0, lambda r=records, h=headers, op=out_path, rc=row_count:
                       self._pre_done(r, h, op, rc))

        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Preprocessing Error", str(err)))
            self.after(0, lambda: self.set_status("Failed", C["danger"]))
            self.after(0, self._prog.stop)
            self.after(0, lambda: self._dot.set_active(False))
            self.after(0, lambda: self._pre_run_btn.configure(state="normal"))

    def _pre_done(self, records, headers, out_path, row_count):
        self._prog.stop()
        self._dot.set_active(False)
        self.set_status("Done ✓", C["accent3"])
        self._pre_run_btn.configure(state="normal")

        for w in self._pre_preview.winfo_children():
            w.destroy()

        metrics_row = ctk.CTkFrame(self._pre_preview, fg_color="transparent")
        metrics_row.pack(fill="x", padx=16, pady=16)
        for label, val, color in [
            ("ROWS PROCESSED",  f"{row_count:,}", C["accent"]),
            ("COLUMNS CREATED", f"{len(headers)}", C["accent2"]),
            ("PREVIEW ROWS",    f"{len(records)}", C["accent3"]),
        ]:
            MetricTile(metrics_row, label, val, color=color).pack(side="left", padx=6, ipadx=8)

        separator(self._pre_preview, color=C["border"], pady=4)

        th = ctk.CTkFrame(self._pre_preview, fg_color="transparent")
        th.pack(fill="x", padx=16, pady=(4, 0))
        accent_label(th, "LAST 20 ROWS  ·  OUTPUT COLUMNS",
                     color=C["text_dim"], font=FONT_SMALL).pack(side="left")
        ghost_btn(th, "📂  Open Excel", width=130,
                  command=lambda p=out_path: os.startfile(p),
                  color=C["accent3"]).pack(side="right")

        tbl_scroll = ctk.CTkScrollableFrame(
            self._pre_preview, height=260,
            fg_color=C["bg"], orientation="horizontal",
            scrollbar_fg_color=C["surface"],
            scrollbar_button_color=C["border"])
        tbl_scroll.pack(fill="x", padx=16, pady=(4, 16))

        tbl   = ctk.CTkFrame(tbl_scroll, fg_color="transparent")
        tbl.pack(anchor="w")
        col_w = 118

        for ci, h in enumerate(headers):
            ctk.CTkLabel(tbl, text=h, width=col_w, font=FONT_SMALL,
                         text_color=C["accent"], fg_color=C["surface2"],
                         corner_radius=0, padx=6, pady=5,
                         anchor="w").grid(row=0, column=ci, padx=1, pady=1, sticky="nsew")

        for ri, row in enumerate(records, start=1):
            bg = C["grid"] if ri % 2 == 0 else C["surface"]
            for ci, h in enumerate(headers):
                val = row.get(h, "")
                if isinstance(val, float):
                    val = f"{val:.4f}"
                ctk.CTkLabel(tbl, text=str(val), width=col_w,
                             font=FONT_MONO, fg_color=bg,
                             text_color=C["text_mid"], corner_radius=0,
                             padx=6, pady=3, anchor="w").grid(
                    row=ri, column=ci, padx=1, pady=1, sticky="nsew")
