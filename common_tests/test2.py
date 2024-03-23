import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
get_runtime_root_dir = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(get_runtime_root_dir)

from typing import (
    TYPE_CHECKING,
    Literal,
    List,
    Optional,
    Callable,
    Generator,
    Dict,
    Any,
    Awaitable,
    Union,
    Tuple
)


class AAAA:
    def __init__(self, aa, bb):
        self.aa = aa
        self.bb = bb


def format_jinja2_prompt_tmpl(prompt: str = None, tmpl_type: str = None, tmpl_name: str = None, **kwargs):
    print(f"-----prompt: {prompt}")
    print(f"-----prompt: {tmpl_type}")
    print(f"-----prompt: {tmpl_name}")
    print(f"-----prompt: {kwargs}")


def props_with_(obj):
    params = {}
    for name in dir(obj):
        value = getattr(obj, name)
        if not name.startswith('__') and not callable(value):
            params[name] = value
    return params


import asyncio, json
from typing import AsyncGenerator


async def fetch_remote(worker_addr: str):
    return "xxxxxxxxxxxxxx"


async def fetch_remote222(worker_addr: str):
    return {"error_code": 21, "content": "23dsds87"}

async def generate_completion(payload: Dict[str, Any], worker_addr: str):
    return await fetch_remote222(worker_addr + "/worker_generate")


async def get_worker_address(model_name: str) -> str:
    """
    Get worker address based on the requested model

    :param model_name: The worker's model name
    :return: Worker address from the controller
    :raises: :class:`ValueError`: No available worker for requested model
    """
    worker_addr = await fetch_remote("/get_worker_address")

    # No available worker
    if worker_addr == "":
        raise ValueError(f"No available worker for {model_name}")
    return worker_addr


async def not_stream_chat_completion_special2(worker_addr, gen_params) -> AsyncGenerator[dict, None]:
    """Creates a completion for the chat message"""
    choices = []
    chat_completions = []
    for i in range(1):
        content = asyncio.create_task(generate_completion(gen_params, worker_addr))
        chat_completions.append(content)
    try:
        all_tasks = await asyncio.gather(*chat_completions)
    except Exception as e:
        yield {"error": 111}
        return
    for i, content in enumerate(all_tasks):
        if isinstance(content, str):
            content = json.loads(content)

        if content["error_code"] != 0:
            yield {"error": 111}
            return

    yield {"DATA": 111}


async def not_stream_chat_completion_special(worker_addr, gen_params) -> dict:
    """Creates a completion for the chat message"""
    choices = []
    chat_completions = []
    for i in range(1):
        content = asyncio.create_task(generate_completion(gen_params, worker_addr))
        chat_completions.append(content)
    try:
        all_tasks = await asyncio.gather(*chat_completions)
    except Exception as e:
        return {"error": 111}
    for i, content in enumerate(all_tasks):
        if isinstance(content, str):
            content = json.loads(content)

        if content["error_code"] != 0:
            return {"error": 111}

    return {"DATA": 111}


async def chat_iter33() -> AsyncGenerator[dict, None]:
    """Creates a completion for the chat message"""
    worker_addr = await get_worker_address("ds9843984398")

    res = await not_stream_chat_completion_special(worker_addr, {})

    yield res


async def sdsd(src_info: str = None):
    print("start" + "-" * 20)
    async for chunk in chat_iter33():
        # handle the chunk data here
        #chunk = await chunk
        print(chunk)
        print(type(chunk))
        print(json.dumps(chunk, ensure_ascii=False))
        if chunk.get("choices") is not None:
            # res.choices[0].delta.content
            yield json.dumps({"answer": chunk["choices"][0]["delta"]["content"]}, ensure_ascii=False)
        else:
            yield json.dumps(chunk, ensure_ascii=False)

    if src_info:
        yield json.dumps({"docs": src_info}, ensure_ascii=False)
    print("end" + "-" * 20)


async def coroutine_wrapper(async_gen, args):
    try:
        print(tuple([i async for i in async_gen(args)]))
    except ValueError:
        print(tuple([(i, j) async for i, j in async_gen(args)]))


if __name__ == "__main__":
    format_jinja2_prompt_tmpl(prompt="xxxxxdssd", inmpu="xsd23423")

    ddd = {"aaaa": AAAA("sss", "eee"), "bbbb": AAAA("3223", "445")}

    ccc = dict(ddd)

    ccc["eeee"] = AAAA("sss", "eee")
    ccc["aaaa"].aa = "384787437"

    import copy

    eee = copy.deepcopy(ddd)

    eee["eeee"] = AAAA("sss", "eee")
    eee["aaaa"].aa = "384787437"

    print(ddd)
    print(ccc)
    print(eee)
    print(props_with_(ddd["aaaa"]))

    # coro = sdsd()
    # loop = asyncio.get_event_loop()
    # task = asyncio.create_task(coro)
    #
    # loop.run_until_complete(task)
    # print('再看下运行情况：', task)
    # loop.close()

    # asyncio.run(sdsd())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    xrange_iterator_task = loop.create_task(coroutine_wrapper(sdsd, None))
    try:
        loop.run_until_complete(xrange_iterator_task)
    except KeyboardInterrupt:
        loop.stop()
    finally:
        loop.close()
