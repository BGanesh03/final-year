import os
import threading
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from theme import C, FONT_SMALL, FONT_LABEL, FONT_MONO
from widgets import FilePickRow
from theme import make_card, accent_label, separator, primary_btn
from tool.src.core_ml import get_wavelet_levels, reconstruct_optimized


class ManualAnalysisMixin:

    def setup_manual(self):
        self.clear_main()
        self._page_header("Manual Analysis",
                           "Apply known gains & shifts via wavelet decomposition", "🔬")

        in_card = make_card(self.main_frame)
        in_card.pack(fill="x", padx=32, pady=16)

        accent_label(in_card, "  INPUT FILES", color=C["text_dim"],
                     font=FONT_SMALL).pack(anchor="w", padx=16, pady=(14, 4))
        separator(in_card, color=C["border"], pady=0)

        fp_frame = ctk.CTkFrame(in_card, fg_color="transparent")
        fp_frame.pack(fill="x", padx=16, pady=12)

        self._man_sig_pick = FilePickRow(
            fp_frame, "⊕  Test Signal CSV",
            [("CSV Files", "*.csv")], self._set_sig)
        self._man_sig_pick.pack(anchor="w", pady=6)

        self._man_xl_pick = FilePickRow(
            fp_frame, "⊕  Processed Excel",
            [("Excel Files", "*.xlsx")], self._set_excel)
        self._man_xl_pick.pack(anchor="w", pady=6)

        srow = ctk.CTkFrame(in_card, fg_color="transparent")
        srow.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(srow, text="Sheet Name", text_color=C["text_mid"],
                     font=FONT_LABEL, width=220, anchor="w").pack(side="left", padx=(0, 8))
        self.sheet_entry = ctk.CTkEntry(
            srow, placeholder_text="Sheet1",
            fg_color=C["surface2"], border_color=C["border"],
            text_color=C["text"], font=FONT_MONO,
            placeholder_text_color=C["text_dim"], width=200)
        self.sheet_entry.pack(side="left")

        run_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        run_row.pack(fill="x", padx=32, pady=4)
        self._man_btn = primary_btn(
            run_row, "▶  EXECUTE MANUAL ANALYSIS",
            self._run_manual_thread, color=C["accent3"], height=48, width=300)
        self._man_btn.configure(text_color="#000000")
        self._man_btn.pack(side="left")

    def _set_sig(self, path):
        self.sig_path = path

    def _set_excel(self, path):
        self.excel_path = path

    def _run_manual_thread(self):
        if not self.sig_path or not self.excel_path:
            return messagebox.showerror("Error", "Please load both CSV and Excel files.")
        sheet = self.sheet_entry.get() or "Sheet1"
        self._man_btn.configure(state="disabled")
        self._prog.start()
        self._dot.set_active(True)
        self.set_status("Analysing…", C["warn"])
        threading.Thread(target=self.execute_manual, args=(sheet,), daemon=True).start()

    def execute_manual(self, sheet):
        try:
            df   = pd.read_csv(self.sig_path)
            cin  = next((c for c in df.columns if 'vinp' in c.lower()), df.columns[0])
            cout = next((c for c in df.columns if 'vinn' in c.lower()),
                        df.columns[1] if len(df.columns) > 1 else df.columns[0])
            vin       = df[cin].values
            vinn_true = df[cout].values

            indices   = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
            params_df = pd.read_excel(self.excel_path, sheet_name=sheet)
            gains     = params_df.loc[indices, 'avg_gain'].values
            shifts    = params_df.loc[indices, 'avg_shift'].values

            coeffs = get_wavelet_levels(vin, level=12)

            raw_data = []
            for i, la in enumerate(coeffs):
                lbl = "A_12" if i == 0 else f"D_{13-i}"
                for val in la:
                    raw_data.append({" ": "", "  ": "", "Level": lbl, "coeffs": val})

            cfp = [c.copy() for c in coeffs]
            for i in range(len(cfp)):
                if i < len(gains): cfp[i] *= gains[i]
            prediction = reconstruct_optimized(cfp, shifts)

            stage1 = []
            for i in range(len(coeffs)):
                if i < len(gains):
                    lbl = "A_12" if i == 0 else f"D_{13-i}"
                    for j, val in enumerate(coeffs[i]):
                        stage1.append({
                            "Level": lbl, "Original Coeff": val,
                            "Gain": gains[i], "Result (Coeff*Gain)": val*gains[i],
                            "   ": "", "    ": "",
                            "Shift Value": shifts[i], "     ": "",
                            "Prediction Result": prediction[j] if j < len(prediction) else "",
                        })
                    coeffs[i] *= gains[i]

            od = "tool/output/intermediate"
            os.makedirs(od, exist_ok=True)
            ts  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            op  = os.path.join(od, f"wavelet_analysis_manual_{ts}.xlsx")
            with pd.ExcelWriter(op, engine="openpyxl") as w:
                pd.DataFrame(raw_data).to_excel(w, sheet_name="decomposition", index=False)
                pd.DataFrame(stage1).to_excel(w, sheet_name="stage 1", index=False)

            self.after(0, lambda v=vin.copy(), t=vinn_true.copy(), p=prediction.copy(),
                              g=gains.copy(), s=shifts.copy(), _ts=ts:
                       self._manual_done(v, t, p, sheet, g, s, _ts))
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Manual Error", str(err)))
            self.after(0, lambda: self.set_status("Failed", C["danger"]))
            self.after(0, self._prog.stop)
            self.after(0, lambda: self._dot.set_active(False))
            self.after(0, lambda: self._man_btn.configure(state="normal"))

    def _manual_done(self, vin, vt, pred, sheet, gains, shifts, ts):
        self._prog.stop()
        self._dot.set_active(False)
        self._man_btn.configure(state="normal")
        self.set_status("Manual Done ✓", C["accent3"])
        self.display_result(vin, vt, pred, "Manual", sheet, gains, shifts)
