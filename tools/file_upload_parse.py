from fastapi import Body, File, Form, UploadFile
from typing import AsyncIterable, List, Optional
import os
from langchain.docstore.document import Document
from common.utils import run_in_thread_pool, get_temp_dir
from tools.document_loaders_helper import load_file_docs
from tools.text_splitter_helper import do_split_docs
from common.api_base import (BaseResponse, ListResponse)
from tools.config import TEXT_SPLITTER_NAME, CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE


def parse_files_in_thread(
        files: List[UploadFile],
        dir: str,
        start_length: int = -1,
        split_docs_fn=None
):
    """
    通过多线程将上传的文件保存到对应目录内。
    生成器返回保存结果：[success or error, filename, msg, docs]
    """

    def parse_file(file: UploadFile) -> dict:
        """
        保存单个文件。
        """
        filename = file.filename
        try:
            file_path = os.path.join(dir, filename)
            file_content = file.file.read()  # 读取上传文件的内容
            if not os.path.isdir(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, "wb") as f:
                f.write(file_content)

            docs = load_file_docs(
                file_path,
                filename=filename,
                start_length=start_length
            )

            split_docs = None
            if split_docs_fn:
                split_docs = split_docs_fn(docs)
            return True, filename, f"成功上传文件 {filename}", docs, split_docs
        except Exception as e:
            msg = f"{filename} 文件上传失败，报错信息为: {e}"
            return False, filename, msg, [], []

    params = [{"file": file} for file in files]
    for result in run_in_thread_pool(parse_file, params=params):
        yield result


def parse_docs(
        files: List[UploadFile] = File(..., description="上传文件，支持多文件")
) -> BaseResponse:
    failed_files = []
    documents = []
    path, id = get_temp_dir()
    print("--------------------------update file, save dir: ")
    print(id)
    rt_success = False
    for success, file, msg, docs, _ in parse_files_in_thread(files=files, dir=path):
        if success:
            documents += docs
            print(f"{file}--------------------------update file success: ")
            # print(docs)
            rt_success = True
        else:
            failed_files.append({file: msg})
            print(f"{file}--------------------------update file failed: ")
            print(msg)
    if rt_success:
        return BaseResponse(code=200, msg="文件上传与解析完成",
                            data={"id": id, "docs": documents, "failed_files": failed_files})
    return BaseResponse(code=500, msg="解析文件失败", data={"failed_files": failed_files})


def test_parse_docs(
        files: List[UploadFile] = File(..., description="上传文件，支持多文件"),
        text_splitter_name: str = Form(TEXT_SPLITTER_NAME, description="分段函数"),
        chunk_size: int = Form(CHUNK_SIZE, description="知识库中单段文本最大长度"),
        chunk_overlap: int = Form(OVERLAP_SIZE, description="知识库中相邻文本重合长度"),
        start_size: int = Form(0, description="解析开始的字符位置"),
        zh_title_enhance: bool = Form(ZH_TITLE_ENHANCE, description="是否开启中文标题加强"),
) -> BaseResponse:
    def split_docs_fn(
            docs: List[Document]
    ):
        return do_split_docs(docs,
                             text_splitter_name=text_splitter_name,
                             zh_title_enhance=zh_title_enhance,
                             chunk_size=chunk_size,
                             chunk_overlap=chunk_overlap)

    failed_files = []
    file_docs = []
    path, id = get_temp_dir()
    print(f"--------------------------update file, save dir: {id}")
    rt_success = False
    for success, file, msg, _, split_docs in parse_files_in_thread(files=files,
                                                                   dir=path,
                                                                   start_length=start_size,
                                                                   split_docs_fn=split_docs_fn):
        if success:
            file_docs.append({"f": file, "d": split_docs})
            print(f"{file}--------------------------update file success: ")
            # print(docs)
            rt_success = True
        else:
            failed_files.append({file: msg})
            print(f"{file}--------------------------update file failed: ")
            print(msg)
    if rt_success:
        return BaseResponse(code=200, msg="文件解析成功",
                            data={"id": id, "files": file_docs, "failed_files": failed_files})
    return BaseResponse(code=500, msg="解析文件失败", data={"id": id, "failed_files": failed_files})
