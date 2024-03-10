from typing import (
    Optional,
    Dict,
    List,
)
from common.base_config import *

DEFAULT_LLM = "Qwen-1.8B-Chat"
LONG_CONTEXT_MODEL = "chatglm3-6b-32k"
TEMPERATURE = 0.7
FILE_CHAT_DEFAULT_TEMPERATURE = 0.1

def file_chat_default_temperature():
    return 0.1

def file_chat_summary_model():
    return LONG_CONTEXT_MODEL

def file_chat_relate_qa_model():
    return file_chat_summary_model()

def summary_max_length():
    return 30000

def default_model():
    return "Qwen-1.8B-Chat"


def default_temperature():
    return TEMPERATURE


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

