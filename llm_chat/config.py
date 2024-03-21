from typing import (
    Optional,
    Dict,
    List,
)
import threading
from jian.common.base_config import *

# DEFAULT_LLM = "Qwen-1.8B-Chat"
# LONG_CONTEXT_MODEL = "chatglm3-6b-32k"
# LONG_CONTEXT_MODEL = "Qwen1.5-14B-Chat-GPTQ-Int4"  # "Qwen1.5-7B-Chat"
# TEMPERATURE = 0.7
# FILE_CHAT_DEFAULT_TEMPERATURE = 0.1

global_running_models_dict = {}


# from fastchat.serve.openai_api_server import (app, logger, fetch_remote, get_gen_params, get_worker_address,
#                                               check_requests, chat_completion_stream_generator, generate_completion,
#                                               create_error_response,
#                                               check_api_key, app_settings, generate_completion_stream)

def init_get_running_models():
    from jian.common.llm_controller_client import list_running_llm_models
    global global_running_models_dict
    global_running_models_dict = list_running_llm_models()
    print("--------------------get global_running_models_dict--------------------------")
    print(global_running_models_dict)


def default_model():
    default_model_order = cfg["agent.default_model_order"]
    for model in default_model_order:
        if model in global_running_models_dict:
            print(f"use model: {model}, running models:{global_running_models_dict}")
            return model
    print(f"warning: use default model: Qwen-1.8B-Chat, running models:{global_running_models_dict}")
    return "Qwen-1.8B-Chat"


def default_temperature():
    return 0.7


def default_long_context_model():
    default_model_order = cfg["agent.default_long_context_model_order"]
    for model in default_model_order:
        if model in global_running_models_dict:
            print(f"use model: {model}, running models:{global_running_models_dict}")
            return model
    print(f"warning: use default model: Qwen1.5-7B-Chat, running models:{global_running_models_dict}")
    return "Qwen1.5-7B-Chat"


def file_chat_default_temperature():
    return 0.1


def file_chat_summary_model():
    return default_long_context_model()


def file_chat_relate_qa_model():
    return file_chat_summary_model()


def summary_max_length():
    return 30000


def openai_proxy():
    return None


def default_openai_model():
    return "gpt-4"


def get_prompt_template(type: str, name: str) -> Optional[str]:
    """
    从prompt_config中加载模板内容
    type: "llm_chat","agent_chat","knowledge_base_chat","search_engine_chat"的其中一种，如果有新功能，应该进行加入。
    """
    from jian.llm_chat.prompt import prompt_config
    import importlib
    importlib.reload(prompt_config)  # TODO: 检查configs/prompt_config.py文件有修改再重新加载
    return prompt_config.PROMPT_TEMPLATES[type].get(name)



def init_config():
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    # 调度方法为 timedTask，触发器选择 interval(间隔性)，间隔时长为 2 秒
    scheduler.add_job(init_get_running_models, 'interval', seconds=15)
    scheduler.start()
    init_get_running_models()
    # t = threading.Timer(5, init_get_running_models)  # 延时x秒后执行action函数
    # t.start()
    # threading.Timer(10, init_get_running_models).start()
    # threading.Timer(15, init_get_running_models).start()