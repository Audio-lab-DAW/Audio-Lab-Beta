"""Build the RF2 pick page and the ideas section of docs/research-features-new.md from ideas.json.
Usage: python3 build.py   (writes ideas-no-daw-has.html and ideas-section.md next to this file)"""
import json, pathlib
here = pathlib.Path(__file__).parent
data = json.loads((here / 'ideas.json').read_text())
tpl = (here / 'template.html').read_text()
(here / 'ideas-no-daw-has.html').write_text(tpl.replace('/*IDEAS*/null', json.dumps(data, ensure_ascii=False)))
out = []
for g in data['groups']:
    out.append(f"### {g['k']}. {g['n']}\n\n{g['d']}\n")
    for i in [i for i in data['ideas'] if i['g'] == g['k']]:
        flags = (' ★' if i['star'] else '') + (' (live mock-up)' if i['mock'] else '')
        out.append(f"#### {i['id']}. {i['t']}{flags}\n")
        for k, n in [('sees', 'What you see'), ('why', 'Why it is more intuitive'), ('prior', 'Prior art'), ('risks', 'Risks'), ('effort', 'Effort'), ('native', 'Native engine')]:
            out.append(f"- **{n}:** {i[k]}")
        out.append('')
(here / 'ideas-section.md').write_text('\n'.join(out))
print(len(data['ideas']), 'ideas;', sum(i['star'] for i in data['ideas']), 'starred;', sum(i['mock'] for i in data['ideas']), 'mock-ups')
