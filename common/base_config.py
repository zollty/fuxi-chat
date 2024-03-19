from typing import (
    Optional,
    Dict,
    List,
)

from common.utils import RUNTIME_ROOT_DIR
from dynaconf import Dynaconf

print(RUNTIME_ROOT_DIR)
cfg = Dynaconf(
    envvar_prefix="FUXI",
    root_path=RUNTIME_ROOT_DIR,
    settings_files=['llm_model/conf_llm_model.yml', 'settings.yaml'],
)

def fschat_openai_api_cfg():
    # if host == "0.0.0.0":
    #     host = "127.0.0.1"
    # port = FSCHAT_OPENAI_API["port"]
    # return f"http://{host}:{port}/v1"
    # address, api_key
    return "http://localhost:20000/v1", "EMPTY"

def fschat_controller_address():
    return "http://localhost:21001"


config_llm_models = None

def get_config_llm_models() -> Dict:
    return config_llm_models


