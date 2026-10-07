"""Zero-shot coat-pattern distribution per crop from CLIP image embeddings + text prompts.
Output coat.npy (N x K softmax probs). Coat is a stable, pose-invariant attribute that generic
embeddings mix with pose/background; used as a soft gate in the similarity."""
import sys, os, numpy as np, torch, open_clip
work = sys.argv[1]; tag = sys.argv[2] if len(sys.argv) > 2 else 'clip_b16__cropsm'
arch = {'clip_b16': ('ViT-B-16', 'openai'), 'clip_l14': ('ViT-L-14', 'openai')}[tag.split('__')[0]]
COATS = {
    'solid black': ['a solid black cat', 'a black cat with no white'],
    'tuxedo': ['a black and white tuxedo cat', 'a black cat with a white chest and white paws'],
    'black and white bicolor': ['a mostly white cat with black patches', 'a white cat with a black head'],
    'orange tabby': ['an orange tabby cat', 'a ginger cat'],
    'orange and white': ['an orange and white cat', 'a white cat with ginger patches'],
    'brown tabby': ['a brown tabby cat with stripes', 'a gray striped tabby cat'],
    'tabby and white': ['a tabby cat with a white chest and white paws'],
    'calico': ['a calico cat with white, orange and black patches'],
    'tortoiseshell': ['a tortoiseshell cat, mottled black and orange'],
    'dilute': ['a dilute calico or dilute tortie cat, gray and cream'],
    'colorpoint': ['a siamese cat', 'a lynx point siamese cat'],
    'white': ['a solid white cat'],
    'gray': ['a solid gray cat'],
}
model, _, _ = open_clip.create_model_and_transforms(*arch); tok = open_clip.get_tokenizer(arch[0])
with torch.no_grad():
    T = []
    for k, ps in COATS.items():
        t = model.encode_text(tok(ps)).float(); t = t / t.norm(dim=-1, keepdim=True); T.append(t.mean(0))
    T = torch.stack(T); T = T / T.norm(dim=-1, keepdim=True)
E = torch.tensor(np.load(f'{work}/emb/{tag}.npy'))
L = 100 * E @ T.T
L = L - L.mean(0, keepdim=True)  # prior correction: remove each prompt's average pull
P = torch.softmax(L, dim=-1).numpy()
np.save(f'{work}/coat.npy', P); json_names = list(COATS)
import json; json.dump(json_names, open(f'{work}/coat_names.json', 'w'))
print({k: int((P.argmax(1) == i).sum()) for i, k in enumerate(COATS)})
