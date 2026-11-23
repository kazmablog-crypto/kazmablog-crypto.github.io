"""Writes computed results into lov/index.html.

usage: embed.py <work/out with S.npy W.npy> <data/out> <index.html>
Replaces the inline data blocks CZ, POP, WORST and PLACES and the rows and
totals of the labour table. Everything else in the page is left as it is.
"""
import sys, json, math, re
import numpy as np
from scipy.spatial import cKDTree

WORK, OUT, PAGE = sys.argv[1:4]
K = math.cos(math.radians(49.8))
S = np.load(WORK + '/S.npy'); W = np.load(WORK + '/W.npy')
place = json.load(open(OUT + '/place.json'))
area = json.load(open(OUT + '/places_area.json'))
towns = json.load(open(OUT + '/towns.json'))
labor = json.load(open(OUT + '/labor.json'))
border = json.load(open(OUT + '/border.json'))

# farthest inhabited cell from any cache, per mode and count
worst = {'area': {}, 'pop': {}}
for mode, src in (('area', area), ('pop', place['pop'])):
    for n in ('77', '206', '300', '1200'):
        C = np.array(src[n], float); d, i = cKDTree(C).query(S)
        j = int(np.argmax(np.where(W > 0, d, -1)))
        worst[mode][n] = [round(float(S[j, 0]), 1), round(float(S[j, 1]), 1),
                          round(float(C[i[j], 0]), 1), round(float(C[i[j], 1]), 1), round(float(d[j]), 1)]

s = open(PAGE, encoding='utf-8').read()
def sub(pattern, value):
    global s
    s, n = re.subn(pattern, lambda m: value, s, count=1, flags=re.S)
    if n != 1: sys.exit('pattern not found: ' + pattern)
js = lambda o: json.dumps(o, separators=(',', ':'), ensure_ascii=False)
lonlat = [[round(x / (111.32 * K) + 12, 4), round(51.1 - y / 110.57, 4)] for x, y in border]
sub(r'var CZ=\[.*?\];', 'var CZ=' + js(lonlat) + ';')
sub(r'var POP=\{.*?\};\n', 'var POP=' + js({'pop': place['pop'], 'stats': place['stats'], 'towns': towns}) + ';\n')
sub(r'var WORST=\{.*?\};\n', 'var WORST=' + js(worst) + ';\n')
sub(r'var PLACES=\{.*?\};\n', 'var PLACES=' + js(area) + ';\n')

cz = lambda x, d=0: f'{x:,.{d}f}'.replace(',', ' ').replace('.', ',')
dur = lambda h: cz(h, 1) + ' h' if h < 10 else cz(h) + ' h · ' + cz(h / 8, 1) + ' prac. dní'
names = {1: '1 člověk', 5: '5 lidí', 10: '10 lidí', 25: '25 lidí', 50: '50 lidí', 100: '100 lidí',
         300: '300 místních pomocníků', 600: '600 místních pomocníků'}
rows = ''.join('<tr{}><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>\n'.format(
    ' class="hl"' if r['k'] in (50, 300) else '', names.get(r['k'], f"{r['k']} lidí"),
    cz(r['per_person']) if r['per_person'] >= 10 else cz(r['per_person'], 1), dur(r['max_h']), dur(r['avg_h'])) for r in labor)
a = s.index('<tbody>', s.index('<section class="labor"')) + 7; b = s.index('</tbody>', a)
s = s[:a] + '\n' + rows + '      ' + s[b:]
tot, km = labor[0]['total_h'], labor[0]['km']
sub(r'<b>[\d  ]+ hodin</b><span>práce celkem, zhruba [\d  ]+ pracovních dnů jednoho člověka</span>',
    f'<b>{cz(tot)} hodin</b><span>práce celkem, zhruba {cz(tot / 8)} pracovních dnů jednoho člověka</span>')
sub(r'<b>[\d  ]+ km</b><span>najetých', f'<b>{cz(km)} km</b><span>najetých')
open(PAGE, 'w', encoding='utf-8').write(s)
print('index.html updated')
