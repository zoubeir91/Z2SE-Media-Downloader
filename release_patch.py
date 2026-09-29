from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.06"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:180], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.05"', 'APP_VERSION = "33.06"')

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


def resolve_forja_episode_stream(page_url, timeout=15, job_label=""):
    """Resolve the episode selected by Forja's zero-based c2 query value."""
    prefix = f"[{job_label}] " if job_label else ""
    try:
        parsed_page = urlparse(str(page_url or ""))
        if not (parsed_page.hostname or "").lower().endswith("forja.ma"):
            return ""
        episode_index = int(parse_qs(parsed_page.query).get("c2", [""])[0])
        if episode_index < 0:
            return ""
    except Exception:
        return ""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        "Referer": str(page_url),
    }
    try:
        request = urllib.request.Request(str(page_url), headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            page_body = response.read().decode("utf-8", errors="replace")
        normalized_body = page_body.replace("\\u002F", "/").replace("\\/", "/")
        content_ids = []
        for content_id in re.findall(
            r"api\.forja\.ma/pages/proxy/content/(\d+)/stream_url",
            normalized_body,
            flags=re.IGNORECASE,
        ):
            if content_id not in content_ids:
                content_ids.append(content_id)
        if episode_index >= len(content_ids):
            return ""
        content_id = content_ids[episode_index]
        api_url = (
            "https://api.forja.ma/pages/proxy/content/"
            + content_id + "/stream_url?lang=ar"
        )
        api_headers = dict(headers)
        api_headers["Accept"] = "application/json,text/plain,*/*"
        api_headers["Origin"] = "https://forja.ma"
        request = urllib.request.Request(api_url, headers=api_headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_url = response.geturl()
            body = response.read().decode("utf-8", errors="replace")
        target = _extract_forja_token_target(body, response_url)
        if not target:
            return ""
        signed = resolve_forja_token_proxy_url(
            target, referer=page_url, timeout=timeout
        )
        final_url = signed or target
        log(
            prefix + "✅ Forja episode API resolved c2="
            + str(episode_index) + " to content " + content_id + "."
        )
        return final_url
    except Exception as exc:
        log(prefix + f"Forja episode API warning: {exc}")
        return ""
'''

replace_once(
    "\n\ndef is_direct_media_url(url):",
    forja_helpers + "\n\ndef is_direct_media_url(url):",
)

worker_insert = '''

            if str(host).lower().endswith("forja.ma"):
                forja_episode_url = resolve_forja_episode_stream(
                    page_url,
                    job_label=label,
                )
                resolver_urls = expand_forja_resolver_urls(
                    resolver_urls,
                    referer=page_url,
                    job_label=label,
                )
                resolver_urls = [
                    value for value in resolver_urls
                    if "/82294/" not in str(value)
                ]
                if forja_episode_url:
                    resolver_urls = [forja_episode_url] + [
                        value for value in resolver_urls
                        if value != forja_episode_url
                    ]

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
    "v33.06 resolves the exact Forja episode selected by c2 through its "
    "content API and rejects the known three-second preroll asset"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.06 app.py sha256", app_hash)
