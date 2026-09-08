from pathlib import Path

path = Path("release_patch.py")
text = path.read_text(encoding="utf-8")

old = '''# URL normalizer needs stable query parsing for duplicate identities.\nold_import = "from urllib.parse import urlparse, parse_qs, urlsplit, urlunsplit, urljoin"\nnew_import = "from urllib.parse import urlparse, parse_qs, parse_qsl, urlencode, urlsplit, urlunsplit, urljoin"\ntext = replace_once(text, old_import, new_import, "urllib.parse import")\n'''
new = '''# URL normalization uses the urllib helpers already present in v32.48.\n# Keep this incremental patch independent of the exact formatting of that import.\n'''
if old not in text:
    raise SystemExit("import-fix anchor missing")
text = text.replace(old, new, 1)

old_query = '''        clean_query = []\n        for key, value in parse_qsl(parts.query, keep_blank_values=True):\n            low = key.lower()\n            if (\n                low.startswith("utm_")\n                or low in _V3249_TRACKING_QUERY_KEYS\n                or low in _V3249_SECRET_QUERY_KEYS\n            ):\n                continue\n            clean_query.append((key, value))\n        clean_query.sort(key=lambda item: (item[0].lower(), item[1]))\n        path = re.sub(r"/{2,}", "/", parts.path or "/")\n        return urlunsplit(\n            (scheme, host, path, urlencode(clean_query, doseq=True), "")\n        )\n'''
new_query = '''        clean_query = []\n        for segment in str(parts.query or "").split("&"):\n            if not segment:\n                continue\n            key = segment.partition("=")[0].strip().lower()\n            if (\n                key.startswith("utm_")\n                or key in _V3249_TRACKING_QUERY_KEYS\n                or key in _V3249_SECRET_QUERY_KEYS\n            ):\n                continue\n            clean_query.append(segment)\n        clean_query.sort(key=str.lower)\n        path = re.sub(r"/{2,}", "/", parts.path or "/")\n        return urlunsplit(\n            (scheme, host, path, "&".join(clean_query), "")\n        )\n'''
if old_query not in text:
    raise SystemExit("query-fix anchor missing")
text = text.replace(old_query, new_query, 1)

path.write_text(text, encoding="utf-8", newline="\n")
print("release_patch.py compatibility fix applied")
