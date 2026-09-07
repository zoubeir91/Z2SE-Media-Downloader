from __future__ import annotations


def apply_final(text: str) -> str:
    start = text.find('_IMPORT_HELP = {')
    end = text.find('\ndef show_import_list_help():', start)
    if start < 0 or end < 0:
        raise RuntimeError('v32.44 import help block missing')

    block = text[start:end]
    # The first patch intentionally stored escaped line separators in a raw
    # patch string. Convert only this help dictionary to normal Python \n
    # escapes so the popup renders real line breaks instead of literal "\\n".
    block = block.replace('\\\\n', '\\n')
    text = text[:start] + block + text[end:]

    if 'Le fichier .txt contient un lien par ligne.\\n\\nVidéo entière' not in text:
        raise RuntimeError('v32.44 import help newline normalization failed')
    if 'Le fichier .txt contient un lien par ligne.\\\\n' in text:
        raise RuntimeError('v32.44 literal import help newline still present')

    return text
