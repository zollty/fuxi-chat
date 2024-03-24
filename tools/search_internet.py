import asyncio
from fastapi.concurrency import run_in_threadpool
from asyncache import cached
from cachetools import TTLCache

SEARCH_ENGINE_TOP_K = 10


def duckduckgo_search(text, result_len: int = SEARCH_ENGINE_TOP_K):
    from langchain.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
    search = DuckDuckGoSearchAPIWrapper()
    return search.results(text, result_len)


def search_result2docs(search_results):
    context = ""
    for item in search_results:
        context = context + "\n" + item["snippet"] if "snippet" in item.keys() else ""
    return context


@cached(TTLCache(100, 600))
async def search_engine_iter(query: str):
    results = await run_in_threadpool(duckduckgo_search, query)
    contents = search_result2docs(results)
    return contents


def search_internet(query: str):
    return asyncio.run(search_engine_iter(query))


if __name__ == "__main__":
    result = search_internet("今天星期几")
    print("答案:", result)
