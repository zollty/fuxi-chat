from typing import List, Literal, Optional, Dict
from common.utils import detect_device

# 选用的 Embedding 名称
EMBEDDING_MODEL = "bge-large-zh-v1.5"

# Embedding 模型运行设备。设为 "auto" 会自动检测(会有警告)，也可手动设定为 "cuda","mps","cpu","xpu" 其中之一。
EMBEDDING_DEVICE = "auto"

OPENAI_EMBEDDINGS_CHUNK_SIZE = 500


def embedding_device(device: str = None) -> Literal["cuda", "mps", "cpu"]:
    device = device or EMBEDDING_DEVICE
    if device not in ["cuda", "mps", "cpu"]:
        device = detect_device()
    return device


# 从model_config中获取模型信息


config_embed_models = {}


def get_config_embed_models() -> Dict:
    return config_embed_models


online_embed_models = {}


def get_online_embed_models() -> Dict:
    return online_embed_models


def get_embed_model_path(model_name: str) -> str:
    return config_embed_models[model_name]
