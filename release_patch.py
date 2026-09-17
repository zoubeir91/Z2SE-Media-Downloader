from pathlib import Path
import ast, hashlib, json, re, sys
TARGET_VERSION="32.80"
def sha256_file(path):
 d=hashlib.sha256()
 with open(path,"rb") as h:
  for c in iter(lambda:h.read(1048576),b""): d.update(c)
 return d.hexdigest()
version=str(sys.argv[1] if len(sys.argv)>1 else "").strip()
if version!=TARGET_VERSION: raise SystemExit(f"Expected {TARGET_VERSION}, got {version!r}")
app=Path("payload/app.py"); updater=Path("payload/z2se_updater.pyw"); manifest=Path("payload/update_manifest.json")
text=app.read_text(encoding="utf-8-sig")
text,n=re.subn(r'APP_VERSION\s*=\s*"32\.79"','APP_VERSION = "32.80"',text,count=1)
if n!=1: raise RuntimeError("APP_VERSION 32.79 not found")

# Remove v32.79 watcher. It found the inner label parent, while the empty UI is drawn
# as multiple sibling widgets; hiding one parent therefore did not remove the overlay.
s=text.find('# v32.79: row-aware empty download helper')
if s>=0:
 e=text.find('root.after(250, _v3279_sync_empty_state)',s)
 if e>=0:
  e=text.find('\n',e); text=text[:s]+text[e+1:]

# Definitive runtime solution: discover every visible widget belonging to the empty-state
# by text and spatial proximity, remember each geometry manager, and hide the complete set
# whenever the Treeview contains rows. This handles the icon/title/subtitle/badges even if
# they are siblings rather than one frame.
mp=text.rfind('root.mainloop()')
if mp<0: raise RuntimeError("root.mainloop not found")
helper=r'''
# v32.80: complete empty-state overlay visibility
_v3280_empty_items = []
_v3280_scanned = False

def _v3280_walk(w):
    try:
        for c in w.winfo_children():
            yield c
            yield from _v3280_walk(c)
    except Exception:
        return

def _v3280_save_widget(w):
    try:
        if any(x[0] is w for x in _v3280_empty_items): return
        mgr=w.winfo_manager()
        if mgr=="place": info=w.place_info()
        elif mgr=="grid": info=w.grid_info()
        elif mgr=="pack": info=w.pack_info()
        else: return
        _v3280_empty_items.append((w,mgr,info))
    except Exception: pass

def _v3280_scan_empty_items():
    global _v3280_scanned
    if _v3280_scanned: return
    try:
        root.update_idletasks()
        title=None
        allw=list(_v3280_walk(root))
        for w in allw:
            try:
                if str(w.cget("text")).strip()=="Aucun téléchargement": title=w; break
            except Exception: pass
        if title is None: return
        _v3280_save_widget(title)
        parent=title.master
        # Empty-state elements are siblings around the title. Select only known helper
        # texts plus small canvas/icon widgets in the same parent; never touch Treeview.
        helper_texts={"Aucun téléchargement","VIDEO","AUDIO","PART","HLS"}
        for w in list(parent.winfo_children()):
            try:
                txt=str(w.cget("text")).strip()
            except Exception: txt=""
            cls=str(w.winfo_class()).lower()
            if txt in helper_texts or "Collez un lien ci-dessus" in txt:
                _v3280_save_widget(w)
            elif "canvas" in cls:
                try:
                    # only the centered empty-state canvas, not arbitrary large canvases
                    if int(w.winfo_width())<=100 and int(w.winfo_height())<=100:
                        _v3280_save_widget(w)
                except Exception: pass
        # If title is inside a dedicated tiny overlay frame, hiding that frame is safest.
        try:
            if str(parent.winfo_class()).lower() in ("frame","tframe") and len(parent.winfo_children())<=12:
                _v3280_save_widget(parent)
        except Exception: pass
        _v3280_scanned=bool(_v3280_empty_items)
    except Exception: pass

def _v3280_show_saved(w,mgr,info):
    try:
        if w.winfo_manager(): return
        if mgr=="place": w.place(**info)
        elif mgr=="grid": w.grid(**info)
        elif mgr=="pack": w.pack(**info)
    except Exception: pass

def _v3280_sync_empty():
    try:
        _v3280_scan_empty_items()
        has_rows=bool(downloads_tree.get_children())
        # Hide children before parent; restore parent before children.
        items=list(_v3280_empty_items)
        if has_rows:
            for w,mgr,info in items:
                try:
                    cur=w.winfo_manager()
                    if cur=="place": w.place_forget()
                    elif cur=="grid": w.grid_remove()
                    elif cur=="pack": w.pack_forget()
                except Exception: pass
        else:
            for w,mgr,info in reversed(items): _v3280_show_saved(w,mgr,info)
        root.after(100,_v3280_sync_empty)
    except Exception:
        try: root.after(400,_v3280_sync_empty)
        except Exception: pass
root.after(300,_v3280_sync_empty)

'''
text=text[:mp]+helper+text[mp:]

# v32.79 screenshot confirms artwork still visually large. Reduce premium icon artwork
# from 42 to 32 px, canvas to 38 px, and active tile/nav vertical footprint accordingly.
text=text.replace('def _v3276_make_nav_icon(kind, active=False, size=42):','def _v3276_make_nav_icon(kind, active=False, size=32):',1)
text=text.replace('_v3276_make_nav_icon(kind, active=active, size=42)','_v3276_make_nav_icon(kind, active=active, size=32)',1)
text=text.replace('width=48,\n        height=48,','width=38,\n        height=38,',1)
text=text.replace('canvas.create_image(24, 24, image=photo)','canvas.create_image(19, 19, image=photo)',1)
text=text.replace('height=106','height=92',1)
# Also shrink label font/padding if the exact premium values remain.
text=text.replace('font=("Segoe UI", 11)', 'font=("Segoe UI", 10)', 5)
text=text.replace('pady=(4, 3)','pady=(2, 2)',1)

# Keep the expanded YouTube recovery signals inherited from 32.79 and completed-media play.
text=text.replace('Clean Editor v32.79:','Clean Editor v32.80:',1)
text=text.replace('Clean Editor v32.79 warning:','Clean Editor v32.80 warning:',1)
text=text.replace('Download details v32.79 warning:','Download details v32.80 warning:',1)
ast.parse(text); app.write_text(text,encoding="utf-8")
m=json.loads(manifest.read_text(encoding="utf-8")); m["version"]=TARGET_VERSION; m["created_by"]="GitHub Actions / v32.80 complete empty-overlay removal + compact 32px premium navigation + Smart Recovery preserved"
m["files"]=[{"path":"app.py","sha256":sha256_file(app),"size":app.stat().st_size},{"path":"z2se_updater.pyw","sha256":sha256_file(updater),"size":updater.stat().st_size}]
manifest.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
print("Prepared Z2SE v32.80")
