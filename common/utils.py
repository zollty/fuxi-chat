from typing import (
    TYPE_CHECKING,
    Literal,
    Optional,
    Callable,
    Generator,
    Dict,
    Any,
    Awaitable,
    Union,
    Tuple
)

import os
# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
RUNTIME_ROOT_DIR = os.path.dirname(os.path.dirname(__current_script_path))

# 日志存储路径
DEFAULT_LOG_PATH = os.path.join(RUNTIME_ROOT_DIR, "logs")
if not os.path.exists(DEFAULT_LOG_PATH):
    os.mkdir(DEFAULT_LOG_PATH)

VERSION = "1.0.0"
# API 是否开启跨域，默认为False，如果需要开启，请设置为True
# is open cross domain
OPEN_CROSS_DOMAIN = True
# SSL_KEYFILE = os.environ["SSL_KEYFILE"]
# SSL_CERTFILE = os.environ["SSL_CERTFILE"]

import logging

# 日志格式
LOG_FORMAT = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
# 是否显示详细日志
LOG_VERBOSE = False
# 通常情况下不需要更改以下内容

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format=LOG_FORMAT)

def detect_device() -> Literal["cuda", "mps", "cpu"]:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except:
        pass
    return "cpu"

