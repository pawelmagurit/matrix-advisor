import numpy as np
from skimage.feature import hog

from matrix_advisor.config import CANVAS_SIZE
from matrix_advisor.normalization.pipeline import load_mask

_TORCH_AVAILABLE = False
_resnet = None
_transform = None


def _init_torch() -> bool:
    global _TORCH_AVAILABLE, _resnet, _transform
    if _TORCH_AVAILABLE:
        return True
    try:
        import torch
        import torchvision.models as models
        import torchvision.transforms as T

        _resnet = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        _resnet.fc = torch.nn.Identity()
        _resnet.eval()
        _transform = T.Compose(
            [
                T.ToPILImage(),
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        _TORCH_AVAILABLE = True
        return True
    except Exception:
        _TORCH_AVAILABLE = False
        _resnet = None
        _transform = None
        return False


def _mask_to_rgb(mask: np.ndarray) -> np.ndarray:
    rgb = np.stack([mask, mask, mask], axis=-1)
    return rgb


def embed_hog(mask: np.ndarray) -> np.ndarray:
    binary = (mask > 127).astype(np.uint8)
    features = hog(
        binary,
        orientations=8,
        pixels_per_cell=(16, 16),
        cells_per_block=(2, 2),
        visualize=False,
    )
    vec = features.astype(np.float64)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def embed_resnet(mask: np.ndarray) -> np.ndarray:
    if not _init_torch():
        return embed_hog(mask)

    import torch

    rgb = _mask_to_rgb(mask)
    tensor = _transform(rgb).unsqueeze(0)
    with torch.no_grad():
        vec = _resnet(tensor).squeeze(0).numpy()
    norm = np.linalg.norm(vec)
    return vec.astype(np.float64) / norm if norm > 0 else vec.astype(np.float64)


def embed_profile(profile_id: str, backend: str = "auto") -> np.ndarray | None:
    mask = load_mask(profile_id)
    if mask is None:
        return None
    if backend == "hog":
        return embed_hog(mask)
    if backend == "resnet":
        return embed_resnet(mask)
    # auto: try resnet, fallback hog
    vec = embed_resnet(mask)
    return vec


def embed_with_rotations_from_mask(mask: np.ndarray, backend: str = "auto") -> list[np.ndarray]:
    vectors = []
    for k in range(4):
        rotated = np.rot90(mask, k)
        if backend == "hog":
            vectors.append(embed_hog(rotated))
        elif backend == "resnet":
            vectors.append(embed_resnet(rotated))
        elif _init_torch():
            vectors.append(embed_resnet(rotated))
        else:
            vectors.append(embed_hog(rotated))
    return vectors


def embed_with_rotations(profile_id: str, backend: str = "auto") -> list[np.ndarray]:
    mask = load_mask(profile_id)
    if mask is None:
        return []
    return embed_with_rotations_from_mask(mask, backend=backend)


def embedding_backend_name() -> str:
    return "resnet18" if _init_torch() else "hog"
