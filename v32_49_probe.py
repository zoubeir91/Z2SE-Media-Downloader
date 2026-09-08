from pathlib import Path
import ast
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8-sig')
lines = text.splitlines()
print('APP_VERSION:', re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)', text).group(1))
print('LINES:', len(lines))

tree = ast.parse(text)
selected = {
    'on_window_close','really_quit_app','start_single','add_bulk_row','clear_bulk_editor_rows',
    'save_download_history','load_download_history','clear_download_list','clear_bulk','start_bulk',
    '_job_row_snapshot','_selected_download_items','pause_selected_downloads','resume_selected_downloads',
    'cancel_selected_downloads','startup_checks','schedule_download_history_save'
}
print('\nFUNCTIONS OF INTEREST')
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        low = node.name.lower()
        if any(k in low for k in ('row','download','queue','history','start','pause','resume','clear','playlist','close','quit')):
            print(f'{node.lineno:6d} {node.name}')

print('\nSELECTED FUNCTION SOURCES')
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in selected:
        print(f'\n### {node.name} lines {node.lineno}-{getattr(node,"end_lineno",node.lineno)}')
        print('\n'.join(lines[node.lineno-1:getattr(node,'end_lineno',node.lineno)]))

print('\nASSIGNMENTS OF INTEREST')
for i, line in enumerate(lines, 1):
    low = line.lower()
    if any(k in low for k in ('rows =', 'download_rows', 'active_download', 'history_file', 'root.protocol', 'wm_delete_window', 'mainloop','bulk_editor_rows')):
        print(f'{i:6d}: {line[:240]}')

print('\nGUI WINDOWS')
for center in (17870,17930,18240,18590,18640,23080):
    start=max(1, center-35); end=min(len(lines), center+70)
    print(f'\n### lines {start}-{end}')
    for i in range(start,end+1):
        print(f'{i:6d}: {lines[i-1]}')
