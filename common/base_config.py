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
    settings_files=['conf/llm_model.yml', 'conf/settings.yaml'],
)

def openai_api_cfg():
    # if host == "0.0.0.0":
    #     host = "127.0.0.1"
    # port = FSCHAT_OPENAI_API["port"]
    # return f"http://{host}:{port}/v1"
    # address, api_key
    return controller_address() + "/v1", "EMPTY"


def controller_address():
    from fastchat.serve.openai_api_server import app_settings
    return app_settings.controller_address


config_llm_models = None


def get_config_llm_models() -> Dict:
    return config_llm_models

