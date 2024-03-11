import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
RUNTIME_ROOT_DIR = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(RUNTIME_ROOT_DIR)

from fastapi import FastAPI, Body
from starlette.responses import RedirectResponse
from typing import List, Literal
from common.api_base import (BaseResponse, ListResponse)
from llm_chat.config import get_prompt_template


async def document():
    return RedirectResponse(url="/docs")


def query_message(conversation_id: str = Body(..., examples=["0f4f588ede084b80be37716570b469aa"]),
                  limit: int = Body(10, description="size limit"),
                  ) -> BaseResponse:
    ret = []
    return BaseResponse(data=ret)


def mount_app_routes(app: FastAPI, run_mode: str = None):
    from llm_chat.chat.chat import chat
    from llm_chat.chat.openai_chat import openai_chat
    from llm_chat.chat.yby_chat import yby_chat
    from llm_chat.chat.file_chat import file_chat, upload_temp_docs, summary_docs, gen_relate_qa
    from llm_chat.llm_client import (list_running_models,
                                     change_llm_model, stop_llm_model)

    from tools.file_upload_parse import test_parse_docs
    from tools.langchain_utils import test_parse_url

    app.get("/",
            response_model=BaseResponse,
            summary="swagger 文档")(document)

    # Tag: Chat
    app.post("/chat/openapi",
             tags=["Chat"],
             summary="与llm模型对话(直接与fs代理的openapi对话)",
             )(openai_chat)

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
    #
    # app.post("/chat/yby_chat",
    #          tags=["Chat"],
    #          summary="与园博园Agent对话",
    #          )(yby_chat)

    # app.post("/chat/feedback",
    #          tags=["Chat"],
    #          summary="返回llm模型对话评分",
    #          )(chat_feedback)

    # 知识库相关接口
    # mount_knowledge_routes(app)
    # 摘要相关接口
    # mount_filename_summary_routes(app)

    # LLM模型相关接口
    # Depercated!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    app.post("/llm_model/list_running_models11",
             tags=["LLM Model Management"],
             summary="列出当前已加载的模型",
             )(list_running_models)

    # app.post("/llm_model/list_config_models",
    #          tags=["LLM Model Management"],
    #          summary="列出configs已配置的模型",
    #          )(list_config_models)
    #
    # app.post("/llm_model/get_model_config",
    #          tags=["LLM Model Management"],
    #          summary="获取模型配置（合并后）",
    #          )(get_model_config)

    # Depercated!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    app.post("/llm_model/stop11",
             tags=["LLM Model Management"],
             summary="停止指定的LLM模型（Model Worker)",
             )(stop_llm_model)

    # Depercated!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    app.post("/llm_model/change11",
             tags=["LLM Model Management"],
             summary="切换指定的LLM模型（Model Worker)",
             )(change_llm_model)

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

    # 其它接口
    # app.post("/other/completion",
    #          tags=["Other"],
    #          summary="要求llm模型补全(通过LLMChain)",
    #          )(completion)
    #
    # app.post("/other/embed_texts",
    #          tags=["Other"],
    #          summary="将文本向量化，支持本地模型和在线模型",
    #          )(embed_texts_endpoint)

    app.post("/other/filter_message",
             tags=["Other"],
             summary="查询历史消息",
             )(query_message)

    # app.post("/other/parse_docs",
    #          tags=["Other"],
    #          summary="解析文件，返回原始文本内容"
    #          )(parse_docs)
    #
    # app.post("/other/test_parse_docs",
    #          tags=["Other"],
    #          summary="解析文件并分段，返回分段文本内容"
    #          )(test_parse_docs)
    #
    # app.post("/other/test_parse_url",
    #          tags=["Other"],
    #          summary="解析url并分段，返回分段文本内容"
    #          )(test_parse_url)


# def mount_knowledge_routes(app: FastAPI):
#     from server.chat.file_chat import upload_temp_docs, file_chat, summary_docs, gen_relate_qa
#     from server.chat.agent_chat import agent_chat
#
#     app.post("/chat/file_chat",
#              tags=["Knowledge Base Management"],
#              summary="文件对话"
#              )(file_chat)
#
#     app.post("/chat/agent_chat",
#              tags=["Chat"],
#              summary="与agent对话")(agent_chat)
#
#     # 内部接口
#     app.post("/inner/auto_summary_docs",
#              tags=["Inner"],
#              summary="自动总结文档",
#              )(summary_docs)
#
#     app.post("/inner/gen_relate_qa",
#              tags=["Inner"],
#              summary="生成相关提问",
#              )(gen_relate_qa)


if __name__ == "__main__":
    import argparse
    from common.fastapi_tool import create_app, run_api
    from common.utils import VERSION
    from common.llm_controller_client import init_server_config

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

    app = create_app([mount_app_routes], version=VERSION, title="FenghouAI Chat API Server")

    run_api(app,
            host=args.host,
            port=args.port,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            )
