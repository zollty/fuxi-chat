from fastapi import Body
from common.api_base import (BaseResponse, ListResponse)
# from configs import logger, log_verbose, LLM_MODELS, HTTPX_DEFAULT_TIMEOUT
# from server.utils import (BaseResponse, fschat_controller_address(), list_config_llm_models,
#                           get_httpx_client, get_model_worker_config)
from typing import List
from common.fastapi_tool import get_httpx_client, HTTPX_DEFAULT_TIMEOUT
from common.utils import LOG_VERBOSE, logger
from llm_chat.config import fschat_controller_address

DEFAULT_LLM = "Qwen-1.8B-Chat"


# Depercated!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def list_running_models(
        controller_address: str = Body(None, description="Fastchat controller服务器地址",
                                       examples=[fschat_controller_address()]),
        placeholder: str = Body(None, description="该参数未使用，占位用"),
) -> BaseResponse:
    '''
    从fastchat controller获取已加载模型列表及其配置项
    '''
    try:
        controller_address = controller_address or fschat_controller_address()
        with get_httpx_client() as client:
            r = client.post(controller_address + "/list_models")
            models = r.json()["models"]
            # data = {m: get_model_config(m).data for m in models} TODO
            data = {m: {} for m in models}
            return BaseResponse(data=data)
    except Exception as e:
        logger.error(f'{e.__class__.__name__}: {e}',
                     exc_info=e if LOG_VERBOSE else None)
        return BaseResponse(
            code=500,
            data={},
            msg=f"failed to get available models from controller: {controller_address}。错误信息是： {e}")

# Depercated!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def stop_llm_model(
        model_name: str = Body(..., description="要停止的LLM模型名称", examples=[DEFAULT_LLM]),
        controller_address: str = Body(None, description="Fastchat controller服务器地址",
                                       examples=[fschat_controller_address()])
) -> BaseResponse:
    '''
    向fastchat controller请求停止某个LLM模型。
    注意：由于Fastchat的实现方式，实际上是把LLM模型所在的model_worker停掉。
    '''
    try:
        controller_address = controller_address or fschat_controller_address()
        with get_httpx_client() as client:
            r = client.post(
                controller_address + "/stop_worker",
                json={"model_name": model_name},
            )
            return r.json()
    except Exception as e:
        logger.error(f'{e.__class__.__name__}: {e}',
                     exc_info=e if LOG_VERBOSE else None)
        return BaseResponse(
            code=500,
            msg=f"failed to stop LLM model {model_name} from controller: {controller_address}。错误信息是： {e}")


# DEPERCATED!!!!!!!!!!!!!!!!!!!!!!!
def change_llm_model(
        model_name: str = Body(..., description="当前运行模型", examples=[DEFAULT_LLM]),
        new_model_name: str = Body(..., description="要切换的新模型", examples=[DEFAULT_LLM]),
        controller_address: str = Body(None, description="Fastchat controller服务器地址",
                                       examples=[fschat_controller_address()]),
        keep_origin: bool = Body(True, description="不释放原模型，加载新模型")
):
    '''
    向fastchat controller请求切换LLM模型。
    DEPERCATED  don't use this function !!!!!!!!!!!!!!!!!
    '''
    try:
        controller_address = controller_address or fschat_controller_address()
        with get_httpx_client() as client:
            if keep_origin:
                r = client.post(
                    controller_address + "/start_worker",
                    json={"model_name": new_model_name},
                    timeout=HTTPX_DEFAULT_TIMEOUT,  # wait for new worker_model
                )
                return r.json()
            else:
                r = client.post(
                    controller_address + "/replace_worker",
                    json={"model_name": model_name, "new_model_name": new_model_name},
                    timeout=HTTPX_DEFAULT_TIMEOUT,  # wait for new worker_model
                )
                return r.json()
    except Exception as e:
        logger.error(f'{e.__class__.__name__}: {e}',
                     exc_info=e if LOG_VERBOSE else None)
        return BaseResponse(
            code=500,
            msg=f"failed to switch LLM model from controller: {controller_address}。错误信息是： {e}")
