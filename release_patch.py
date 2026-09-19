from pathlib import Path
import ast,hashlib,json,sys
v=sys.argv[1]; assert v=="32.93"
p=Path("payload/app.py"); t=p.read_text(encoding="utf-8-sig")
def rep(a,b):
 global t
 assert t.count(a)==1,(a[:80],t.count(a))
 t=t.replace(a,b,1)
rep('APP_VERSION = "32.85"','APP_VERSION = "32.93"')
rep('S=4; OW,OH=48,36; W,H=OW*S,OH*S','S=4; OW,OH=52,44; W,H=OW*S,OH*S')
start=t.index('        elif kind=="tools":');end=t.index('        elif kind=="language":',start)
t=t[:start]+'''        elif kind=="tools":
            # A compact crossed wrench and screwdriver with longer, distinct handles.
            # The wrench jaw is drawn as two independent prongs (not a filled polygon),
            # leaving its mouth visibly open at the final navigation-icon resolution.
            # All geometry stays well inside the 52 x 44 source canvas.
            def line(points, fill, width, joint="curve"):
                d.line([(sc(x), sc(y)) for x, y in points], fill=fill,
                       width=sc(width), joint=joint)
            def poly(points, fill):
                d.polygon([(sc(x), sc(y)) for x, y in points], fill=fill)
            # Screwdriver: slim shaft from upper-right to lower-left; long handle.
            line([(39,8),(25,22)], blue, 3)
            line([(24,23),(11,36)], cyan, 5)
            d.ellipse((sc(8),sc(33),sc(14),sc(39)),fill=cyan)
            poly([(36,9),(40,5),(43,8),(39,12)], light)
            # Wrench: long diagonal stem, rounded grip at lower right.
            line([(17,16),(38,37)], light, 4)
            d.ellipse((sc(35),sc(34),sc(41),sc(40)),fill=cyan)
            # Open-end head: two prongs reach upper-left and lower-left.
            # No connecting stroke across the mouth between (9,8) and (9,17).
            line([(9,8),(14,12),(17,11),(20,14),(20,17),(17,20),
                  (14,20),(9,17)], light, 3)
            # A tiny central notch makes the jaw opening legible after resizing.
            poly([(9,10),(13,13),(16,13),(16,16),(13,16),(9,15)], (0,0,0,0))
'''+t[end:]
for a,b in [('img.thumbnail((44,34),Image.Resampling.LANCZOS)','img.thumbnail((35,32) if kind=="tools" else (44,36),Image.Resampling.LANCZOS)'),('canvas.create_image(26, 18, image=photo)','canvas.create_image(26, 22, image=photo)'),('menu_strip, bg=tile_bg, cursor="hand2", padx=18, pady=5,','menu_strip, bg=tile_bg, cursor="hand2", padx=14, pady=0,'),('tile.pack(side="left", padx=10, pady=4, fill="y")','tile.pack(side="left", padx=8, pady=0)'),('icon = tk.Canvas(tile, width=64, height=64, bg=tile_bg, highlightthickness=0, bd=0, cursor="hand2")','icon = tk.Canvas(tile, width=52, height=44, bg=tile_bg, highlightthickness=0, bd=0, cursor="hand2")'),('caption.pack(pady=(0, 4))','caption.pack(pady=(0, 1))'),('underline = tk.Frame(tile, height=5, bg="#08d8ff")','underline = tk.Frame(tile, height=3, bg="#08d8ff")')]:rep(a,b)
start=t.index('# v32.80: complete empty-state overlay visibility');end=t.index('root.after(300,_v3280_sync_empty)',start)+len('root.after(300,_v3280_sync_empty)')
t=t[:start]+'''# v32.93: Keep the empty-state overlay in sync with the ACTUAL download list.
# Use only the dedicated v3273_empty frame; do not hide its individual children.
# Treeview does not emit a reliable event for every insert/delete, so poll its
# immediate children. This also covers history restoration and bulk clearing.
def _v3293_sync_empty_state():
    try:
        has_downloads = bool(bulk_tree.get_children(""))
        is_visible = bool(v3273_empty.winfo_manager())
        if has_downloads and is_visible:
            v3273_empty.place_forget()
        elif not has_downloads and not is_visible:
            v3273_empty.place(relx=0.5, rely=0.54, anchor="center")
    except tk.TclError:
        return  # Window has closed.
    root.after(100, _v3293_sync_empty_state)

root.after(0, _v3293_sync_empty_state)'''+t[end:]
ast.parse(t)
p.write_text(t,encoding="utf-8")
h=hashlib.sha256(p.read_bytes()).hexdigest();assert h=="0feb79b7395777507aeb202ab76d34e6f0ff0aa6a0e26f797f27dd5ff6cfc72a",h
m=Path("payload/update_manifest.json");j=json.loads(m.read_text());j["version"]=v;j["created_by"]="v32.93 empty-state overlay follows actual bulk_tree rows; v32.92 navigation unchanged";j["files"][0]["sha256"]=h;j["files"][0]["size"]=p.stat().st_size;m.write_text(json.dumps(j,indent=2)+"\n")
print("VERIFIED exact v32.93 app.py sha256",h)
