"""Apply review-page feedback to the labels -> labels_v5.json (reproducible; inputs in labels/feedback/).
group_fb  (cat__vN: same yes/no/unsure): yes -> link confirmed; no/unsure -> crop dropped ('?').
pair_fb   (cropA__cropB: same yes/no): yes -> crop A takes crop B's label.
crop_fb   split letters (A-D) set in 'Split into cats' mode + cat_fb note 'A = Name; B = Name' -> crop relabeled.
cat_fb    name -> identity renamed; the same name on several groups merges them.
CUTOFF    cats whose last sighting is on/before this date are removed (user, Oct 7: 'cut cats last seen Jul 7 or earlier')."""
import json, glob, os, sys, re, collections, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); import common
FB = f'{HERE}/feedback'
CUTOFF = dt.date(2026, 7, 7)
RENAMES = {'BlackBlue': 'Onyx', 'SmokeKit': 'Onyx', 'OrangeYellow': 'Shovel'}   # user, Oct 7 (chat)
CHAT_NAMES = {'CalicoTabbyKitPink': 'Smoothie'}   # user, Oct 7 (chat): the 4:13 pm pink-collar kitten is Smoothie, not Callie
SPLITS = {'CalicoKitYellow': {'PXL_20261006_2313': 'CalicoTabbyKitPink', 'PXL_20261006_2314': 'CalicoTabbyKitPink',
                              'PXL_20261007_011159213': 'CalicoTabbyWin'}}   # my split of the group the user flagged (chat)
lab = json.load(open(f'{HERE}/labels_v2.json'))
dets = json.load(open(os.environ.get('WORK', '/home/user/data/work') + '/dets.json'))
files = {d['id']: d['file'] for d in dets}
sess = dict(zip([d['id'] for d in dets], common.sessions([d['file'] for d in dets])))
base = lambda l: l.rstrip('~')
load_dir = lambda d: {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob(f'{FB}/{d}/*.json')}
st = collections.Counter()
# 1. cross-visit link answers
for k, d in load_dir('group_fb').items():
    cat, v = k.rsplit('__v', 1)
    for did, l in lab.items():
        if l.endswith('~') and base(l) == cat and sess[did] == int(v):
            lab[did] = cat if d.get('same') == 'yes' else '?'; st['link_' + ('ok' if d.get('same') == 'yes' else 'drop')] += 1
# 2. same-cat pairs
for k, d in load_dir('pair_fb').items():
    a, b = k.split('__')
    if d.get('same') == 'yes': lab[a] = base(lab[b]); st['pair_relabel'] += 1
# 3. my hand split
for did, l in lab.items():
    for pre, new in SPLITS.get(base(l), {}).items():
        if did.startswith(pre): lab[did] = new
# 4. user's split letters + 'A = Name' notes
cat_fb = load_dir('cat_fb')
letters = {}
for k, d in cat_fb.items():
    for L, name in re.findall(r'\b([A-D])\s*=\s*([^;,\n]+)', d.get('note', '')): letters[(k, L)] = name.strip()
for did, d in load_dir('crop_fb').items():
    L = d.get('split'); cat = d.get('cat')
    if L and (cat, L) in letters: lab[did] = letters[(cat, L)]; st['split_relabel'] += 1
    elif L: lab[did] = f'{cat}_{L}'; st['split_unnamed'] += 1
# 5. names (cat_fb name field) + chat renames; same name merges
names = {k: d['name'].strip() for k, d in cat_fb.items() if d.get('name', '').strip()}
names.update(CHAT_NAMES)
for did, l in lab.items():
    if l in ('?', 'x'): continue
    b = RENAMES.get(base(l), base(l)); b = names.get(b, b)
    lab[did] = b + ('~' if l.endswith('~') else '')
# 6. cut cats last seen on/before CUTOFF
last = collections.defaultdict(lambda: dt.date.min)
for did, l in lab.items():
    if l not in ('?', 'x'): last[base(l)] = max(last[base(l)], common.local(files[did]).date())
cut = sorted(c for c, d in last.items() if d <= CUTOFF)
for did, l in lab.items():
    if base(l) in cut: lab[did] = '?'
json.dump(lab, open(f'{HERE}/labels_v5.json', 'w'), indent=0, sort_keys=True)
c = collections.Counter(base(l) for l in lab.values() if l not in ('?', 'x'))
print(dict(st), '| cut (last seen <= Jul 7):', cut)
print(len(c), 'cats,', sum(c.values()), 'crops:', c.most_common())
