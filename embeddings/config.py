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

def list_embed_models() -> List[str]:
    '''
    get names of configured embedding models
    '''
    return [] #list(MODEL_PATH["embed_model"])


def list_online_embed_models() -> Dict:
    # from server import model_workers

    ret = {}
    for k, v in list_config_llm_models()["online"].items():
        if provider := v.get("provider"):
            worker_class = getattr(model_workers, provider, None)
            if worker_class is not None and worker_class.can_embedding():
                ret[k] = worker_class
    return ret


def get_model_path(model_name: str, type: str = None) -> Optional[str]:
    return ""