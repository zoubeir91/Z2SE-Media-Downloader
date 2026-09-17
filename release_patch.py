from pathlib import Path
import ast, hashlib, json, re, sys
TARGET_VERSION="32.84"
def sha256_file(path):
 d=hashlib.sha256()
 with open(path,"rb") as h:
  for c in iter(lambda:h.read(1048576),b""): d.update(c)
 return d.hexdigest()
version=str(sys.argv[1] if len(sys.argv)>1 else "").strip()
if version!=TARGET_VERSION: raise SystemExit(f"Expected {TARGET_VERSION}, got {version!r}")
app=Path("payload/app.py"); updater=Path("payload/z2se_updater.pyw"); manifest=Path("payload/update_manifest.json")
text=app.read_text(encoding="utf-8-sig")
text,n=re.subn(r'APP_VERSION\s*=\s*"32\.83"','APP_VERSION = "32.84"',text,count=1)
if n!=1: raise RuntimeError("APP_VERSION 32.83 not found")

# NAVIGATION: keep compact header, but make icon+label a correctly centered block.
# The previous releases enlarged the transparent bitmap, not the artwork. Here we
# replace the renderer itself with larger artwork (36-38 px) inside a fixed safe box.
start=text.find('def _v3276_make_nav_icon('); end=text.find('\ndef _v3272_draw_nav_icon',start)
if start<0 or end<0: raise RuntimeError("nav renderer not found")
renderer=r'''def _v3276_make_nav_icon(kind, active=False, size=38):
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageTk
        S=4; OW,OH=52,44; W,H=OW*S,OH*S
        base=Image.new("RGBA",(W,H),(0,0,0,0)); glow=Image.new("RGBA",(W,H),(0,0,0,0))
        d=ImageDraw.Draw(base); g=ImageDraw.Draw(glow)
        cyan=(22,205,255,255); light=(170,241,255,255); blue=(20,155,232,255)
        def sc(v): return int(v*S)
        def ln(dr,pts,fill,width=3): dr.line([(sc(x),sc(y)) for x,y in pts],fill=fill,width=sc(width),joint="curve")
        if kind=="file":
            g.rounded_rectangle((sc(7),sc(11),sc(45),sc(38)),radius=sc(5),fill=(0,205,255,155))
            d.rounded_rectangle((sc(7),sc(11),sc(45),sc(38)),radius=sc(5),fill=(28,190,235,255),outline=light,width=sc(1))
            d.rounded_rectangle((sc(11),sc(6),sc(27),sc(15)),radius=sc(2),fill=(69,214,248,255))
        elif kind=="downloads":
            ln(g,[(26,4),(26,27)],(0,220,255,180),5); ln(g,[(15,19),(26,30),(37,19)],(0,220,255,180),5); ln(g,[(11,36),(41,36)],(0,220,255,180),5)
            ln(d,[(26,4),(26,27)],cyan,4); ln(d,[(15,19),(26,30),(37,19)],cyan,4); ln(d,[(11,34),(11,39),(41,39),(41,34)],blue,3)
        elif kind=="tools":
            ln(g,[(10,7),(41,36)],(0,210,255,155),6); ln(g,[(41,7),(11,36)],(0,210,255,155),6)
            ln(d,[(10,7),(41,36)],light,4); ln(d,[(41,7),(11,36)],blue,4)
            d.ellipse((sc(6),sc(3),sc(15),sc(12)),fill=light); d.ellipse((sc(37),sc(32),sc(46),sc(41)),fill=cyan)
        elif kind=="language":
            box=(sc(7),sc(3),sc(45),sc(41)); g.ellipse(box,outline=(0,220,255,175),width=sc(5)); d.ellipse(box,outline=light,width=sc(2))
            d.ellipse((sc(16),sc(3),sc(36),sc(41)),outline=cyan,width=sc(2)); ln(d,[(8,22),(44,22)],cyan,2)
            d.arc((sc(8),sc(9),sc(44),sc(35)),180,360,fill=cyan,width=sc(2)); d.arc((sc(8),sc(9),sc(44),sc(35)),0,180,fill=cyan,width=sc(2))
        else:
            g.ellipse((sc(8),sc(3),sc(44),sc(41)),outline=(0,220,255,175),width=sc(5)); d.ellipse((sc(8),sc(3),sc(44),sc(41)),outline=light,width=sc(2))
            d.arc((sc(16),sc(8),sc(35),sc(27)),190,70,fill=cyan,width=sc(4)); ln(d,[(26,25),(26,31)],cyan,3); d.ellipse((sc(24),sc(35),sc(28),sc(39)),fill=light)
        glow=glow.filter(ImageFilter.GaussianBlur(sc(1.8)))
        img=Image.alpha_composite(glow,base).resize((OW,OH),Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None
'''
text=text[:start]+renderer+text[end:]
# Fixed canvas with full icon; no header-height change.
text=text.replace('width=58,\n        height=50,','width=56,\n        height=45,',1)
text=text.replace('canvas.create_image(29, 25, image=photo)','canvas.create_image(28, 22, image=photo)',1)
# Move labels immediately under icons and keep full text visible.
nav=text.find('def _make_top_menu_button')
if nav>=0:
 e=text.find('\n\ndef ',nav+10)
 if e<0: e=min(len(text),nav+8000)
 seg=text[nav:e]
 seg=seg.replace('pady=(1, 0)','pady=(0, 0)')
 seg=seg.replace('pady=(0, 1)','pady=(0, 0)')
 seg=seg.replace('pady=(0, 0)','pady=0')
 text=text[:nav]+seg+text[e:]

