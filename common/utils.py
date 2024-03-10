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
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
RUNTIME_ROOT_DIR = os.path.dirname(os.path.dirname(__current_script_path))

# 日志存储路径
DEFAULT_LOG_PATH = os.path.join(RUNTIME_ROOT_DIR, "logs")
if not os.path.exists(DEFAULT_LOG_PATH):
    os.mkdir(DEFAULT_LOG_PATH)

import tempfile
import shutil

# 临时文件目录，主要用于文件对话
BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), "fuxi_ai")
try:
    shutil.rmtree(BASE_TEMP_DIR)
except Exception:
    pass
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

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


# NLTK模型分词模型，例如 NLTKTextSplitter，SpacyTextSplitter，配置 nltk 模型存储路径
# import nltk
# NLTK_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nltk_data")
# nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path

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


def torch_gc():
    try:
        import torch
        if torch.cuda.is_available():
            # with torch.cuda.device(DEVICE):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        elif torch.backends.mps.is_available():
            try:
                from torch.mps import empty_cache
                empty_cache()
            except Exception as e:
                msg = ("如果您使用的是 macOS 建议将 pytorch 版本升级至 2.0.0 或更高版本，"
                       "以支持及时清理 torch 产生的内存占用。")
                logger.error(f'{e.__class__.__name__}: {msg}',
                             exc_info=e if LOG_VERBOSE else None)
    except Exception:
        ...


def get_temp_dir(id: str = None) -> Tuple[str, str]:
    """
    创建一个临时目录，返回（路径，文件夹名称）
    """
    import tempfile

    if id is not None:  # 如果指定的临时目录已存在，直接返回
        path = os.path.join(BASE_TEMP_DIR, id)
        if os.path.isdir(path):
            return path, id

    path = tempfile.mkdtemp(dir=BASE_TEMP_DIR)
    return path, os.path.basename(path)


from concurrent.futures import ThreadPoolExecutor, as_completed


def run_in_thread_pool(
        func: Callable,
        params: List[Dict] = [],
) -> Generator:
    """
    在线程池中批量运行任务，并将运行结果以生成器的形式返回。
    请确保任务中的所有操作是线程安全的，任务函数请全部使用关键字参数。
    """
    tasks = []
    with ThreadPoolExecutor() as pool:
        for kwargs in params:
            thread = pool.submit(func, **kwargs)
            tasks.append(thread)

        for obj in as_completed(tasks):  # TODO: Ctrl+c无法停止
            yield obj.result()
