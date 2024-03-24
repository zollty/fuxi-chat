import asyncio
from fastapi.concurrency import run_in_threadpool
from asyncache import cached
from cachetools import TTLCache
from jian.tools.webpage_loader import load_webpage

SEARCH_ENGINE_TOP_K = 5


@cached(TTLCache(100, 600))
async def do_search_engine(text, result_len: int = SEARCH_ENGINE_TOP_K):
    from search_engines import Google

    engine = Google()
    results = engine.search(text, pages=2)

    info = ""
    ctx = []
    links = []
    for row in results.results():
        info += row.get("title") + "\n" + row.get("text")
        host = row.get('host')
        if ("youtube.com" in host
                or "weibo.com" in host
                or "google.com" in host

                or "instagram.com" in host
                or "facebook.com" in host
                or "douyin.com" in host

                or "bilibili.com" in host
                or "youtube.com" in host
                or "instagram.com" in host
                or "facebook.com" in host
                or "douyin.com" in host
        ):
            continue
        if row.get('link').endswith('.pdf'):
            continue
        # context = await load_webpage(row.get('link'), 30000)
        # ctx.append(context)
        links.append(row.get('link'))
        if len(links) >= result_len:
            break

    chat_completions = []
    for li in links:
        content = asyncio.create_task(load_webpage(li, 30000))
        chat_completions.append(content)
    try:
        all_tasks = await asyncio.gather(*chat_completions)
    except Exception as e:
        print(e)
        return ""

    for i, content in enumerate(all_tasks):
        ctx.append(content)

    return info + "\n" + "\n".join(ctx)


# @cached(TTLCache(100, 600))
async def search_engine_iter(query: str):
    # results = await run_in_threadpool(do_search_engine, query)
    # return results
    return ""


def search_internet(query: str):
    return asyncio.run(search_engine_iter(query))


if __name__ == "__main__":
    result = search_internet("今天星期几")
    print("答案:", result)