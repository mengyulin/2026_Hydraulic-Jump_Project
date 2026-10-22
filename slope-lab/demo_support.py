"""Small display helpers for P0 walkthroughs; numerical solvers are unchanged."""
import csv
import html
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def show_table(rows):
    """Notebook display; floats remain full precision in saved CSV/JSON."""
    from IPython.display import HTML, display
    if not rows:
        print('沒有可顯示的資料。')
        return
    def cell(v):
        if v is None: return 'N/A'
        return f'{v:.8g}' if isinstance(v, float) else str(v)
    head = list(rows[0])
    body = '<table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in head)+'</tr></thead><tbody>'
    for row in rows:
        body += '<tr>'+''.join('<td>'+html.escape(cell(row.get(k)))+'</td>' for k in head)+'</tr>'
    display(HTML(body+'</tbody></table>'))


def save_rows(path, rows):
    if not rows: return
    with Path(path).open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def result_rows(run_paths):
    rows=[]
    for label, folder in run_paths.items():
        folder=Path(folder);s=read_json(folder/'summary.json');m=read_json(folder/'metadata.json')
        # Report the actual SS jump, not the fine SS reference stored on every run.
        jump=s['checks']['jump']['x_m'] if m['method']=='ss' else None
        rows.append(dict(method=label,SS_xJ_m=jump,x50_unique_m=s['x50_unique_m'],
            upstream_h_m=s['upstream_mean_h_m'],downstream_h_m=s['downstream_mean_h_m'],
            peak_h_m=s['first_peak_h_m'],peak_x_m=s['first_peak_x_m'],
            tail_wavelength_m=s['tail_wavelength_m'],tail_efold_m=s['tail_amplitude_efold_m'],
            integrity=m['status'],steady_screen=m['steady_screen']))
    return rows
