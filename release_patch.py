from pathlib import Path
import ast, hashlib, json, re, sys
TARGET_VERSION="32.85"
def sha256_file(path):
 d=hashlib.sha256()
 with open(path,"rb") as h:
  for c in iter(lambda:h.read(1048576),b""): d.update(c)
 return d.hexdigest()
version=str(sys.argv[1] if len(sys.argv)>1 else "").strip()
if version!=TARGET_VERSION: raise SystemExit(f"Expected {TARGET_VERSION}, got {version!r}")
app=Path("payload/app.py"); updater=Path("payload/z2se_updater.pyw"); manifest=Path("payload/update_manifest.json")
text=app.read_text(encoding="utf-8-sig")
text,n=re.subn(r'APP_VERSION\s*=\s*"32\.84"','APP_VERSION = "32.85"',text,count=1)
if n!=1: raise RuntimeError("APP_VERSION 32.84 not found")

# v32.85 NAV: the screenshot proves the labels are being clipped by the compact menu.
# Keep the header height, but make the icon canvas shorter and pull the label upward.
# Artwork stays professional and fully visible; icon+label now fit as one block.
text=text.replace('S=4; OW,OH=52,44; W,H=OW*S,OH*S','S=4; OW,OH=48,36; W,H=OW*S,OH*S',1)
# Scale the existing renderer vertically into the shorter safe output.
text=text.replace('img=Image.alpha_composite(glow,base).resize((OW,OH),Image.Resampling.LANCZOS)',
'''img=Image.alpha_composite(glow,base)
        # Crop transparent vertical excess, then fit without cutting the actual icon.
        bbox=img.getbbox()
        if bbox:
            img=img.crop(bbox)
        img.thumbnail((44,34),Image.Resampling.LANCZOS)
        out=Image.new("RGBA",(OW,OH),(0,0,0,0))
        out.alpha_composite(img,((OW-img.width)//2,(OH-img.height)//2))
        img=out''',1)
text=text.replace('width=56,\n        height=45,','width=52,\n        height=36,',1)
text=text.replace('canvas.create_image(28, 22, image=photo)','canvas.create_image(26, 18, image=photo)',1)

# Force the navigation builder itself to use a tight icon/label stack.
nav=text.find('def _make_top_menu_button')
if nav<0: raise RuntimeError("top menu builder not found")
e=text.find('\n\ndef ',nav+10)
if e<0: e=min(len(text),nav+9000)
seg=text[nav:e]
# Remove vertical padding around icon/label and shrink only nav text slightly.
seg=seg.replace('icon_canvas.pack(', 'icon_canvas.pack(', 1)
seg=re.sub(r'icon_canvas\.pack\([^\n]*\)', 'icon_canvas.pack(pady=(0,0))', seg, count=1)
seg=re.sub(r'label\.pack\([^\n]*\)', 'label.pack(pady=(0,0))', seg, count=1)
seg=seg.replace('font=("Segoe UI", 10)','font=("Segoe UI", 9)',1)
text=text[:nav]+seg+text[e:]

# Recovery v3 readiness: keep v32.84 classifier and add a small compatibility helper
# for the native yt-dlp PO-token framework / JS runtime migration. No external provider
# is forced and no downloader path is removed.
mp=text.rfind('root.mainloop()')
if mp<0: raise RuntimeError("mainloop not found")
helper=r'''
# v32.85 YouTube readiness helper for modern yt-dlp.
def _v3285_youtube_readiness_from_log(message):
    s=str(message or "").lower()
    state={"js_runtime":True,"po_provider":True,"legacy_getpot":False}
    if "no supported javascript runtime" in s or "javascript runtime" in s and "missing" in s:
        state["js_runtime"]=False
    if "po token" in s and ("provider" in s or "missing" in s or "not available" in s):
        state["po_provider"]=False
    if "get-pot" in s or "getpot" in s:
        state["legacy_getpot"]=True
    return state

'''
text=text[:mp]+helper+text[mp:]
text=text.replace('Clean Editor v32.84:','Clean Editor v32.85:',1)
text=text.replace('Clean Editor v32.84 warning:','Clean Editor v32.85 warning:',1)
text=text.replace('Download details v32.84 warning:','Download details v32.85 warning:',1)
ast.parse(text); app.write_text(text,encoding="utf-8")
m=json.loads(manifest.read_text(encoding="utf-8")); m["version"]=TARGET_VERSION
m["created_by"]="GitHub Actions / v32.85 compact unclipped nav stack + yt-dlp readiness helper; existing recovery preserved"
m["files"]=[{"path":"app.py","sha256":sha256_file(app),"size":app.stat().st_size},{"path":"z2se_updater.pyw","sha256":sha256_file(updater),"size":updater.stat().st_size}]
manifest.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
print("Prepared Z2SE v32.85")
