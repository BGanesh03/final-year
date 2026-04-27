import os
import threading
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import customtkinter as ctk
import joblib
from tkinter import messagebox
from datetime import datetime
from PIL import Image
from theme import C, FONT_SMALL, FONT_HEAD
from widgets import FilePickRow, TagBadge, MetricTile
from theme import make_card, accent_label, separator, primary_btn, ghost_btn
from tool.src.core_ml import get_wavelet_levels, reconstruct_optimized
from tool.src.trainer import extract_wavelet_features_l11 as extract_features


class MLAnalysisMixin:

    def setup_ml(self):
        self.clear_main()
        self._page_header("AI / ML Prediction",
                           "Run all trained models — XGBoost, Linear, RF, GPR", "🤖")

        in_card = make_card(self.main_frame)
        in_card.pack(fill="x", padx=32, pady=16)

        accent_label(in_card, "  INPUT SIGNAL", color=C["text_dim"],
                     font=FONT_SMALL).pack(anchor="w", padx=16, pady=(14, 4))
        separator(in_card, color=C["border"], pady=0)

        fp = ctk.CTkFrame(in_card, fg_color="transparent")
        fp.pack(fill="x", padx=16, pady=12)
        self._ml_sig_pick = FilePickRow(
            fp, "⊕  Test Signal CSV",
            [("CSV Files", "*.csv")], self._set_sig)
        self._ml_sig_pick.pack(anchor="w")

        mb = ctk.CTkFrame(in_card, fg_color="transparent")
        mb.pack(fill="x", padx=16, pady=(0, 14))
        for m, c in [("XGBoost", C["accent"]), ("Linear", C["accent2"]),
                     ("Random Forest", C["accent3"]), ("GPR", C["warn"])]:
            TagBadge(mb, m, color=c).pack(side="left", padx=4)

        run_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        run_row.pack(fill="x", padx=32, pady=4)
        self.ml_btn = primary_btn(
            run_row, "⚡  RUN ALL AI MODELS",
            self._start_ml_thread, color=C["accent2"], height=48, width=280)
        self.ml_btn.pack(side="left")

    def _set_sig(self, path):
        self.sig_path = path

    def _start_ml_thread(self):
        if not self.sig_path:
            return messagebox.showerror("Error", "Please upload a test signal CSV.")
        self.ml_btn.configure(state="disabled")
        self._prog.start()
        self._dot.set_active(True)
        self.set_status("Running models…", C["warn"])
        threading.Thread(target=self.execute_ml, daemon=True).start()

    def execute_ml(self):
        try:
            df   = pd.read_csv(self.sig_path)
            cin  = next((c for c in df.columns if 'vinp' in c.lower()), df.columns[0])
            cout = next((c for c in df.columns if 'vinn' in c.lower()),
                        df.columns[1] if len(df.columns) > 1 else df.columns[0])
            vin       = df[cin].values
            vinn_true = df[cout].values

            for m in ['xgboost', 'linear', 'rf', 'gpr']:
                gp = f"tool/models/gain_{m}.pkl"
                sp = f"tool/models/shift_{m}.pkl"
                if not os.path.exists(gp): continue

                mg = joblib.load(gp)
                ms = joblib.load(sp)
                ft = [extract_features(vin, level=11)]
                p_gains  = mg.predict(ft)[0]
                p_shifts = ms.predict(ft)[0]

                coeffs = get_wavelet_levels(vin)
                raw_data = []
                for i, la in enumerate(coeffs):
                    lbl = "A_12" if i == 0 else f"D_{13-i}"
                    for val in la:
                        raw_data.append({"Level": lbl, "coeffs": val})

                cfp = [c.copy() for c in coeffs]
                for i in range(len(cfp)):
                    if i < len(p_gains): cfp[i] *= p_gains[i]
                prediction = reconstruct_optimized(cfp, p_shifts)

                stage1 = []
                for i in range(len(coeffs)):
                    if i < len(p_gains):
                        lbl = "A_12" if i == 0 else f"D_{13-i}"
                        for j, val in enumerate(coeffs[i]):
                            stage1.append({
                                "Level": lbl, "Original Coeff": val,
                                "Gain (Predicted)": p_gains[i],
                                "Result (Coeff*Gain)": val*p_gains[i],
                                "": "",
                                "Shift (Predicted)": p_shifts[i],
                                "Prediction Result": prediction[j] if j < len(prediction) else "",
                            })

                od = "tool/output/intermediate"
                os.makedirs(od, exist_ok=True)
                ts  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                op  = os.path.join(od, f"wavelet_analysis_ML_{m}_{ts}.xlsx")
                with pd.ExcelWriter(op, engine="openpyxl") as w:
                    pd.DataFrame(raw_data).to_excel(w, sheet_name="decomposition", index=False)
                    pd.DataFrame(stage1).to_excel(w, sheet_name="stage 1", index=False)

                self.after(0,
                    lambda v=vin.copy(), t=vinn_true.copy(), p=prediction.copy(),
                           mod=m, g=p_gains.copy(), s=p_shifts.copy():
                    self.display_result(v, t, p, f"ML_{mod}", mod, g, s))

            self.after(0, lambda: self.ml_btn.configure(state="normal"))
            self.after(0, self._prog.stop)
            self.after(0, lambda: self._dot.set_active(False))
            self.after(0, lambda: self.set_status("All Models Done ✓", C["accent3"]))

        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("ML Error", str(err)))
            self.after(0, lambda: self.ml_btn.configure(state="normal"))
            self.after(0, self._prog.stop)
            self.after(0, lambda: self._dot.set_active(False))
            self.after(0, lambda: self.set_status("Failed", C["danger"]))

    def display_result(self, vin, true, pred, mode, name, gains, shifts):
        vin  = np.array(vin).flatten()
        true = np.array(true).flatten()
        pred = np.array(pred).flatten()
        n    = min(len(vin), len(true), len(pred))
        vin, true, pred = vin[:n], true[:n], pred[:n]

        mse  = np.mean((true - pred) ** 2)
        rmse = np.sqrt(mse)
        mae  = np.mean(np.abs(true - pred))
        sp   = np.mean(true ** 2)
        snr  = 10 * np.log10(sp / mse) if mse > 0 else 0

        print(f"\n{'='*30}\nModel: {mode} | {name}")
        print(f"  SNR={snr:.2f}dB ")
        print(f"  MSE={mse:.2e}  RMSE={rmse:.2e}  MAE={mae:.2e}")

        od = "tool/output"
        os.makedirs(od, exist_ok=True)
        ts       = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        img_path = os.path.join(od, f"plot_{mode}_{name}_{ts}.png")

        fig, ax = plt.subplots(figsize=(11, 3.8), facecolor="white")
        ax.set_facecolor("white")
        ax.plot(true, color="#1A56DB", lw=2.2, label="True Signal", alpha=1.0)
        ax.plot(pred, color="#E02020", lw=2.0, label="Predicted", alpha=1.0)
        ax.set_xlabel("Sample Index", color="#222222", fontsize=11, fontweight="bold")
        ax.set_ylabel("Voltage (V)",  color="#222222", fontsize=11, fontweight="bold")
        ax.set_title(
            f"{mode}  ·  {name.upper()}\n"
            f"SNR = {snr:.2f} dB   |   MSE = {mse:.4e}   |  ",
            color="#111111", fontsize=11, fontweight="bold", pad=12)
        ax.tick_params(colors="#333333", labelsize=10)
        for sp_ in ax.spines.values():
            sp_.set_color("#AAAAAA")
            sp_.set_linewidth(0.8)
        ax.legend(facecolor="white", edgecolor="#CCCCCC",
                  labelcolor="#111111", fontsize=11, framealpha=1.0, loc="upper right")
        ax.grid(color="#DDDDDD", linewidth=0.8, alpha=1.0)
        plt.tight_layout()
        plt.savefig(img_path, dpi=140, bbox_inches="tight", facecolor="white")
        plt.close()

        mode_color = {
            "xgboost": C["accent"],
            "linear":  C["accent2"],
            "rf":      C["accent3"],
            "gpr":     C["warn"],
        }.get(name.lower(), C["accent"])

        card = ctk.CTkFrame(self.main_frame, fg_color=C["surface"],
                            corner_radius=14, border_width=1,
                            border_color=mode_color)
        card.pack(pady=12, fill="x", padx=32)

        ch = ctk.CTkFrame(card, fg_color="transparent")
        ch.pack(fill="x", padx=16, pady=(14, 4))
        TagBadge(ch, mode.upper(), color=mode_color).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(ch, text=name.upper(), text_color=C["text"],
                     font=FONT_HEAD).pack(side="left")
        ghost_btn(ch, "📂  View Plot", width=120,
                  command=lambda p=img_path: os.startfile(p),
                  color=mode_color).pack(side="right")

        separator(card, color=mode_color, pady=0)

        mt = ctk.CTkFrame(card, fg_color="transparent")
        mt.pack(fill="x", padx=16, pady=12)
        for lbl, val, col in [
            ("SNR",  f"{snr:.2f} dB",  C["accent"]),
            ("MSE",  f"{mse:.3e}",     C["warn"]),
            ("RMSE", f"{rmse:.3e}",    C["text_mid"]),
            ("MAE",  f"{mae:.3e}",     C["text_mid"]),
        ]:
            MetricTile(mt, lbl, val, color=col).pack(side="left", padx=5, ipadx=6)

        try:
            img     = Image.open(img_path)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(860, 288))
            lbl_img = ctk.CTkLabel(card, image=ctk_img, text="")
            lbl_img.image = ctk_img
            lbl_img.pack(padx=16, pady=(4, 14))
        except Exception:
            pass
