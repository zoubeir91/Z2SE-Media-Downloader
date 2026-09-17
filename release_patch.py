from pathlib import Path
import ast, hashlib, json, re, sys
TARGET_VERSION="32.83"
def sha256_file(path):
 d=hashlib.sha256()
 with open(path,"rb") as h:
  for c in iter(lambda:h.read(1048576),b""): d.update(c)
 return d.hexdigest()
version=str(sys.argv[1] if len(sys.argv)>1 else "").strip()
if version!=TARGET_VERSION: raise SystemExit(f"Expected {TARGET_VERSION}, got {version!r}")
app=Path("payload/app.py"); updater=Path("payload/z2se_updater.pyw"); manifest=Path("payload/update_manifest.json")
text=app.read_text(encoding="utf-8-sig")
text,n=re.subn(r'APP_VERSION\s*=\s*"32\.82"','APP_VERSION = "32.83"',text,count=1)
if n!=1: raise RuntimeError("APP_VERSION 32.82 not found")

# Keep the compact header height. Increase only visible icon artwork and tighten the
# icon-to-label gap so each navigation item reads as one centered professional block.
# v32.82 renderer has a 46x42 safe output; scale the artwork coordinates by replacing
# its output with 50x46 while retaining margins, then use a 58x50 Tk canvas.
text=text.replace('def _v3276_make_nav_icon(kind, active=False, size=32):','def _v3276_make_nav_icon(kind, active=False, size=38):',1)
text=text.replace('out_w, out_h = 46, 42','out_w, out_h = 50, 46',1)
# Generator coordinates occupy roughly 30px; enlarge final composed artwork modestly
# before returning while preserving transparency and antialiasing.
old='return ImageTk.PhotoImage(composed.resize((out_w,out_h),Image.Resampling.LANCZOS))'
new='return ImageTk.PhotoImage(composed.resize((out_w,out_h), Image.Resampling.LANCZOS))'
text=text.replace(old,new,1)
text=text.replace('width=54,\n        height=46,','width=58,\n        height=50,',1)
text=text.replace('canvas.create_image(27, 23, image=photo)','canvas.create_image(29, 25, image=photo)',1)

# Tighten vertical spacing between icon canvas and label. The menu builder packs the
# canvas and text separately; reduce both surrounding paddings without changing header.
text=text.replace('icon_canvas.pack(pady=(2, 2))','icon_canvas.pack(pady=(1, 0))',1)
text=text.replace('label.pack(pady=(0, 4))','label.pack(pady=(0, 1))',1)
text=text.replace('label.pack(pady=(0, 3))','label.pack(pady=(0, 1))',1)
# Some builds use a generic pack for the label; make only the first nav-label occurrence tighter.
navpos=text.find('def _make_top_menu_button')
if navpos>=0:
 segend=text.find('\n\ndef ',navpos+10)
 if segend<0: segend=min(len(text),navpos+7000)
 seg=text[navpos:segend]
 seg=seg.replace('pady=(2, 2)', 'pady=(0, 0)', 1)
 text=text[:navpos]+seg+text[segend:]

text=text.replace('Clean Editor v32.82:','Clean Editor v32.83:',1)
text=text.replace('Clean Editor v32.82 warning:','Clean Editor v32.83 warning:',1)
text=text.replace('Download details v32.82 warning:','Download details v32.83 warning:',1)
ast.parse(text); app.write_text(text,encoding="utf-8")
m=json.loads(manifest.read_text(encoding="utf-8")); m["version"]=TARGET_VERSION; m["created_by"]="GitHub Actions / v32.83 balanced 38px premium nav, tighter icon-label spacing; compact header and functional fixes preserved"
m["files"]=[{"path":"app.py","sha256":sha256_file(app),"size":app.stat().st_size},{"path":"z2se_updater.pyw","sha256":sha256_file(updater),"size":updater.stat().st_size}]
manifest.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
print("Prepared Z2SE v32.83")
