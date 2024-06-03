import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
runtime_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__current_script_path)))
sys.path.append(runtime_root_dir)

from dynaconf import Dynaconf


def base_init_0(cfg: Dynaconf, log_level):

    host = cfg.get("agent.openai_api_server.host")
    port = cfg.get("agent.openai_api_server.port")
    if host == "localhost" or host == "127.0.0.1":
        host = "0.0.0.0"

    from jian.common.internet_tools_client import search_engine

    ret = search_engine("text2json")
    print(f"----------------------------ret: {ret}")


def init_api_server():
    import argparse
    from fuxi.utils.runtime_conf import get_runtime_root_dir, get_default_log_path

    print(get_runtime_root_dir())
    cfg = Dynaconf(
        envvar_prefix="JIAN",
        root_path=get_runtime_root_dir(),
        settings_files=['conf/llm_model.yml', 'conf/settings.yaml'],
    )
    import jian.common.base_config as bc
    bc.cfg = cfg

    log_level = cfg.get("agent.openai_api_server.log_level", "info")
    verbose = True if log_level == "debug" else False
    host = cfg.get("agent.openai_api_server.host", "0.0.0.0")
    port = cfg.get("agent.openai_api_server.port", 8000)

    parser = argparse.ArgumentParser(prog='FenghouAI',
                                     description='About FenghouAI-Chat API')
    parser.add_argument("--host", type=str, default=host)
    parser.add_argument("--port", type=int, default=port)
    parser.add_argument(
        "-v",
        "--verbose",
        help="增加log信息",
        dest="verbose",
        type=bool,
        default=verbose,
    )
    # 初始化消息
    args = parser.parse_args()
    host = args.host
    port = args.port
    if args.verbose:
        log_level = "debug"
        cfg["agent.openai_api_server.log_level"] = "debug"

    cfg["agent.openai_api_server.host"] = host
    cfg["agent.openai_api_server.port"] = port

    import fastchat.constants
    fastchat.constants.LOGDIR = get_default_log_path()

    # from fuxi.utils.fastapi_tool import set_httpx_config
    # set_httpx_config()

    base_init_0(cfg, log_level)


if __name__ == "__main__":
    init_api_server()
