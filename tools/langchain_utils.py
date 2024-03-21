from fastapi import Body, File, Form, UploadFile
from fuxi.utils.api_base import (BaseResponse, ListResponse)
from jian.tools.config import TEXT_SPLITTER_NAME, CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE

from langchain.document_loaders import WebBaseLoader


def test_parse_url(
        url: str = Form(..., description="可解析的url"),
        chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
        chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),
        start_size: int = Form(0, description="解析开始的字符位置"),
        zh_title_enhance: bool = Form(ZH_TITLE_ENHANCE, description="是否开启中文标题加强"),
) -> BaseResponse:
    try:

        # 创建webLoader
        loader = WebBaseLoader(url)

        # 获取文档
        docs = loader.load()
        # 查看文档内容
        text = docs[0].page_content

        return BaseResponse(code=200, msg="解析成功", data=text)
    except Exception as e:
        msg = f"{url} 解析失败，报错信息为: {e}"
        print(f"{url}--------------------------url parse failed: ")
        print(msg)
        return BaseResponse(code=500, msg=msg)
