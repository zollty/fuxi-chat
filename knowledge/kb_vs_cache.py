from langchain.vectorstores.faiss import FAISS
from langchain.docstore.in_memory import InMemoryDocstore
from langchain.schema import Document
import os
from langchain.schema import Document
from typing import List, Any, Union, Tuple
from langchain.embeddings.base import Embeddings

from fuxi.utils.runtime_conf import get_log_verbose, logger
from embeddings.base import EmbeddingsFunAdapter
from vectorstores.config import CACHED_EMBEDDING_MODEL
from vectorstores.mem_cache.faiss_cache import ThreadSafeFaiss, FaissPool
from knowledge.config import CACHED_KB_VS_NUM, get_kb_vs_path
from embeddings.embeddings_api import online_embed_models, embedding_device, embeddings_pool


class KBFaissPool(FaissPool):
    def load_kb_embeddings(
            self,
            kb_name: str,
            embed_device: str = embedding_device(),
            default_embed_model: str = CACHED_EMBEDDING_MODEL,
    ) -> Embeddings:
        from knowledge.db.repository.knowledge_base_repository import get_kb_detail

        kb_detail = get_kb_detail(kb_name)
        embed_model = kb_detail.get("embed_model", default_embed_model)

        if embed_model in online_embed_models:
            return EmbeddingsFunAdapter(embed_model)
        else:
            return embeddings_pool.load_embeddings(model=embed_model, device=embed_device)

    def load_vector_store(
            self,
            kb_name: str,
            vector_name: str = None,
            create: bool = True,
            embed_model: str = CACHED_EMBEDDING_MODEL,
            embed_device: str = embedding_device(),
    ) -> ThreadSafeFaiss:
        self.atomic.acquire()
        vector_name = vector_name or embed_model
        cache = self.get((kb_name, vector_name))  # 用元组比拼接字符串好一些
        if cache is None:
            item = ThreadSafeFaiss((kb_name, vector_name), pool=self)
            self.set((kb_name, vector_name), item)
            with item.acquire(msg="初始化"):
                self.atomic.release()
                logger.info(f"loading vector store in '{kb_name}/vector_store/{vector_name}' from disk.")
                vs_path = get_kb_vs_path(kb_name, vector_name)

                if os.path.isfile(os.path.join(vs_path, "index.faiss")):
                    embeddings = self.load_kb_embeddings(kb_name=kb_name, embed_device=embed_device,
                                                         default_embed_model=embed_model)
                    vector_store = FAISS.load_local(vs_path, embeddings, normalize_L2=True,
                                                    distance_strategy="METRIC_INNER_PRODUCT")
                elif create:
                    # create an empty vector store
                    if not os.path.exists(vs_path):
                        os.makedirs(vs_path)
                    vector_store = self.new_vector_store(embed_model=embed_model, embed_device=embed_device)
                    vector_store.save_local(vs_path)
                else:
                    raise RuntimeError(f"knowledge base {kb_name} not exist.")
                item.obj = vector_store
                item.finish_loading()
        else:
            self.atomic.release()
        return self.get((kb_name, vector_name))


kb_cache_faiss_pool = KBFaissPool(cache_num=CACHED_KB_VS_NUM)
