import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
get_runtime_root_dir() = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(get_runtime_root_dir())

from langchain.document_loaders import TextLoader
from langchain.embeddings import ModelScopeEmbeddings
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
import chardet
from retrieval.redis_search_vl import create_and_run_index, insert_doc, retrieve_docs, DocSchema, get_short_url

# def read_file(path, encoding):
#     result = []
#     with open(path, 'r', encoding=encoding) as f:
#         result.append(f.read())
#     return result

# 读取原始文档
raw_documents_sanguo = TextLoader('/ai/apps/data/园博园参考资料.txt', encoding='utf-8').load()
raw_documents_xiyou = TextLoader('/ai/apps/data/园博园介绍.txt', encoding='utf-8').load()
raw_documents_fw = TextLoader('/ai/apps/data/园博园服务.txt', encoding='utf-8').load()

print(
    len(raw_documents_sanguo[0].page_content + raw_documents_xiyou[0].page_content + raw_documents_fw[0].page_content))

# 分割文档
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
documents_sanguo = text_splitter.split_documents(raw_documents_sanguo)
documents_xiyou = text_splitter.split_documents(raw_documents_xiyou)
documents_fw = text_splitter.split_documents(raw_documents_fw)
documents = documents_sanguo + documents_xiyou + documents_fw
print("documents nums:", documents.__len__())
print(documents[0].page_content)
print(documents[-1].page_content)


def load_docs(path: str):
    # 读取原始文档
    raw_documents = TextLoader(path, encoding='utf-8').load()

    print(len(raw_documents[0].page_content))

    # 分割文档
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=50)
    documents = text_splitter.split_documents(raw_documents)
    print("documents nums:", documents.__len__())
    print(documents[0].page_content)
    print(documents[-1].page_content)

    docs = [DocSchema(doc=x.page_content, key=get_short_url(x.page_content), src=path) for x in documents]
    return docs


if __name__ == '__main__':

    kb_name = "yby"
    create_and_run_index(kb_name)

    raw_documents_sanguo = load_docs('/ai/apps/data/园博园参考资料.txt')
    raw_documents_xiyou = load_docs('/ai/apps/data/园博园介绍.txt')
    raw_documents_fw = load_docs('/ai/apps/data/园博园服务.txt')
    docs = raw_documents_sanguo + raw_documents_xiyou + raw_documents_fw

    insert_doc(docs, kb_name, use_id="key")

    sentences = [
        "白蛇娘子",
        "美国",
        "照壁",
        "博纳",
        "梅苑山庄",
        "院融景园",
        "在景点分布布局上，主要的景点景区中有梅林山庄吗",
        "介绍一下景点分布布局上的主要景点景区",
        "哪里提到了梅苑山庄",
        "梅苑山庄与什么关联",
        "提到梅苑山庄是什么事情",
        "某省被成为曲艺之乡，包括相声、评书等都在这里形成，某园林具有地域文化特色",
        "“某省被成为曲艺之乡，包括相声、评书等都在这里形成，某园林具有地域文化特色”，请问这是哪个园林",
    ]
    for doc in sentences:
        print(f"\n\n\n\n-------------------------query: {doc}")
        results = retrieve_docs(doc, kb_name, 3)
        for x in results:
            print(x["doc"], x["vector_distance"], x["src"])
