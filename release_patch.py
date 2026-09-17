from pathlib import Path
import ast, hashlib, json, re, sys
TARGET_VERSION="32.79"
def sha256_file(path):
    d=hashlib.sha256()
    with open(path,"rb") as h:
        for c in iter(lambda:h.read(1024*1024),b""): d.update(c)
    return d.hexdigest()
version=str(sys.argv[1] if len(sys.argv)>1 else "").strip()
if version!=TARGET_VERSION: raise SystemExit(f"This patch prepares only v{TARGET_VERSION}; got {version!r}")
app_path=Path("payload/app.py"); updater_path=Path("payload/z2se_updater.pyw"); manifest_path=Path("payload/update_manifest.json")
for p in (app_path,updater_path,manifest_path):
    if not p.is_file(): raise FileNotFoundError(p)
text=app_path.read_text(encoding="utf-8-sig")
text,n=re.subn(r'APP_VERSION\s*=\s*"32\.78"','APP_VERSION = "32.79"',text,count=1)
if n!=1: raise RuntimeError("Could not update APP_VERSION 32.78 -> 32.79")

# Remove the ineffective v32.78 watcher completely.
s=text.find('# v32.78: empty helper is visible only when there are no download rows.')
if s>=0:
    e=text.find('root.after(150, _v3278_empty_state_watch)',s)
    if e>=0:
        e=text.find('\n',e); text=text[:s]+text[e+1:]
text=text.replace('downloads_tree.bind("<<TreeviewOpen>>", _v3278_sync_empty_download_state, add="+")\n','')

# Robust empty-state fix without guessing source variable names: at runtime locate the
# Label whose cget("text") is exactly "Aucun téléchargement", then hide/show its
# overlay container according to whether the Treeview has rows. We save geometry so
# the helper returns when the list becomes empty again.
anchor='root.after(150, _v3278_empty_state_watch)'
# inject near the end of the UI setup, before mainloop if possible
mainloop_pos=text.rfind('root.mainloop()')
if mainloop_pos<0: mainloop_pos=text.rfind('.mainloop()')
if mainloop_pos<0: raise RuntimeError("Could not locate Tk mainloop")
helper=r'''
# v32.79: row-aware empty download helper, discovered from live Tk widgets.
_v3279_empty_overlay = None
_v3279_empty_geom = None

def _v3279_walk_widgets(w):
    try:
        for child in w.winfo_children():
            yield child
            yield from _v3279_walk_widgets(child)
    except Exception:
        return

def _v3279_find_empty_overlay():
    global _v3279_empty_overlay, _v3279_empty_geom
    if _v3279_empty_overlay is not None:
        return _v3279_empty_overlay
    try:
        for w in _v3279_walk_widgets(root):
            try:
                if str(w.cget("text")).strip() == "Aucun téléchargement":
                    # The title sits inside the centered helper frame. Use its parent,
                    # never the downloads table itself.
                    _v3279_empty_overlay = w.master
                    mgr = _v3279_empty_overlay.winfo_manager()
                    if mgr == "place": _v3279_empty_geom = ("place", _v3279_empty_overlay.place_info())
                    elif mgr == "grid": _v3279_empty_geom = ("grid", _v3279_empty_overlay.grid_info())
                    elif mgr == "pack": _v3279_empty_geom = ("pack", _v3279_empty_overlay.pack_info())
                    return _v3279_empty_overlay
            except Exception:
                pass
    except Exception:
        pass
    return None

def _v3279_sync_empty_state():
    try:
        overlay=_v3279_find_empty_overlay()
        if overlay is not None:
            has_rows=bool(downloads_tree.get_children())
            mgr=overlay.winfo_manager()
            if has_rows and mgr:
                if mgr=="place": overlay.place_forget()
                elif mgr=="grid": overlay.grid_remove()
                elif mgr=="pack": overlay.pack_forget()
            elif (not has_rows) and (not mgr) and _v3279_empty_geom:
                kind,info=_v3279_empty_geom
                if kind=="place": overlay.place(**info)
                elif kind=="grid": overlay.grid(**info)
                elif kind=="pack": overlay.pack(**info)
        root.after(120, _v3279_sync_empty_state)
    except Exception:
        try: root.after(500, _v3279_sync_empty_state)
        except Exception: pass
root.after(250, _v3279_sync_empty_state)

'''
text=text[:mainloop_pos]+helper+text[mainloop_pos:]

# Actually shrink the whole premium nav footprint, not only the image pixels.
text=text.replace('def _v3276_make_nav_icon(kind, active=False, size=54):','def _v3276_make_nav_icon(kind, active=False, size=42):',1)
text=text.replace('_v3276_make_nav_icon(kind, active=active, size=54)','_v3276_make_nav_icon(kind, active=active, size=42)',1)
text=text.replace('width=58,\n        height=58,','width=48,\n        height=48,',1)
text=text.replace('canvas.create_image(29, 29, image=photo)','canvas.create_image(24, 24, image=photo)',1)
text=text.replace('height=126','height=106',1)

# Smart Recovery: broaden classification for current YouTube SABR / PO / 403 failure
# wording. Existing recovery machinery remains authoritative; this only makes these
# failures enter recovery instead of being treated as generic terminal errors.
needle='"sabr"'
if needle in text:
    # Extend the first SABR-related tuple/list occurrence conservatively with modern signals.
    p=text.find(needle)
    close=text.find(')',p)
    if close>p and close-p<1800:
        addition=', "po token", "pot token", "googlevideo", "http error 403", "forbidden", "login_required", "sign in to confirm", "only images are available"'
        segment=text[p:close]
        if 'googlevideo' not in segment:
            text=text[:close]+addition+text[close:]

# Diagnostics only.
text=text.replace('Clean Editor v32.78:','Clean Editor v32.79:',1)
text=text.replace('Clean Editor v32.78 warning:','Clean Editor v32.79 warning:',1)
text=text.replace('Download details v32.78 warning:','Download details v32.79 warning:',1)

ast.parse(text)
app_path.write_text(text,encoding="utf-8")
manifest=json.loads(manifest_path.read_text(encoding="utf-8")); manifest["product"]="Z2SE Media Downloader"; manifest["version"]=TARGET_VERSION
manifest["created_by"]="GitHub Actions / v32.79 row-aware empty state + smaller premium nav + expanded YouTube recovery signals"
manifest["files"]=[{"path":"app.py","sha256":sha256_file(app_path),"size":app_path.stat().st_size},{"path":"z2se_updater.pyw","sha256":sha256_file(updater_path),"size":updater_path.stat().st_size}]
manifest_path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print("Prepared Z2SE v32.79")
