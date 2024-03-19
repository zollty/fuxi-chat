import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
RUNTIME_ROOT_DIR = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(RUNTIME_ROOT_DIR)

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

def format_jinja2_prompt_tmpl(prompt: str=None, tmpl_type: str=None, tmpl_name: str=None, **kwargs):
    print(f"-----prompt: {prompt}")
    print(f"-----prompt: {tmpl_type}")
    print(f"-----prompt: {tmpl_name}")
    print(f"-----prompt: {kwargs}")

if __name__ == "__main__":
    from common.conf import Cfg
    from common.utils import RUNTIME_ROOT_DIR
    import re

    format_jinja2_prompt_tmpl(prompt="xxxxxdssd", inmpu="xsd23423")


