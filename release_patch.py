from pathlib import Path
import ast, hashlib, json, re, sys
TARGET_VERSION="32.82"
def sha256_file(path):
 d=hashlib.sha256()
 with open(path,"rb") as h:
  for c in iter(lambda:h.read(1048576),b""): d.update(c)
 return d.hexdigest()
version=str(sys.argv[1] if len(sys.argv)>1 else "").strip()
if version!=TARGET_VERSION: raise SystemExit(f"Expected {TARGET_VERSION}, got {version!r}")
app=Path("payload/app.py"); updater=Path("payload/z2se_updater.pyw"); manifest=Path("payload/update_manifest.json")
text=app.read_text(encoding="utf-8-sig")
text,n=re.subn(r'APP_VERSION\s*=\s*"32\.81"','APP_VERSION = "32.82"',text,count=1)
if n!=1: raise RuntimeError("APP_VERSION 32.81 not found")

# v32.81 proved the clipping is inside the PIL icon generator itself, not the Tk header.
# Keep header height unchanged. Replace only the navigation icon generator with a renderer
# that draws INSIDE a safe margin from the start, so no shape/glow can be cropped.
start=text.find('def _v3276_make_nav_icon(')
end=text.find('\ndef _v3272_draw_nav_icon',start)
if start<0 or end<0: raise RuntimeError("navigation icon generator not found")
new=r'''def _v3276_make_nav_icon(kind, active=False, size=32):
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageTk
        # Render at high resolution with a real outer margin, then antialias down.
        out_w, out_h = 46, 42
        S = 4
        W, H = out_w*S, out_h*S
        base = Image.new("RGBA", (W,H), (0,0,0,0))
        glow = Image.new("RGBA", (W,H), (0,0,0,0))
        g = ImageDraw.Draw(glow)
        d = ImageDraw.Draw(base)
        cyan=(25,199,255,255); light=(164,238,255,255); blue=(17,151,232,255)
        # Safe drawing box: x 7..39, y 5..37 in final pixels.
        def sc(v): return int(v*S)
        def line(draw, pts, fill, width=3): draw.line([(sc(x),sc(y)) for x,y in pts],fill=fill,width=sc(width),joint="curve")
        if kind=="file":
            # complete folder, safely inside bounds
            g.rounded_rectangle((sc(8),sc(13),sc(38),sc(34)),radius=sc(4),fill=(0,190,255,150))
            d.rounded_rectangle((sc(8),sc(13),sc(38),sc(34)),radius=sc(4),fill=(25,190,238,255),outline=light,width=sc(1))
            d.rounded_rectangle((sc(11),sc(9),sc(24),sc(16)),radius=sc(2),fill=(63,207,244,255))
        elif kind=="downloads":
            line(g,[(23,7),(23,27)],(0,220,255,180),4); line(g,[(15,20),(23,28),(31,20)],(0,220,255,180),4); line(g,[(12,33),(34,33)],(0,220,255,180),4)
            line(d,[(23,7),(23,27)],cyan,3); line(d,[(15,20),(23,28),(31,20)],cyan,3); line(d,[(12,33),(12,36),(34,36),(34,33)],blue,3)
        elif kind=="tools":
            line(g,[(12,10),(34,32)],(0,210,255,150),5); line(g,[(34,9),(13,32)],(0,210,255,150),5)
            line(d,[(12,10),(34,32)],light,4); line(d,[(34,9),(13,32)],blue,4)
            d.ellipse((sc(8),sc(6),sc(16),sc(14)),fill=light); d.ellipse((sc(30),sc(28),sc(38),sc(36)),fill=cyan)
        elif kind=="language":
            box=(sc(8),sc(5),sc(38),sc(35)); g.ellipse(box,outline=(0,220,255,180),width=sc(4)); d.ellipse(box,outline=light,width=sc(2))
            d.arc((sc(15),sc(5),sc(31),sc(35)),90,270,fill=cyan,width=sc(2)); d.arc((sc(15),sc(5),sc(31),sc(35)),270,90,fill=cyan,width=sc(2))
            line(d,[(9,20),(37,20)],cyan,2); d.arc((sc(9),sc(11),sc(37),sc(29)),180,360,fill=cyan,width=sc(2)); d.arc((sc(9),sc(11),sc(37),sc(29)),0,180,fill=cyan,width=sc(2))
        else:
            g.ellipse((sc(9),sc(5),sc(37),sc(35)),outline=(0,220,255,180),width=sc(4)); d.ellipse((sc(9),sc(5),sc(37),sc(35)),outline=light,width=sc(2))
            # question mark made from arcs/line, fully visible
            d.arc((sc(16),sc(10),sc(30),sc(23)),190,70,fill=cyan,width=sc(3)); line(d,[(23,22),(23,27)],cyan,3); d.ellipse((sc(21.5),sc(30),sc(24.5),sc(33)),fill=light)
        glow=glow.filter(ImageFilter.GaussianBlur(sc(2)))
        composed=Image.alpha_composite(glow,base)
        return ImageTk.PhotoImage(composed.resize((out_w,out_h),Image.Resampling.LANCZOS))
    except Exception:
        return None
'''
text=text[:start]+new+text[end:]

# Match Tk canvas to the renderer output. Header/menu height stays exactly v32.80/v32.81.
text=text.replace('width=54,\n        height=46,','width=54,\n        height=46,',1)
text=text.replace('canvas.create_image(27, 23, image=photo)','canvas.create_image(27, 23, image=photo)',1)

text=text.replace('Clean Editor v32.81:','Clean Editor v32.82:',1)
text=text.replace('Clean Editor v32.81 warning:','Clean Editor v32.82 warning:',1)
text=text.replace('Download details v32.81 warning:','Download details v32.82 warning:',1)
ast.parse(text); app.write_text(text,encoding="utf-8")
m=json.loads(manifest.read_text(encoding="utf-8")); m["version"]=TARGET_VERSION; m["created_by"]="GitHub Actions / v32.82 safe-margin antialiased navigation renderer; header height, empty-state, recovery and media play preserved"
m["files"]=[{"path":"app.py","sha256":sha256_file(app),"size":app.stat().st_size},{"path":"z2se_updater.pyw","sha256":sha256_file(updater),"size":updater.stat().st_size}]
manifest.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
print("Prepared Z2SE v32.82")
