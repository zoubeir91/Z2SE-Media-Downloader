from pathlib import Path
import ast, hashlib, json, re, sys
TARGET_VERSION="32.81"
def sha256_file(path):
 d=hashlib.sha256()
 with open(path,"rb") as h:
  for c in iter(lambda:h.read(1048576),b""): d.update(c)
 return d.hexdigest()
version=str(sys.argv[1] if len(sys.argv)>1 else "").strip()
if version!=TARGET_VERSION: raise SystemExit(f"Expected {TARGET_VERSION}, got {version!r}")
app=Path("payload/app.py"); updater=Path("payload/z2se_updater.pyw"); manifest=Path("payload/update_manifest.json")
text=app.read_text(encoding="utf-8-sig")
text,n=re.subn(r'APP_VERSION\s*=\s*"32\.80"','APP_VERSION = "32.81"',text,count=1)
if n!=1: raise RuntimeError("APP_VERSION 32.80 not found")

# Keep v32.80 header/menu height exactly as requested. Only fix clipping of the icons.
# Artwork stays 32px, but gets a generous transparent canvas so glow/strokes are never cut.
text=text.replace('width=38,\n        height=38,','width=54,\n        height=46,',1)
text=text.replace('canvas.create_image(19, 19, image=photo)','canvas.create_image(27, 23, image=photo)',1)

# PIL-generated image itself is 32px; add transparent breathing room around it before
# converting to PhotoImage. This preserves the small visual icon while retaining glow.
needle='return ImageTk.PhotoImage(img)'
if needle in text:
 text=text.replace(needle,
'''# v32.81: pad the small icon so antialiased glow and outer strokes stay visible.\n        try:\n            padded = Image.new("RGBA", (46, 42), (0, 0, 0, 0))\n            px = (46 - img.width) // 2\n            py = (42 - img.height) // 2\n            padded.alpha_composite(img, (px, py))\n            img = padded\n        except Exception:\n            pass\n        return ImageTk.PhotoImage(img)''',1)

text=text.replace('Clean Editor v32.80:','Clean Editor v32.81:',1)
text=text.replace('Clean Editor v32.80 warning:','Clean Editor v32.81 warning:',1)
text=text.replace('Download details v32.80 warning:','Download details v32.81 warning:',1)
ast.parse(text); app.write_text(text,encoding="utf-8")
m=json.loads(manifest.read_text(encoding="utf-8")); m["version"]=TARGET_VERSION; m["created_by"]="GitHub Actions / v32.81 unclipped centered premium nav icons; v32.80 header height and empty-state fix preserved"
m["files"]=[{"path":"app.py","sha256":sha256_file(app),"size":app.stat().st_size},{"path":"z2se_updater.pyw","sha256":sha256_file(updater),"size":updater.stat().st_size}]
manifest.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
print("Prepared Z2SE v32.81")
