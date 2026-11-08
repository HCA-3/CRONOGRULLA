with open("views/view_lesiones_3d.py", "r", encoding="utf-8") as f:
    content = f.read()

# Let's find project_3d definition
start_marker = "    def project_3d(self, x, y, z, cx, cy, img_scale=1.0, fov=650, yaw=None, pitch=None):"
end_marker = "            c.create_text(20, h - 20, anchor=\"w\", \n                          text=f\"{'Mujer ♀' if is_female else 'Hombre ♂'}  |  Zoom: {int(self.zoom_level*100)}%\",\n                          fill=\"#94a3b8\", font=(\"Helvetica\", 9))"

print("Start marker found:", start_marker in content)
print("End marker found:", end_marker in content)

