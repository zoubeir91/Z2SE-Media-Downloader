from pathlib import Path
import ast
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8-sig')
lines = text.splitlines()
match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)', text)
print('APP_VERSION:', match.group(1) if match else 'unknown')
print('LINES:', len(lines))

tree = ast.parse(text)
selected = {
    'collect_bulk_jobs','manual_live_job_worker','_allocate_live_job_index','_restored_status',
    'bulk_worker','bulk_worker_item','set_bulk_item_status','set_bulk_row_status','set_job_status',
    'update_bulk_item','update_bulk_row','update_bulk_job_progress','manual_job_finished',
    'register_job_output_path','_register_job_output_path','_set_row_file_path',
    'start_bulk','clear_bulk','really_quit_app','load_download_history','save_download_history'
}
print('\nSELECTED FUNCTION SOURCES')
found = set()
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in selected:
        found.add(node.name)
        print(f'\n### {node.name} lines {node.lineno}-{getattr(node,"end_lineno",node.lineno)}')
        print('\n'.join(lines[node.lineno-1:getattr(node,'end_lineno',node.lineno)]))
print('\nNOT FOUND:', sorted(selected - found))

print('\nWORKER/CALLBACK FUNCTIONS')
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        low = node.name.lower()
        if any(k in low for k in ('worker','finished','complete','status','progress','allocate_live')):
            print(f'{node.lineno:6d} {node.name}')

print('\nGLOBALS 780-920')
for i in range(780, min(921, len(lines)+1)):
    print(f'{i:6d}: {lines[i-1]}')

print('\nBULK AREA 13040-13680')
for i in range(13040, min(13681, len(lines)+1)):
    print(f'{i:6d}: {lines[i-1]}')
