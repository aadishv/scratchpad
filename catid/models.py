"""Embedding model registry. Each loader returns (model_fn, input_size, mean, std):
model_fn(float tensor Bx3xSxS normalized) -> Bx D features (unnormalized)."""
import torch, timm, open_clip
from torch import nn

IMNET = ((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
CLIPN = ((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
HALF = ((0.5,) * 3, (0.5,) * 3)

def _timm(name, size, norm=IMNET, **kw):
    m = timm.create_model(name, pretrained=True, num_classes=0, **kw).eval()
    return m, size, *norm

def _clip(arch, tag, size, norm):
    m, _, _ = open_clip.create_model_and_transforms(arch, pretrained=tag)
    m = m.eval()
    return m.encode_image, size, *norm

class GeM(nn.Module):
    def __init__(self, p=3, eps=1e-6):
        super().__init__(); self.p = nn.Parameter(torch.ones(1) * p); self.eps = eps
    def forward(self, x):
        return nn.functional.avg_pool2d(x.clamp(min=self.eps).pow(self.p), (x.size(-2), x.size(-1))).pow(1. / self.p).flatten(1)

def _miewid():
    """MiewID-msv3 (multi-species re-ID, EfficientNetV2-M + GeM + BN). Its HF remote code breaks on
    current transformers, so rebuild it from timm and load the safetensors directly."""
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file
    bb = timm.create_model('efficientnetv2_rw_m', pretrained=False, num_classes=0)
    bb.global_pool = GeM()
    net = nn.Module(); net.backbone = bb; net.bn = nn.BatchNorm1d(2152)
    sd = load_file(hf_hub_download('conservationxlabs/miewid-msv3', 'model.safetensors'))
    sd = {k: v for k, v in sd.items() if k.startswith(('backbone.', 'bn.'))}
    missing, unexpected = net.load_state_dict(sd, strict=False)
    assert not missing, missing
    net.eval()
    return (lambda x: net.bn(net.backbone(x))), 440, *IMNET

REGISTRY = {
    'clip_b16':      lambda: _clip('ViT-B-16', 'openai', 224, CLIPN),
    'clip_l14':      lambda: _clip('ViT-L-14', 'openai', 224, CLIPN),
    'siglip2_b16':   lambda: _clip('ViT-B-16-SigLIP2', 'webli', 224, HALF),
    'siglip2_so400m':lambda: _clip('ViT-SO400M-16-SigLIP2-384', 'webli', 384, HALF),
    'dinov2_s':      lambda: _timm('vit_small_patch14_reg4_dinov2.lvd142m', 336, img_size=336),
    'dinov2_b':      lambda: _timm('vit_base_patch14_reg4_dinov2.lvd142m', 336, img_size=336),
    'dinov2_l':      lambda: _timm('vit_large_patch14_reg4_dinov2.lvd142m', 336, img_size=336),
    'dinov3_b':      lambda: _timm('vit_base_patch16_dinov3.lvd1689m', 320, img_size=320),
    'dinov3_l':      lambda: _timm('vit_large_patch16_dinov3.lvd1689m', 320, img_size=320),
    'mega_t224':     lambda: _timm('hf-hub:BVRA/MegaDescriptor-T-224', 224),
    'mega_l384':     lambda: _timm('hf-hub:BVRA/MegaDescriptor-L-384', 384),
    'miewid':        _miewid,
}

def load(name):
    fn, size, mean, std = REGISTRY[name]()
    if isinstance(fn, nn.Module): fn = fn.eval()
    return fn, size, mean, std
