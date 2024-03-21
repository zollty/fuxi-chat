from langchain.vectorstores.faiss import FAISS
from langchain.docstore.in_memory import InMemoryDocstore
from langchain.schema import Document
import os
from langchain.schema import Document
from typing import List, Any, Union, Tuple
from langchain.embeddings.base import Embeddings

import threading
from fuxi.utils.runtime_conf import get_log_verbose, logger
from knowledge.kb_vs_cache import kb_cache_faiss_pool
from embeddings.embeddings_api import load_local_embeddings


if __name__ == "__main__":
    import time, random
    from pprint import pprint

    kb_names = ["vs1", "vs2", "vs3"]


    # for name in kb_names:
    #     memo_faiss_pool.load_vector_store(name)

    def worker(vs_name: str, name: str):
        vs_name = "samples"
        time.sleep(random.randint(1, 5))
        embeddings = load_local_embeddings()
        r = random.randint(1, 3)

        with kb_cache_faiss_pool.load_vector_store(vs_name).acquire(name) as vs:
            if r == 1:  # add docs
                ids = vs.add_texts([f"text added by {name}"], embeddings=embeddings)
                pprint(ids)
            elif r == 2:  # search docs
                docs = vs.similarity_search_with_score(f"{name}", k=3, score_threshold=1.0)
                pprint(docs)
        if r == 3:  # delete docs
            logger.warning(f"清除 {vs_name} by {name}")
            kb_cache_faiss_pool.get(vs_name).clear()


    threads = []
    for n in range(1, 30):
        t = threading.Thread(target=worker,
                             kwargs={"vs_name": random.choice(kb_names), "name": f"worker {n}"},
                             daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
