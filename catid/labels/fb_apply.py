"""Apply review-page feedback to the labels -> labels_v3.json (reproducible).
group_fb (cat__vN: same yes/no/unsure): yes -> link confirmed ('~' removed); no/unsure -> dropped ('?').
pair_fb (cropA__cropB: same yes/no): yes -> crop A takes crop B's label; no -> labels kept.
RENAMES: identities the user named or merged."""
import json, glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); import common
RENAMES = {'BlackBlue': 'Onyx', 'SmokeKit': 'Onyx', 'OrangeYellow': 'Shovel'}   # user, Oct 7
# User-given real names (review page, cat_fb). The same name on two groups merges them.
NAMES = json.load(open(f'{HERE}/feedback/cat_names.json'))
# Groups the user flagged as several cats, split by hand (Oct 7): CalicoKitYellow = 3 cats.
SPLITS = {
    'CalicoKitYellow': {'PXL_20261006_2313': 'CalicoTabbyKitPink', 'PXL_20261006_2314': 'CalicoTabbyKitPink',
                        'PXL_20261007_011159213': 'CalicoTabbyWin'},  # prefix -> new label; rest stays (yellow-collar calico kitten)
}
lab = json.load(open(f'{HERE}/labels_v2.json'))
dets = json.load(open(os.environ.get('WORK', '/home/user/data/work') + '/dets.json'))
sess = dict(zip([d['id'] for d in dets], common.sessions([d['file'] for d in dets])))
base = lambda l: l.rstrip('~')
stats = {'confirmed': 0, 'dropped': 0, 'pair_relabel': 0}
for p in glob.glob(f'{HERE}/feedback/group_fb/*.json'):
    k = os.path.basename(p)[:-5]; cat, v = k.rsplit('__v', 1); ans = json.load(open(p)).get('same')
    for did, l in lab.items():
        if l.endswith('~') and base(l) == cat and sess[did] == int(v):
            if ans == 'yes': lab[did] = cat; stats['confirmed'] += 1
            else: lab[did] = '?'; stats['dropped'] += 1
for p in glob.glob(f'{HERE}/feedback/pair_fb/*.json'):
    a, b = os.path.basename(p)[:-5].split('__'); d = json.load(open(p))
    if d.get('same') == 'yes': lab[a] = base(lab[b]); stats['pair_relabel'] += 1
for did, l in lab.items():
    for cat, rules in SPLITS.items():
        if base(l) == cat:
            for pre, new in rules.items():
                if did.startswith(pre): lab[did] = new
for did, l in lab.items():
    b = base(l); b = RENAMES.get(b, b)
    if l not in ('?', 'x'): lab[did] = NAMES.get(b, b) + ('~' if l.endswith('~') else '')
json.dump(lab, open(f'{HERE}/labels_v4.json', 'w'), indent=0, sort_keys=True)
import collections
c = collections.Counter(base(l) for l in lab.values())
print(stats, '| identities', len(c) - 2, '| labeled', sum(v for k, v in c.items() if k not in '?x'), '| still uncertain', sum(l.endswith('~') for l in lab.values()))