# RECOVERY V2: preserve existing recovery engine, but classify modern YouTube failures
# before retrying. This avoids blind repeated retries and gives the existing machinery
# distinct signals for SABR, PO-token, auth/cookies and CDN 403 failures.
mp=text.rfind('root.mainloop()')
if mp<0: raise RuntimeError("mainloop not found")
recovery=r'''
# v32.84 YouTube Diagnostic / Recovery Engine v2 helpers.
def _v3284_youtube_failure_class(message):
    s=str(message or "").lower()
    if "sabr" in s or "only images are available" in s or "missing url" in s:
        return "SABR_ONLY"
    if "po token" in s or "pot token" in s or "proof of origin" in s:
        return "PO_TOKEN"
    if "login_required" in s or "sign in to confirm" in s or "not a bot" in s or "cookies" in s:
        return "AUTH_SESSION"
    if "googlevideo" in s and ("403" in s or "forbidden" in s):
        return "GOOGLEVIDEO_403"
    if "http error 403" in s or "403 forbidden" in s:
        return "HTTP_403"
    if "javascript" in s and ("challenge" in s or "runtime" in s):
        return "JS_CHALLENGE"
    return "GENERIC"

def _v3284_recovery_hint(message):
    kind=_v3284_youtube_failure_class(message)
    return {
        "SABR_ONLY":"refresh clients/formats before accepting low-quality fallback",
        "PO_TOKEN":"refresh PO-token/provider path",
        "AUTH_SESSION":"refresh authenticated session/cookies separately from PO token",
        "GOOGLEVIDEO_403":"refresh media URL/session before another CDN attempt",
        "HTTP_403":"avoid blind retry; refresh extraction/session first",
        "JS_CHALLENGE":"ensure supported JS runtime/challenge solver path",
    }.get(kind,"standard recovery")

'''
text=text[:mp]+recovery+text[mp:]
# Existing v32.79 recovery keywords are retained; add JS/SABR variants only if absent.
p=text.find('"sabr"')
if p>=0:
 close=text.find(')',p)
 if close>p and close-p<2200:
  seg=text[p:close]
  extras=[]
  for x in ('"sabr-only"','"javascript challenge"','"proof of origin"','"missing url"'):
   if x not in seg: extras.append(x)
  if extras: text=text[:close]+', '+', '.join(extras)+text[close:]

text=text.replace('Clean Editor v32.83:','Clean Editor v32.84:',1)
text=text.replace('Clean Editor v32.83 warning:','Clean Editor v32.84 warning:',1)
text=text.replace('Download details v32.83 warning:','Download details v32.84 warning:',1)
ast.parse(text); app.write_text(text,encoding="utf-8")
m=json.loads(manifest.read_text(encoding="utf-8")); m["version"]=TARGET_VERSION; m["created_by"]="GitHub Actions / v32.84 larger balanced nav artwork + tight labels + YouTube Diagnostic Recovery v2 helpers; existing downloader preserved"
m["files"]=[{"path":"app.py","sha256":sha256_file(app),"size":app.stat().st_size},{"path":"z2se_updater.pyw","sha256":sha256_file(updater),"size":updater.stat().st_size}]
manifest.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
print("Prepared Z2SE v32.84")
