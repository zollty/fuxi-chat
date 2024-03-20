from typing import (
    List,
    Dict,
)
from common.api_base import ApiRequest
from fastchat.serve.openai_api_server import app_settings

api = ApiRequest(base_url=app_settings.controller_address)

url = app_settings.controller_address
print(f"=============================={url}")
print(f"=============================={url}")
print(f"=============================={url}")
print(f"=============================={url}")

def list_llm_models(
        types: List[str] = ["local", "online"],
) -> Dict:
    data = {
        "types": types,
    }
    print("start to list_llm_models---------------------------------")
    response = api.post(
        "/list_llm_models",
        json=data
    )
    return api.get_response_value(response, as_json=True, value_func=lambda r: r.get("data", {}))


def list_embed_models() -> Dict:
    """
    从本地获取configs中配置的embedding模型列表
    """
    print("start to list_embed_models ---------------------------------")
    response = api.post(
        "/list_embed_models",
    )
    return api.get_response_value(response, as_json=True, value_func=lambda r: r.get("data", {}))


def list_online_embed_models() -> Dict:
    """
    从本地获取configs中配置的online embedding模型列表
    """
    print("start to list_online_embed_models ---------------------------------")
    response = api.post(
        "/list_online_embed_models",
    )
    return api.get_response_value(response, as_json=True, value_func=lambda r: r.get("data", {}))


def list_running_llm_models() -> Dict:
    print("start to list_models---------------------------------")
    response = api.post(
        "/list_models"
    )
    return api.get_response_value(response, as_json=True, value_func=lambda r: r.get("models", {}))


def init_server_config():
    import embeddings.config as embeddings_config
    import llm_chat.config as llm_chat_config
    embeddings_config.config_embed_models = list_embed_models()
    llm_chat_config.config_llm_models = list_llm_models()
    embeddings_config.online_embed_models = list_online_embed_models()
    print(f"init config_embed_models--------: {embeddings_config.config_embed_models}")
    print(f"init online_embed_models--------: {embeddings_config.online_embed_models}")
    print(f"init config_llm_models--------: {llm_chat_config.config_llm_models}")
