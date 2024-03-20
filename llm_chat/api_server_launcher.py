import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
RUNTIME_ROOT_DIR = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(RUNTIME_ROOT_DIR)

from dynaconf import Dynaconf


def mount_more_routes(app):
    from llm_chat.api import mount_app_routes
    mount_app_routes(app)


def call_controller_to_init(cfg: Dynaconf, app):
    from common.llm_controller_client import init_server_config
    init_server_config()

    from llm_chat.config import init_config
    init_config()


def base_init_1(cfg: Dynaconf):
    import fastchat
    from fastapi.middleware.cors import CORSMiddleware
    from common.fastapi_tool import set_httpx_config, MakeFastAPIOffline
    from fastchat.serve.openai_api_server import app

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
    app_settings.api_keys = cfg.get("llm.openai_api_server.api_keys", "")

    app = base_init_1(cfg)
    call_controller_to_init(cfg, app)
    mount_more_routes(app)

    # with open(RUNTIME_ROOT_DIR + '/logs/start_info.txt', 'a') as f:
    #     f.write(f"    FenghouAI OpeanAI API Server (fastchat): http://{host}:{port}\n")

    host = cfg.get("llm.openai_api_server.host")
    port = cfg.get("llm.openai_api_server.port")
    if host == "localhost" or host == "127.0.0.1":
        host = "0.0.0.0"

    from common.fastapi_tool import run_api
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
    from common.utils import RUNTIME_ROOT_DIR, DEFAULT_LOG_PATH

    print(RUNTIME_ROOT_DIR)
    cfg = Dynaconf(
        envvar_prefix="FUXI",
        root_path=RUNTIME_ROOT_DIR,
        settings_files=['conf_llm_model.yml', 'settings.yaml'],
    )

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
    fastchat.constants.LOGDIR = DEFAULT_LOG_PATH

    base_init_0(cfg, log_level)


if __name__ == "__main__":
    init_api_server()
