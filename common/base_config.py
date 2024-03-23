from typing import (
    Optional,
    Dict,
    List,
)

from fuxi.utils.runtime_conf import get_runtime_root_dir
from dynaconf import Dynaconf

print(get_runtime_root_dir())
cfg = Dynaconf(
    envvar_prefix="JIAN",
    root_path=get_runtime_root_dir(),
    settings_files=['conf/llm_model.yml', 'conf/settings.yaml'],
)

def openai_api_cfg():
    # if host == "0.0.0.0":
    #     host = "127.0.0.1"
    # port = FSCHAT_OPENAI_API["port"]
    # return f"http://{host}:{port}/v1"
    # address, api_key
    return controller_address() + "/v1", api_keys()


def controller_address():
    from fastchat.serve.openai_api_server import app_settings
    return app_settings.controller_address


def api_keys():
    from fastchat.serve.openai_api_server import app_settings
    return app_settings.api_keys


config_llm_models = None


def get_config_llm_models() -> Dict:
    return config_llm_models

