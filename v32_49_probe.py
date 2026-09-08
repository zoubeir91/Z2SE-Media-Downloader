from pathlib import Path
import ast
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8-sig')
print('APP_VERSION:', re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)', text).group(1))
print('LINES:', text.count('\n') + 1)
print('\nFUNCTIONS OF INTEREST')
tree = ast.parse(text)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        low = node.name.lower()
        if any(k in low for k in ('row','download','queue','history','start','pause','resume','clear','playlist','close','quit')):
            print(f'{node.lineno:6d} {node.name}')

print('\nASSIGNMENTS OF INTEREST')
for i, line in enumerate(text.splitlines(), 1):
    low = line.lower()
    if any(k in low for k in ('rows =', 'download_rows', 'active_download', 'history_file', 'root.protocol', 'wm_delete_window', 'mainloop')):
        print(f'{i:6d}: {line[:240]}')

print('\nGUI LABEL ANCHORS')
for needle in ['Start downloads','Start','Pause all','Resume all','Clear List','NEW DOWNLOADS','Check updates now']:
    matches = [i for i,line in enumerate(text.splitlines(),1) if needle.lower() in line.lower()]
    if matches:
        print(needle, matches[:20])
