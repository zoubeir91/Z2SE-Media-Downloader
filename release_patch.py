from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.05"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:180], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.04"', 'APP_VERSION = "33.05"')

forja_helpers = r'''

def _extract_forja_token_target(body, response_url=""):
    """Return the signed HLS URL produced by token.forja.ma/prod."""
    values = []

    def collect(value):
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    text = str(body or "").strip()
    if text:
        try:
            collect(json.loads(text))
        except Exception:
            collect(text)
    collect(response_url)

    for raw in values:
        decoded = str(raw or "").strip().strip('"\'')
        decoded = decoded.replace("\\/", "/").replace("&amp;", "&")
        match = re.search(
            r"https?://[^\s\"'<>]+\.m3u8(?:\?[^\s\"'<>]*)?",
            decoded,
            flags=re.IGNORECASE,
        )
        if not match:
            continue
        target = match.group(0)
        parsed = urlsplit(target)
        clean_path = re.sub(r"/{2,}", "/", parsed.path)
        return urlunsplit(
            (parsed.scheme, parsed.netloc, clean_path, parsed.query, parsed.fragment)
        )
    return ""


def resolve_forja_token_proxy_url(value, referer=None, timeout=12):
    """Resolve Forja's token endpoint before handing the URL to FFmpeg."""
    value = str(value or "").strip()
    try:
        parsed = urlparse(value)
        if (parsed.hostname or "").lower() != "token.forja.ma":
            return ""
        if not parsed.path.rstrip("/").lower().endswith("/prod"):
            return ""
    except Exception:
        return ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }
    if referer:
        headers["Referer"] = str(referer)

    try:
        request = urllib.request.Request(value, headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_url = response.geturl()
            body = response.read().decode("utf-8", errors="replace")
        return _extract_forja_token_target(body, response_url)
    except Exception:
        return ""


def expand_forja_resolver_urls(urls, referer=None, job_label=""):
    """Replace Forja token wrappers with fresh signed HLS manifests."""
    expanded = []
    seen = set()
    prefix = f"[{job_label}] " if job_label else ""

    def add(value):
        value = normalize_sniffed_media_url(value)
        if value and value not in seen:
            seen.add(value)
            expanded.append(value)

    for value in urls or []:
        resolved = resolve_forja_token_proxy_url(value, referer=referer)
        if resolved:
            log(prefix + "✅ Forja token resolved to signed HLS stream.")
            add(resolved)
        else:
            add(value)
    return expanded
'''

replace_once(
    "\n\ndef is_direct_media_url(url):",
    forja_helpers + "\n\ndef is_direct_media_url(url):",
)

worker_insert = '''

            if str(host).lower().endswith("forja.ma"):
                resolver_urls = expand_forja_resolver_urls(
                    resolver_urls,
                    referer=page_url,
                    job_label=label,
                )

            resolver_media_candidates = list(media_candidates)
            resolver_media_candidates.extend(
                {"url": value}
                for value in resolver_urls
                if is_hls_manifest_url(value)
            )
'''

replace_once(
    '''            resolver_urls = (
                []
                if facebook_generic_unbound
                else _browser_media_candidate_urls(
                    normalized_media_url,
                    media_candidates,
                )
            )

            if facebook_generic_unbound:
                log(
''',
    '''            resolver_urls = (
                []
                if facebook_generic_unbound
                else _browser_media_candidate_urls(
                    normalized_media_url,
                    media_candidates,
                )
            )
''' + worker_insert + '''
            if facebook_generic_unbound:
                log(
''',
)

replace_once(
    '''                            media_candidates=media_candidates,
                            quality=quality,
                            referer=page_url,
                            expected_duration=page_duration,
''',
    '''                            media_candidates=resolver_media_candidates,
                            quality=quality,
                            referer=page_url,
                            expected_duration=page_duration,
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.05 resolves Forja token endpoints into fresh signed HLS streams and "
    "selects the complete episode instead of short stale preview manifests"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.05 app.py sha256", app_hash)
