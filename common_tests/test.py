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

def string_args(args, args_list):
    args_str = ""
    for key, value in args._get_kwargs():
        key = key.replace("_", "-")
        if key not in args_list:
            continue

        key = key.split("-")[-1] if re.search("port|host", key) else key
        if not value:
            pass
        # 1==True ->  True
        elif isinstance(value, bool) and value == True:
            args_str += f" --{key} "
        elif (
            isinstance(value, list)
            or isinstance(value, tuple)
            or isinstance(value, set)
        ):
            value = " ".join(value)
            args_str += f" --{key} {value} "
        else:
            args_str += f" --{key} {value} "

    return args_str


if __name__ == "__main__":
    from common.conf import Cfg
    from common.utils import RUNTIME_ROOT_DIR
    import re
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--verbose",
        help="增加log信息",
        dest="verbose", type=bool, default=False
    )
    parser.add_argument(
        "-cp",
        "--controller-config-path",
        help="custom controller path/openai_api servers",
        default="xxx",
    )
    parser.add_argument(
        "-m",
        "--model",
        nargs="+",
        type=str,
        help="custom default start models",
        dest="model",
        default="x4343",
    )

    args = parser.parse_args()

    # args = argparse.Namespace(
    #     **vars(args),
    #     **{"controller-address": f"http://{args.controller_host}:{args.controller_port}"},
    # )

    controller_args = ["controller_config_path", "verbose", "model"]
    controller_str_args = string_args(args, controller_args)
    print(" xxxx " + controller_str_args)

    ret = "xxxx@123".split("@2")
    print(len(ret))

    def xx(params: Dict = {}):
        print(params["bbb"])
        if "aaa" in params:
            for kwargs, c in params.items():
                print(kwargs)
            print("-------------------------")
    xx({"aaa": 123, "bbb": 23453})


