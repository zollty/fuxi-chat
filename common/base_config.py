from typing import Dict
from dynaconf import Dynaconf

cfg: Dynaconf = None


def openai_api_cfg():
    return (cfg.get("agent.openai_api_client.address", "http://127.0.0.1:20000/v1"),
            cfg.get("agent.openai_api_client.api_keys", "EMPTY"))


def controller_address():
    from fastchat.serve.openai_api_server import app_settings
    return app_settings.controller_address

def internet_tools_address():
    host = cfg.get("agent.internet_tools_server.host")
    port = cfg.get("agent.internet_tools_server.port")
    return f"http://{host}:{port}"

def controller_keys():
    from fastchat.serve.openai_api_server import app_settings
    return app_settings.api_keys


config_llm_models: Dict = None


def get_config_llm_models() -> Dict:
    return config_llm_models
