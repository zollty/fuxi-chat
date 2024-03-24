import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
runtime_root_dir = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(runtime_root_dir)

from fastapi import FastAPI, Body, Request
from starlette.responses import RedirectResponse
from typing import List, Literal
from fuxi.utils.api_base import (BaseResponse, ListResponse)
from jian.llm_chat.config import get_prompt_template


async def document():
    return RedirectResponse(url="/docs")


def query_message(conversation_id: str = Body(..., examples=["0f4f588ede084b80be37716570b469aa"]),
                  limit: int = Body(10, description="size limit"),
                  ) -> BaseResponse:
    ret = []
    return BaseResponse(data=ret)


async def update_config(request: Request):
    from omegaconf import OmegaConf
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8")
    print("---------------------------------------")
    # print(body_text)
    conf = OmegaConf.create(body_text)
    print(conf["llm"]["default_run"])
    print(OmegaConf.to_yaml(conf))
    return BaseResponse(data=body_text)


def mount_app_routes(app: FastAPI):
    from jian.llm_chat.chat.chat import chat
    from jian.llm_chat.chat.openai_chat import openai_chat
    from jian.llm_chat.chat.unichat import unichat
    from jian.llm_chat.chat.yby_chat import yby_chat
    from jian.llm_chat.chat.file_chat import file_chat, upload_temp_docs, summary_docs, gen_relate_qa
    from jian.llm_chat.chat.special_chat import summary_chat, summary_chat2

    from jian.tools.file_upload_parse import test_parse_docs
    from jian.tools.langchain_utils import test_parse_url

    app.get("/",
            response_model=BaseResponse,
            summary="swagger 文档")(document)

    # Tag: Chat
    app.post("/chat/chat",
             tags=["Chat"],
             summary="与llm模型对话(通过LLMChain)",
             )(chat)

    app.post("/chat/file_chat",
             tags=["Chat"],
             summary="文件对话"
             )(file_chat)

    app.post("/chat/yby_chat",
             tags=["Chat"],
             summary="与园博园Agent对话"
             )(yby_chat)

    app.post("/chat/summary_chat",
             tags=["Chat"],
             summary="文档总结"
             )(summary_chat)

    app.post("/chat/unichat",
             tags=["Chat"],
             summary="综合Chat（兼容OpenAI API）"
             )(unichat)

    app.post("/chat/openai",
             tags=["Chat"],
             summary="与代理的openai api对话",
             )(openai_chat)

    # 内部接口
    app.post("/inner/file_chat/auto_summary_docs",
             tags=["Inner"],
             summary="自动总结文档（for file_chat，用于文件对话）。内部接口，勿单独调用",
             )(summary_docs)

    app.post("/inner/file_chat/gen_relate_qa",
             tags=["Inner"],
             summary="生成相关提问（for file_chat，用于文件对话）。内部接口，勿单独调用",
             )(gen_relate_qa)

    app.post("/inner/file_chat/upload_temp_docs",
             tags=["Inner"],
             summary="上传文件到临时目录（for file_chat，用于文件对话）。内部接口，勿单独调用"
             )(upload_temp_docs)

    app.post("/inner/config/update_config",
             tags=["Inner"],
             summary="更新配置"
             )(update_config)

    app.post("/tools/test_parse_docs",
             tags=["Tools"],
             summary="解析文件并分段，返回分段文本内容"
             )(test_parse_docs)

    app.post("/tools/test_parse_url",
             tags=["Tools"],
             summary="解析url并分段，返回分段文本内容"
             )(test_parse_url)

    # app.post("/chat/search_engine_chat",
    #          tags=["Chat"],
    #          summary="与搜索引擎对话",
    #          )(search_engine_chat)
    # app.post("/chat/feedback",
    #          tags=["Chat"],
    #          summary="返回llm模型对话评分",
    #          )(chat_feedback)

    # 服务器相关接口
    # app.post("/server/configs",
    #          tags=["Server State"],
    #          summary="获取服务器原始配置信息",
    #          )(get_server_configs)
    #
    # app.post("/server/list_search_engines",
    #          tags=["Server State"],
    #          summary="获取服务器支持的搜索引擎",
    #          )(list_search_engines)

    @app.post("/server/get_prompt_template",
              tags=["Server State"],
              summary="获取服务区配置的 prompt 模板")
    def get_server_prompt_template(
            type: Literal["llm_chat", "knowledge_base_chat", "search_engine_chat", "agent_chat", "yby_chat"] = Body(
                "llm_chat",
                description="模板类型，可选值：llm_chat，knowledge_base_chat，search_engine_chat，agent_chat，yby_chat"),
            name: str = Body("default", description="模板名称"),
    ) -> str:
        return get_prompt_template(type=type, name=name)

    app.post("/other/filter_message",
             tags=["Other"],
             summary="查询历史消息",
             )(query_message)


if __name__ == "__main__":
    import argparse
    from fuxi.utils.fastapi_tool import create_app, run_api
    from jian.common.llm_controller_client import init_server_config

    parser = argparse.ArgumentParser(prog='fenghou-ai',
                                     description='About FenghouAI-Chat API')
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7961)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # 初始化消息
    args = parser.parse_args()
    args_dict = vars(args)

    init_server_config()

    app = create_app([mount_app_routes], version="1.0.0", title="FenghouAI Chat API Server")

    run_api(app,
            host=args.host,
            port=args.port,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            )
