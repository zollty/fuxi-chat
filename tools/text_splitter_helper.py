import importlib
from jian.tools.config import text_splitter_dict, DEFAULT_HUGGINGFACE_TOKENIZER_MODEL, SUPPORTED_EXTS
from typing import List, Union, Dict

from jian.tools.config import TEXT_SPLITTER_NAME, CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE
import langchain

def load_text_splitter(
        splitter_name: str = TEXT_SPLITTER_NAME,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = OVERLAP_SIZE,
        huggingface_tokenizer_model: str = DEFAULT_HUGGINGFACE_TOKENIZER_MODEL,
):
    """
    根据参数获取特定的分词器
    """
    splitter_name = splitter_name or "SpacyTextSplitter"
    print(f"------------------------------------------获取文档切分器：{splitter_name}")
    try:
        if splitter_name == "MarkdownHeaderTextSplitter":  # MarkdownHeaderTextSplitter特殊判定
            headers_to_split_on = text_splitter_dict[splitter_name]['headers_to_split_on']
            print("------------------------------------------使用文档切分器：MarkdownHeaderTextSplitter")
            text_splitter = langchain.text_splitter.MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on)
        else:

            try:  # 优先使用用户自定义的text_splitter
                text_splitter_module = importlib.import_module('jian.tools.text_splitter')
                TextSplitter = getattr(text_splitter_module, splitter_name)
            except:  # 否则使用langchain的text_splitter
                text_splitter_module = importlib.import_module('langchain.text_splitter')
                TextSplitter = getattr(text_splitter_module, splitter_name)

            if text_splitter_dict[splitter_name]["source"] == "tiktoken":  # 从tiktoken加载
                try:
                    text_splitter = TextSplitter.from_tiktoken_encoder(
                        encoding_name=text_splitter_dict[splitter_name]["tokenizer_name_or_path"],
                        pipeline="zh_core_web_sm",
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                except:
                    text_splitter = TextSplitter.from_tiktoken_encoder(
                        encoding_name=text_splitter_dict[splitter_name]["tokenizer_name_or_path"],
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
            elif text_splitter_dict[splitter_name]["source"] == "huggingface":  # 从huggingface加载
                # 参见：https: // zhuanlan.zhihu.com / p / 640424318
                if text_splitter_dict[splitter_name]["tokenizer_name_or_path"] == "":
                    text_splitter_dict[splitter_name]["tokenizer_name_or_path"] = huggingface_tokenizer_model

                if text_splitter_dict[splitter_name]["tokenizer_name_or_path"] == "gpt2":
                    from transformers import GPT2TokenizerFast
                    from langchain.text_splitter import CharacterTextSplitter
                    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
                else:  # 字符长度加载
                    from transformers import AutoTokenizer
                    tokenizer = AutoTokenizer.from_pretrained(
                        text_splitter_dict[splitter_name]["tokenizer_name_or_path"], trust_remote_code=True)

                text_splitter = TextSplitter.from_huggingface_tokenizer(
                    tokenizer=tokenizer,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
            else:
                try:
                    text_splitter = TextSplitter(
                        pipeline="zh_core_web_sm",
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                except:
                    text_splitter = TextSplitter(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
    except Exception as e:
        print(e)
        text_splitter_module = importlib.import_module('langchain.text_splitter')
        TextSplitter = getattr(text_splitter_module, "RecursiveCharacterTextSplitter")
        text_splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print("错误信息见上--------------改用文档切分器：langchain.text_splitter.RecursiveCharacterTextSplitter")

    # If you use SpacyTextSplitter you can use GPU to do split likes Issue #1287
    # text_splitter._tokenizer.max_length = 37016792
    # text_splitter._tokenizer.prefer_gpu()
    return text_splitter


from langchain.docstore.document import Document
from jian.tools.zh_title_enhance import zh_title_enhance as func_zh_title_enhance


def do_split_docs(
        docs: List[Document],
        text_splitter_name: str = TEXT_SPLITTER_NAME,
        zh_title_enhance: bool = ZH_TITLE_ENHANCE,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = OVERLAP_SIZE,
):
    if not docs:
        return []

    text_splitter = load_text_splitter(splitter_name=text_splitter_name, chunk_size=chunk_size,
                                       chunk_overlap=chunk_overlap)

    if text_splitter_name == "MarkdownHeaderTextSplitter":
        split_docs = text_splitter.split_text(docs[0].page_content)
        lens = len(split_docs)
        print(f"--------MarkdownHeaderTextSplitter--------文档切分后数量：{lens}")
    else:
        split_docs = text_splitter.split_documents(docs)

    if not split_docs:
        return []

    if zh_title_enhance:
        split_docs = func_zh_title_enhance(split_docs)

    lens = len(split_docs)
    print(f"文档切分结果：-----------------------------------切分后数量：{lens}")
    for dd in split_docs:
        #print(docs[0].index(dd.page_content))
        print(dd)

    return split_docs
