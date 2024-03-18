import time
from typing import Any, List, Optional, Dict

import hashlib


def get_short_url(url):
    md5 = hashlib.md5(url.encode('utf-8')).hexdigest()
    # 将32位的md5哈希值转化为10进制数
    num = int(md5, 16)
    # 将10进制数转化为62进制数
    base = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    short_url = ''
    while num > 0:
        short_url += base[num % 62]
        num //= 62
    # 短链接的长度为6位
    return short_url[:6]


# from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex
from redisvl.utils.vectorize import HFTextVectorizer
from redisvl.query import VectorQuery

DEFAULT_EMBED_PATH = "/ai/models/bce-embedding-base_v1"
DEFAULT_EMBED_DIMS = 768
REDIS_URL = "redis://127.0.0.1:6389"
EMBED_BATCH_SIZE = 16
DEFAULT_VEC_NUM = 20


class DocSchema:
    nid: int = 0
    key: str = ""
    src: str = ""
    doc: str

    def __init__(self, doc: str, src: str = "", key: str = "", nid: int = 0):
        self.nid = nid
        self.key = key
        self.src = src
        self.doc = doc


def create_schema(kb_name: str, dims: int = DEFAULT_EMBED_DIMS):
    s = get_short_url(kb_name)
    prefix = "r:" + s
    name = "idx:" + s

    schema = {
        "index": {
            "name": name,
            "prefix": prefix,
        },
        "fields": [
            {"name": "nid", "type": "numeric"},  # id，和key二选一即可
            {"name": "key", "type": "tag"},  # 唯一key，和nid二选一即可
            {"name": "src", "type": "tag"},  # 来源，例如文件名
            {"name": "doc", "type": "text"},
            {
                "name": "embed",
                "type": "vector",
                "attrs": {
                    "dims": dims,
                    "distance_metric": "cosine",
                    "algorithm": "flat",
                    "datatype": "float32"
                }
            }
        ]
    }

    return schema


def create_and_run_index(kb_name: str, dims: int = DEFAULT_EMBED_DIMS, redis_url: str = REDIS_URL):
    schema = create_schema(kb_name, dims)
    index = SearchIndex.from_dict(schema)
    # connect to local redis instance
    index.connect(redis_url)

    # create the index (no data yet)
    index.create(overwrite=True)
    return index


def insert_doc(docs: List[DocSchema], kb_name: str, use_id: str = None, redis_url: str = REDIS_URL,
               embedd_path: str = DEFAULT_EMBED_PATH):
    sentences = [t.doc for t in docs]

    # Embedding a single text
    vectorizer = HFTextVectorizer(model=embedd_path)
    # Embedding a batch of texts
    embeddings = vectorizer.embed_many(sentences, batch_size=EMBED_BATCH_SIZE, as_buffer=True)
    dims = len(embeddings[0])

    schema = create_schema(kb_name, dims)
    index = SearchIndex.from_dict(schema)
    # connect to local redis instance
    index.connect(redis_url)  # "redis://127.0.0.1:6389"

    data = [{"doc": t.doc,
             "key": t.key,
             "nid": t.nid,
             "src": t.src,
             "embed": v}
            for t, v in zip(docs, embeddings)]

    # load装载数据
    if use_id:
        index.load(data, id_field=use_id)
    else:
        index.load(data)


def retrieve_docs(query: str, kb_name: str, top_k: int = DEFAULT_VEC_NUM, redis_url: str = REDIS_URL,
                  embedd_path: str = DEFAULT_EMBED_PATH):
    vectorizer = HFTextVectorizer(model=embedd_path)
    # use the HuggingFace vectorizer again to create a query embedding
    query_embedding = vectorizer.embed(query)
    dims = len(query_embedding)

    query = VectorQuery(
        vector=query_embedding,
        vector_field_name="embed",
        return_fields=["nid", "key", "doc", "src"],
        num_results=top_k
    )

    schema = create_schema(kb_name, dims)
    index = SearchIndex.from_dict(schema)
    # connect to local redis instance
    index.connect(redis_url)
    results = index.query(query)
    # for x in results:
    #     print(x["doc"], x["vector_distance"])

    return results


if __name__ == '__main__':

    kb_name = "vectorizers"
    create_and_run_index(kb_name)

    docs = [
        "That is a happy apple",
        "That is a happy person",
        "That is a happy dog",
        "Today is a sunny day"
    ]

    sentences = [DocSchema(doc, key=get_short_url(doc)) for doc in docs]

    insert_doc(sentences, kb_name, use_id="key")

    results = retrieve_docs("That is a happy cat", kb_name)

    for x in results:
        print(x["doc"], x["vector_distance"])
