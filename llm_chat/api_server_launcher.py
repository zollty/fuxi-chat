import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
runtime_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__current_script_path)))
sys.path.append(runtime_root_dir)

from dynaconf import Dynaconf


def mount_more_routes(app):
    from jian.llm_chat.api import mount_app_routes
    mount_app_routes(app)


def call_controller_to_init(cfg: Dynaconf, app):
    from jian.common.llm_controller_client import init_server_config
    init_server_config()

    from jian.llm_chat.config import init_config
    init_config()


def base_init_1(cfg: Dynaconf):
    import fastchat
    from fastapi.middleware.cors import CORSMiddleware
    from fastchat.serve.openai_api_server import app
    from fuxi.utils.fastapi_tool import set_httpx_config, MakeFastAPIOffline

    app.title = "风后AI-Chat API Server (兼容OpenAI API)"
    app.version = fastchat.__version__

    cross_domain = cfg.get("llm.openai_api_server.cross_domain", cfg.get("root.cross_domain", True))
    if cross_domain:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    set_httpx_config()

    MakeFastAPIOffline(app)

    return app


def base_init_0(cfg: Dynaconf, log_level):
    from fastchat.serve.openai_api_server import logger, app_settings

    logger.setLevel(log_level.upper())

    app_settings.controller_address = cfg.get("agent.controller.address")
    app_settings.api_keys = cfg.get("llm.controller.api_keys", "EMPTY")

    app = base_init_1(cfg)
    call_controller_to_init(cfg, app)
    mount_more_routes(app)

    # with open(get_runtime_root_dir() + '/logs/start_info.txt', 'a') as f:
    #     f.write(f"    FenghouAI OpeanAI API Server (fastchat): http://{host}:{port}\n")

    host = cfg.get("llm.openai_api_server.host")
    port = cfg.get("llm.openai_api_server.port")
    if host == "localhost" or host == "127.0.0.1":
        host = "0.0.0.0"

    from fuxi.utils.fastapi_tool import run_api
    run_api(
        app,
        host=host,
        port=port,
        log_level=log_level,
        ssl_keyfile=cfg.get("llm.openai_api_server.ssl_keyfile"),
        ssl_certfile=cfg.get("llm.openai_api_server.ssl_certfile"),
    )


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

    log_level = cfg.get("llm.openai_api_server.log_level", "info")
    host = cfg.get("llm.openai_api_server.host", "0.0.0.0")
    port = cfg.get("llm.openai_api_server.port", 8000)

    parser = argparse.ArgumentParser(prog='FenghouAI',
                                     description='About FenghouAI-Chat API')
    parser.add_argument("--host", type=str, default=host)
    parser.add_argument("--port", type=int, default=port)
    # 初始化消息
    args = parser.parse_args()
    host = args.host
    port = args.port

    cfg["llm.openai_api_server.host"] = host
    cfg["llm.openai_api_server.port"] = port

    import fastchat.constants
    fastchat.constants.LOGDIR = get_default_log_path()

    base_init_0(cfg, log_level)


if __name__ == "__main__":
    init_api_server()
