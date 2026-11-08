import customtkinter as ctk
import tkinter as tk

app = ctk.CTk()
app.geometry("1100x700")

content_f = ctk.CTkFrame(app)
content_f.pack(fill="both", expand=True, padx=10, pady=10)

# Set up uniform grid
left_w = 40
right_w = 60
content_f.grid_columnconfigure(0, weight=left_w, uniform="main_cols")
content_f.grid_columnconfigure(1, weight=0)
content_f.grid_columnconfigure(2, weight=right_w, uniform="main_cols")
content_f.grid_rowconfigure(0, weight=1)

# Left box
left_box = ctk.CTkFrame(content_f, fg_color="#0f172a")
left_box.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
lbl_l = ctk.CTkLabel(left_box, text="3D Model Canvas Area", font=("Helvetica", 16))
lbl_l.pack(expand=True)

# Splitter
splitter = ctk.CTkFrame(content_f, width=12, fg_color="#334155", cursor="sb_h_double_arrow")
splitter.grid(row=0, column=1, sticky="ns", padx=2, pady=10)

# Right box
right_box = ctk.CTkScrollableFrame(content_f, fg_color="#1e293b",
                                   scrollbar_button_color="#38bdf8",
                                   scrollbar_button_hover_color="#0284c7")
right_box.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

for i in range(25):
    card = ctk.CTkFrame(right_box, fg_color="#0f172a")
    card.pack(fill="x", padx=10, pady=5)
    ctk.CTkLabel(card, text=f"Card Item #{i+1}: Detailed Clinical Occupational Diagnosis").pack(padx=10, pady=8)

app.update()

print("Initial widths:")
print("Left box width:", left_box.winfo_width())
print("Right box width:", right_box.winfo_width())

def set_split(right_pct):
    l = 100 - right_pct
    r = right_pct
    content_f.grid_columnconfigure(0, weight=l, uniform="main_cols")
    content_f.grid_columnconfigure(2, weight=r, uniform="main_cols")
    app.update()
    print(f"Set right={right_pct}% -> Left={left_box.winfo_width()}px, Right={right_box.winfo_width()}px")

set_split(70)
set_split(85)
set_split(50)

app.destroy()
print("Test completed successfully!")

