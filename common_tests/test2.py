import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
get_runtime_root_dir() = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(get_runtime_root_dir())

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

def format_jinja2_prompt_tmpl(prompt: str=None, tmpl_type: str=None, tmpl_name: str=None, **kwargs):
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


if __name__ == "__main__":
    from jian.common.conf import Cfg
    from jian.common.utils import get_runtime_root_dir()
    import re

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



