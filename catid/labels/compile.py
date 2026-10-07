"""Compile raw per-visit labels (visit: idx,... label) into labels.json {det_id: label}.
Indices refer to the per-visit, time-ordered labeling sheets (ids.txt)."""
import sys, json, glob, collections
ids_file, out = sys.argv[1], sys.argv[2]
groups, cur = {}, None
for line in open(ids_file):
    line = line.strip()
    if line.startswith('#visit'): cur = int(line.split()[1]); groups[cur] = []
    elif line: groups[cur].append(line)
lab, dup = {}, []
for f in sorted(glob.glob(__import__('os').path.dirname(__file__) + '/raw_*.txt')):
    for line in open(f):
        line = line.strip()
        if not line or line.startswith('#'): continue
        v, rest = line.split(':', 1); idxs, name = rest.split()
        for i in idxs.split(','):
            did = groups[int(v)][int(i)]
            if did in lab: dup.append((v, i, lab[did], name))
            lab[did] = name
missing = [(v, i) for v, g in groups.items() for i, d in enumerate(g) if d not in lab]
print('labeled', len(lab), 'dups', dup[:10], 'missing', missing[:20], len(missing))
json.dump(lab, open(out, 'w'), indent=0, sort_keys=True)
c = collections.Counter(l.rstrip('~') for l in lab.values())
print(len(c) - 2, 'identities;', c.most_common())
