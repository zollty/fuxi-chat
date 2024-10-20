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
from jian.tools.config import TEXT_SPLITTER_NAME, CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE
from langchain.docstore.document import Document
from jian.tools.text_splitter_helper import do_split_docs


async def document():
    return RedirectResponse(url="/docs")


def mount_deep_parser_app_routes(app: FastAPI):
    from fuxi.utils.runtime_conf import get_temp_dir
    from jian.tools.file_upload_parse import parse_files_in_thread, FileLoadReq, parse_files_by_url_in_thread

    async def text_split_req(
            text: str = Form(..., description="文本"),
            text_splitter_name: str = Form(TEXT_SPLITTER_NAME, description="分段函数"),
            chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
            chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度")
    ) -> BaseResponse:
        docs = do_split_docs([Document(page_content=text, metadata={})],
                             text_splitter_name=text_splitter_name, chunk_size=chunk_size,
                             chunk_overlap=chunk_overlap)
        return BaseResponse(code=200, msg="文件分段完成", data=
        [{"page_content": x.page_content, "metadata": x.metadata, "type": x.type} for x in docs])

    async def load_file_by_form_req(
            file: UploadFile = File(..., description="浏览器标准Form二进制文件对象"),
            file_name: str = Form(None, description="名称"),
            file_format: str = Form(None, description="后缀")
    ) -> BaseResponse:
        failed_files = []
        documents = []
        path, id = get_temp_dir()
        print("--------------------------update file, save dir: ")
        print(id)
        rt_success = False
        for success, filename, msg, docs, _ in parse_files_in_thread(files=[file], dir=path):
            if success:
                documents += docs
                print(f"{filename}--------------------------update file success: ")
                # print(docs)
                rt_success = True
            else:
                failed_files.append({filename: msg})
                print(f"{filename}--------------------------update file failed: ")
                print(msg)
        if rt_success:
            return BaseResponse(code=200, msg="文件上传与解析完成",
                                data={"content": documents[0].page_content, "metadata": documents[0].metadata})
        return BaseResponse(code=500, msg="解析文件失败")

    async def load_file_by_url_req(
            file_url: str = Form(..., description="文件URL"),
            file_name: str = Form(None, description="名称"),
            file_format: str = Form(None, description="后缀")
    ) -> BaseResponse:
        failed_files = []
        documents = []
        path, id = get_temp_dir()
        print("--------------------------update file, save dir: ")
        print(id)
        rt_success = False
        for success, filename, msg, docs, _ in (
                parse_files_by_url_in_thread(files=[FileLoadReq(file_url, file_name, file_format)], dir=path)):
            if success:
                documents += docs
                print(f"{filename}--------------------------update file success: ")
                # print(docs)
                rt_success = True
            else:
                failed_files.append({filename: msg})
                print(f"{filename}--------------------------update file failed: ")
                print(msg)
        if rt_success:
            return BaseResponse(code=200, msg="文件上传与解析完成",
                                data={"content": documents[0].page_content, "metadata": documents[0].metadata})
        return BaseResponse(code=500, msg="解析文件失败")

    async def load_file_and_split_by_form_req(
            file: UploadFile = File(..., description="浏览器标准Form二进制文件对象"),
            file_name: str = Form(None, description="名称"),
            file_format: str = Form(None, description="后缀"),
            text_splitter_name: str = Form(TEXT_SPLITTER_NAME, description="分段函数"),
            chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
            chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度")
    ) -> BaseResponse:
        docs = []
        res = await load_file_by_form_req(file, file_name, file_format)
        if res.code == 200:
            docs.append(Document(page_content=res.data["content"], metadata=res.data["metadata"]))
        else:
            return res
        docs = do_split_docs(docs,
                             text_splitter_name=text_splitter_name, chunk_size=chunk_size,
                             chunk_overlap=chunk_overlap)
        return BaseResponse(code=200, msg="文件解析及分段完成", data=
                            [{"page_content": x.page_content, "metadata": x.metadata, "type": x.type} for x in docs])

    async def load_file_and_split_by_url_req(
            file_url: str = Form(..., description="文件URL"),
            file_name: str = Form(None, description="名称"),
            file_format: str = Form(None, description="后缀"),
            text_splitter_name: str = Form(TEXT_SPLITTER_NAME, description="分段函数"),
            chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
            chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度")
    ) -> BaseResponse:
        docs = []
        res = await load_file_by_url_req(file_url, file_name, file_format)
        if res.code == 200:
            docs.append(Document(page_content=res.data["content"], metadata=res.data["metadata"]))
        else:
            return res
        docs = do_split_docs(docs,
                             text_splitter_name=text_splitter_name, chunk_size=chunk_size,
                             chunk_overlap=chunk_overlap)
        return BaseResponse(code=200, msg="文件解析及分段完成", data=
                            [{"page_content": x.page_content, "metadata": x.metadata, "type": x.type} for x in docs])

    # app.get("/",
    #         response_model=BaseResponse,
    #         summary="swagger 文档")(document)
    app.post("/doc/text-split",
             tags=["DeepParser"],
             summary="文档分段（TextSplitter）"
             )(text_split_req)

    app.post("/doc/load-file-content-by-form",
             tags=["DeepParser"],
             summary="文档解析（不分段）（表单上传）"
             )(load_file_by_form_req)

    app.post("/doc/load-file-content-by-url",
             tags=["DeepParser"],
             summary="文档解析（不分段）（根据文件URL）"
             )(load_file_by_url_req)

    app.post("/doc/parse-and-split-file-by-form",
             tags=["DeepParser"],
             summary="文档解析分段（根据临时上传文件）"
             )(load_file_and_split_by_form_req)

    app.post("/doc/parse-and-split-file-by-url",
             tags=["DeepParser"],
             summary="文档解析分段（根据文件url下载）"
             )(load_file_and_split_by_url_req)


if __name__ == "__main__":
    import argparse
    from fuxi.utils.fastapi_tool import create_app, run_api

    parser = argparse.ArgumentParser(prog='fenghou-ai',
                                     description='About FenghouAI-DeepParser API')
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7963)
    parser.add_argument("--ssl_keyfile", type=str)
    parser.add_argument("--ssl_certfile", type=str)
    # 初始化消息
    args = parser.parse_args()
    args_dict = vars(args)

    app = create_app([mount_deep_parser_app_routes], version="1.0.0", title="FenghouAI DeepParser API Server")

    run_api(app,
            host=args.host,
            port=args.port,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            )
