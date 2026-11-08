import customtkinter as ctk
import json
import os
import pandas as pd
from tkinter import filedialog, messagebox

class MediaGalleryView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app; self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent"); header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(header, text="📊 GALERÍA TÉCNICA", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent"); self.scroll.pack(fill="both", expand=True, padx=20)
        self.refresh_gallery()

    def refresh_gallery(self):
        for w in self.scroll.winfo_children(): w.destroy()
        data = self.app.data.get("measurements", [])
        for m in reversed(data): self.create_card(m)

    def create_card(self, m):
        card = ctk.CTkFrame(self.scroll, corner_radius=15, border_width=1, border_color=("#e2e8f0", "#334155"))
        card.pack(fill="x", pady=10, padx=5)
        
        header = ctk.CTkFrame(card, fg_color="transparent"); header.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(header, text=f"Estudio {m.get('id')} - {m.get('timestamp')}", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        grid = ctk.CTkFrame(card, fg_color="transparent"); grid.pack(fill="x", padx=15, pady=5)
        
        # Tarjeta LUX
        lux_f = ctk.CTkFrame(grid, fg_color=("#e0f2fe", "#0c4a6e"), corner_radius=10)
        lux_f.pack(side="left", fill="both", expand=True, padx=(0,5))
        lux_data = m.get("env_lux", [])
        lux_txt = ", ".join([f"{l['puesto']}: {sum(l['lux'])/len(l['lux']):.0f}lx" for l in lux_data if l.get('lux')])
        ctk.CTkLabel(lux_f, text="💡 LUX", font=ctk.CTkFont(size=11, weight="bold")).pack(); ctk.CTkLabel(lux_f, text=lux_txt or "N/R").pack()

        # Tarjeta SONO
        sono_f = ctk.CTkFrame(grid, fg_color=("#fef2f2", "#450a0a"), corner_radius=10)
        sono_f.pack(side="left", fill="both", expand=True, padx=(5,0))
        sono_data = m.get("env_sound", [])
        sono_txt = ", ".join([f"{s['operario']}: {sum(d['db'] for d in s['medidas'])/len(s['medidas']):.1f}dB" for s in sono_data if s.get('medidas')])
        ctk.CTkLabel(sono_f, text="🔊 SONO", font=ctk.CTkFont(size=11, weight="bold")).pack(); ctk.CTkLabel(sono_f, text=sono_txt or "N/R").pack()

        btns = ctk.CTkFrame(card, fg_color="transparent"); btns.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(btns, text="EDITAR", width=100, command=lambda: messagebox.showinfo("Info", "Editor abierto")).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="EXPORTAR EXCEL", width=100, fg_color="#10b981", command=lambda: messagebox.showinfo("Info", "Exportando...")).pack(side="left", padx=5)
