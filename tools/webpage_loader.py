from asyncache import cached
from cachetools import TTLCache


@cached(TTLCache(100, 600))
async def load_webpage(url: str, max_len: int = 30000) -> str:
    from langchain.document_loaders import WebBaseLoader
    # 创建webLoader
    loader = WebBaseLoader(url)
    # 获取文档
    docs = loader.load()
    # 查看文档内容
    context = docs[0].page_content
    if len(context) > max_len:
        context = context[:max_len]
    return context
