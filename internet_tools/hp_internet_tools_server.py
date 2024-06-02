import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
runtime_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__current_script_path)))
sys.path.append(runtime_root_dir)

from dynaconf import Dynaconf

def base_init_0(cfg: Dynaconf, log_level):
    from fuxi.utils.fastapi_tool import run_api, create_app_without_httpx
    from jian.internet_tools.api import mount_app_routes

    host = cfg.get("agent.internet_tools_server.host")
    port = cfg.get("agent.internet_tools_server.port")
    if host == "localhost" or host == "127.0.0.1":
        host = "0.0.0.0"

    app = create_app_without_httpx([mount_app_routes], version="1.0.0", title="FenghouAI internet_tools API Server")

    run_api(
        app,
        host=host,
        port=port,
        log_level=log_level,
        ssl_keyfile=cfg.get("agent.internet_tools_server.ssl_keyfile", cfg.get("root.ssl_keyfile", None)),
        ssl_certfile=cfg.get("agent.internet_tools_server.ssl_certfile", cfg.get("root.ssl_certfile", None)),
    )


def init_api_server():
    import argparse
    from fuxi.utils.runtime_conf import get_runtime_root_dir

    print(get_runtime_root_dir())
    cfg = Dynaconf(
        envvar_prefix="JIAN",
        root_path=get_runtime_root_dir(),
        settings_files=['conf/llm_model.yml', 'conf/settings.yaml'],
    )
    import jian.common.base_config as bc
    bc.cfg = cfg

    log_level = cfg.get("agent.internet_tools_server.log_level", "info")
    verbose = True if log_level == "debug" else False
    host = cfg.get("agent.internet_tools_server.host", "0.0.0.0")
    port = cfg.get("agent.internet_tools_server.port", 8111)

    parser = argparse.ArgumentParser(prog='FenghouAI',
                                     description='About FenghouAI-internet_tools API')
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
        cfg["agent.internet_tools_server.log_level"] = "debug"

    cfg["agent.internet_tools_server.host"] = host
    cfg["agent.internet_tools_server.port"] = port

    # from fuxi.utils.fastapi_tool import set_httpx_config
    # set_httpx_config()

    base_init_0(cfg, log_level)


if __name__ == "__main__":
    init_api_server()
