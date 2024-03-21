import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
get_runtime_root_dir() = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(get_runtime_root_dir())

toml_str = """
[embed]
device = "cuda"

[[players]]
name = "Lehtinen"
number = 26

[[players]]
name = "Numminen"
number = 27
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class KbConfig:
    # 默认使用的知识库
    DEFAULT_KNOWLEDGE_BASE = "samples"
    # kbs_config: Dict[str, Dict] = field(default_factory=lambda:
    kbs_config = {
        "faiss": {
        },
        "milvus": {
            "host": "127.0.0.1",
            "port": "19530",
            "user": "",
            "password": "",
            "secure": False,
        },
        "zilliz": {
            "host": "in01-a7ce524e41e3935.ali-cn-hangzhou.vectordb.zilliz.com.cn",
            "port": "19530",
            "user": "",
            "password": "",
            "secure": True,
        },
        "pg": {
            "connection_uri": "postgresql://postgres:postgres@127.0.0.1:5432/fenghou-ai",
        },

        "es": {
            "host": "127.0.0.1",
            "port": "9200",
            "index_name": "test_index",
            "user": "",
            "password": ""
        },
        "milvus_kwargs": {
            "search_params": {"metric_type": "L2"},  # 在此处增加search_params
            "index_params": {"metric_type": "L2", "index_type": "HNSW"}  # 在此处增加index_params
        },
        "chromadb": {}
    }


if __name__ == "__main__":
    from jian.common.conf import Cfg
    from jian.common.utils import get_runtime_root_dir()

    print(get_runtime_root_dir())
    # cfg = Cfg(get_runtime_root_dir() + "/conf_rerank_test.toml")
    # print(cfg.get("reranker.model.bge-reranker-large"))
    # print(cfg.get("embed.device"))
    #
    # print("---------222------------------")
    # cfg = Cfg(toml_str, False, None)
    # print(cfg.get("players[1].name"))


    # print(cfg.get("servers.alpha.ip"))

    def props(obj):
        pr = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value):
                pr[name] = value
        return pr


    # from embed.server_config import ServerConfig
    # conf = props(ServerConfig)
    # print(conf)
    from omegaconf import OmegaConf

    # conf = OmegaConf.structured(KbConfig)
    # print(OmegaConf.to_yaml(conf))
    conf = props(KbConfig)
    print(conf)
    conf = OmegaConf.create(conf)
    print(conf.kbs_config)

    print(get_runtime_root_dir())
    conf = OmegaConf.load(get_runtime_root_dir() + '/conf/llm_model.yml')
    print(conf.llm.model_cfg)
    for mc in conf["llm"]["model_cfg"].items():
        print(mc)

    from dynaconf import Dynaconf

    cfg = Dynaconf(
        envvar_prefix="FUXI",
        root_path=get_runtime_root_dir(),
        settings_files=['conf/llm_model.yml', 'conf/settings.yaml'],
    )

    print("===================================")
    print(cfg["test-aa.key-bb"])
    print(cfg.get("test-aa.key-bb"))
    print(cfg.get("test-aa.key-bb-cc", cfg.get("llm.worker.base.controller_addr")))
    for k, v in cfg.items():
        print(k, v)

    tgf = cfg.get("llm.worker.vllm")
    tgf["cc"] = "dsjhdhjsjhds"
    print(tgf)
    print(cfg.get("llm.worker.vllm"))

    tfg1 = cfg.get("llm.worker.base") + {}
    print("-------------------------")
    tfg1["cc"] = "xxxxxxxxx"
    print(getattr(tfg1, "conv_template"))

    print(cfg.get("llm.worker.base"))
    print(cfg.get("llm.worker.vllm"))

    model_name = "Qwen1.5-7B-Chat"
    model_worker_config = {"model_name": model_name}
    if model_name == "langchain_model":
        model_worker_config["langchain_model"] = True
    else:
        model_worker_config = cfg.get("llm.model_cfg")[model_name] + model_worker_config

    model_name = model_worker_config.get("model_name")
    start_port = cfg.get("llm.worker.start_port")
    worker_port = model_worker_config.get("port")
    if not worker_port:
        worker_port = start_port
        model_worker_config["worker_port"] = worker_port

    host = cfg.get("llm.worker.host")
    worker_addr = f"http://{host}:{worker_port}"
    model_worker_config["base"]["worker_addr"] = worker_addr
    model_worker_config["base"]["model_path"] = model_worker_config.get("path")
    model_worker_config["base"]["model_names"] = [model_worker_config.get("model_name")]
    print("--------------------------")
    print(model_worker_config.get("base"))

    vllm_args = cfg.get("llm.worker.base") + cfg.get("llm.worker.vllm") + model_worker_config.get("base")
    if model_worker_config.get("vllm"):
        vllm_args = vllm_args + model_worker_config.get("vllm")

    vllm_args["tokenizer"] = vllm_args["model_path"]

    print(vllm_args)
    if vllm_args.get("gpus"):
        if not vllm_args.get("num_gpus"):
            vllm_args["num_gpus"] = len(vllm_args.gpus.split(','))
        print(len(vllm_args.gpus.split(",")), vllm_args.num_gpus)
        if len(vllm_args.gpus.split(",")) < vllm_args.num_gpus:
            raise ValueError(
                f"Larger --num-gpus ({vllm_args.num_gpus}) than --gpus {vllm_args.gpus}!"
            )

