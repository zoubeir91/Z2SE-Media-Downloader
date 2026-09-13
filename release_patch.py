from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.76"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

version = str(sys.argv[1] if len(sys.argv) > 1 else "").strip()
if version != TARGET_VERSION:
    raise SystemExit(f"This patch prepares only v{TARGET_VERSION}; got {version!r}")

app_path = Path("payload/app.py")
updater_path = Path("payload/z2se_updater.pyw")
manifest_path = Path("payload/update_manifest.json")
for required in (app_path, updater_path, manifest_path):
    if not required.is_file():
        raise FileNotFoundError(required)

text = app_path.read_text(encoding="utf-8-sig")
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.75"', 'APP_VERSION = "32.76"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.75 -> 32.76")

# Replace direct Canvas rendering with supersampled Pillow icons. The icon is
# drawn at 4x and downsampled with LANCZOS, producing smooth edges on Windows.
icon_pattern = re.compile(r'def _v3272_draw_nav_icon\(canvas, kind, color\):\n.*?(?=\n\ndef _make_top_menu_button)', re.S)
icon_replacement = r'''_v3276_nav_images = []

def _v3276_make_nav_icon(kind, active=False, size=64):
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageTk
        S = 4
        W = H = size * S
        cyan = (13, 205, 255, 255)
        pale = (184, 232, 255, 255)
        blue = (19, 151, 239, 255)
        transparent = (0, 0, 0, 0)
        glow_layer = Image.new("RGBA", (W, H), transparent)
        gd = ImageDraw.Draw(glow_layer)
        main = Image.new("RGBA", (W, H), transparent)
        d = ImageDraw.Draw(main)
        def L(points, fill, width, joint="curve"):
            pts = [(int(x*S), int(y*S)) for x,y in points]
            d.line(pts, fill=fill, width=int(width*S), joint=joint)
        def GL(points, width=8):
            pts = [(int(x*S), int(y*S)) for x,y in points]
            gd.line(pts, fill=(0, 194, 255, 175), width=int(width*S), joint="curve")
        if kind == "file":
            # glossy cyan folder
            gd.rounded_rectangle((7*S,22*S,57*S,50*S), radius=7*S, fill=(0,190,255,130))
            d.rounded_rectangle((8*S,22*S,56*S,50*S), radius=6*S, fill=(18,169,231,255), outline=pale, width=1*S)
            d.polygon([(9*S,24*S),(20*S,24*S),(24*S,18*S),(39*S,18*S),(43*S,23*S),(55*S,23*S)], fill=(98,219,255,255))
            d.rounded_rectangle((9*S,27*S,55*S,49*S), radius=5*S, fill=(28,188,245,255))
        elif kind == "downloads":
            GL([(32,9),(32,39)], 9); GL([(20,29),(32,41),(44,29)], 9); GL([(14,47),(14,54),(50,54),(50,47)], 9)
            L([(32,9),(32,39)], cyan, 5); L([(20,29),(32,41),(44,29)], cyan, 5); L([(14,47),(14,54),(50,54),(50,47)], cyan, 5)
        elif kind == "tools":
            GL([(15,14),(49,49)], 9); GL([(49,14),(15,49)], 8)
            L([(15,14),(49,49)], pale, 7); L([(49,14),(15,49)], blue, 7)
            d.ellipse((8*S,8*S,23*S,23*S), outline=pale, width=4*S)
            d.ellipse((42*S,42*S,55*S,55*S), outline=(123,217,255,255), width=4*S)
        elif kind == "language":
            gd.ellipse((7*S,7*S,57*S,57*S), outline=(0,190,255,170), width=7*S)
            d.ellipse((8*S,8*S,56*S,56*S), outline=pale, width=3*S)
            d.ellipse((20*S,8*S,44*S,56*S), outline=(139,220,255,255), width=3*S)
            d.line((9*S,32*S,55*S,32*S), fill=(139,220,255,255), width=3*S)
            d.arc((9*S,17*S,55*S,47*S), 0, 180, fill=(139,220,255,255), width=2*S)
            d.arc((9*S,17*S,55*S,47*S), 180, 360, fill=(139,220,255,255), width=2*S)
        else:
            gd.ellipse((8*S,7*S,56*S,55*S), outline=(0,201,255,180), width=7*S)
            d.ellipse((9*S,8*S,55*S,54*S), outline=cyan if active else (78,194,238,255), width=4*S)
            d.arc((20*S,15*S,44*S,39*S), 205, 520, fill=pale, width=4*S)
            d.line((32*S,36*S,32*S,41*S), fill=pale, width=4*S)
            d.ellipse((30*S,46*S,34*S,50*S), fill=pale)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(4*S))
        composed = Image.alpha_composite(glow_layer, main)
        composed = composed.resize((size, size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(composed)
    except Exception:
        return None


def _v3272_draw_nav_icon(canvas, kind, color):
    active = str(color).lower() in ("#12cfff", "#13cfff", "#08c9ff")
    photo = _v3276_make_nav_icon(kind, active=active, size=64)
    if photo is not None:
        _v3276_nav_images.append(photo)
        canvas.create_image(32, 32, image=photo)
        return
    # safe fallback if Pillow is unavailable
    canvas.create_text(32, 30, text={"file":"▰","downloads":"↓","tools":"✦","language":"◎","help":"?"}.get(kind,"?"), fill=color, font=("Segoe UI", 26, "bold"))
'''
text, count = icon_pattern.subn(lambda m: icon_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not replace navigation renderer")

# Reference-like active tile: deeper navy, cyan border, larger icon area and spacing.
text = text.replace('tile_bg = "#0a3150" if active else UI_TOP', 'tile_bg = "#07304c" if active else UI_TOP', 1)
text = text.replace('cursor="hand2", padx=16, pady=5,', 'cursor="hand2", padx=18, pady=5,', 1)
text = text.replace('highlightbackground=("#08bdf8" if active else UI_TOP),', 'highlightbackground=("#08cfff" if active else UI_TOP),', 1)
text = text.replace('tile.pack(side="left", padx=7, pady=4, fill="y")', 'tile.pack(side="left", padx=10, pady=4, fill="y")', 1)
text = text.replace('width=62, height=58', 'width=64, height=64', 1)
text = text.replace('font=("Segoe UI Semibold", 11)', 'font=("Segoe UI", 11)', 1)
text = text.replace('height=4, bg="#08c9ff"', 'height=5, bg="#08d8ff"', 1)
text = text.replace('height=118,', 'height=126,', 1)

# Keep preview functional and make the instruction compact/visible.
text = text.replace('Clean Editor v32.75: startup draft/PART rows cleared.', 'Clean Editor v32.76: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.75 warning:', 'Clean Editor v32.76 warning:', 1)
text = text.replace('Download details v32.75 warning:', 'Download details v32.76 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.76 antialiased Pillow navigation matching approved reference"
manifest["files"] = [
    {"path":"app.py","sha256":sha256_file(app_path),"size":app_path.stat().st_size},
    {"path":"z2se_updater.pyw","sha256":sha256_file(updater_path),"size":updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
print("Prepared Z2SE v32.76 antialiased premium navigation")
