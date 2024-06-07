import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
runtime_root_dir = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(runtime_root_dir)

from fastapi import FastAPI, Body, Request, File, Form, UploadFile
from starlette.responses import RedirectResponse
from fuxi.utils.api_base import (BaseResponse, ListResponse)


async def document():
    return RedirectResponse(url="/docs")


def mount_app_routes(app: FastAPI):
    from jian.tools.search_free import do_search_engine
    from jian.tools.webpage_loader import load_webpage

    async def search_engine(
            query: str = Form("", description="查询语句"),
            engine: str = Form("google", description="搜索引擎")
    ) -> BaseResponse:
        context = await do_search_engine(query)
        if context:
            return BaseResponse(code=200, msg="搜索成功", data=context)
        return BaseResponse(code=500, msg="搜索失败")

    async def load_webpage_req(
            url: str = Form(..., description="网址"),
            max_len: int = Form(30000, description="最大长度")
    ) -> BaseResponse:
        context = await load_webpage(url, max_len)
        if context:
            return BaseResponse(code=200, msg="搜索成功", data=context)
        return BaseResponse(code=500, msg="搜索失败")

    app.get("/",
            response_model=BaseResponse,
            summary="swagger 文档")(document)

    app.post("/internet/search_engine",
             tags=["Internet"],
             summary="使用互联网搜索引擎（默认Google）"
             )(search_engine)

    app.post("/internet/load_webpage",
             tags=["Internet"],
             summary="解析url网页内容"
             )(load_webpage_req)


if __name__ == "__main__":
    import argparse
    from fuxi.utils.fastapi_tool import create_app, run_api

    parser = argparse.ArgumentParser(prog='fenghou-ai',
                                     description='About FenghouAI-internet_tools API')
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7962)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # 初始化消息
    args = parser.parse_args()
    args_dict = vars(args)

    app = create_app([mount_app_routes], version="1.0.0", title="FenghouAI internet_tools API Server")

    run_api(app,
            host=args.host,
            port=args.port,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            )
