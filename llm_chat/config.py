from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    Callable,
    Generator,
    Dict,
    Any,
    Awaitable,
    Union,
    Tuple
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


def default_model():
    return "Qwen-1.8B-Chat"


def default_temperature():
    return 1.0


def openai_proxy():
    return None

def default_openai_model():
    return "gpt-4"

def get_prompt_template(type: str, name: str) -> Optional[str]:
    """
    从prompt_config中加载模板内容
    type: "llm_chat","agent_chat","knowledge_base_chat","search_engine_chat"的其中一种，如果有新功能，应该进行加入。
    """
    from llm_chat.prompt import prompt_config
    import importlib
    importlib.reload(prompt_config)  # TODO: 检查configs/prompt_config.py文件有修改再重新加载
    return prompt_config.PROMPT_TEMPLATES[type].get(name)
