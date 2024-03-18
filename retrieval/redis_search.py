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


from redisvl.index import SearchIndex
from redisvl.utils.vectorize import HFTextVectorizer
from redisvl.query import VectorQuery

import json
import time

import numpy as np
import redis
from redis.commands.search.field import (
    NumericField,
    TagField,
    TextField,
    VectorField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

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


def create_schema(client, kb_name: str):
    s = get_short_url(kb_name)
    prefix = "r:" + s
    name = "doc:" + s

    schema = (
        TextField("doc"),
        TagField("key"),
        TagField("src"),
    )

    definition = IndexDefinition(prefix=[prefix], index_type=IndexType.JSON)
    res = client.ft(name).create_index(
        fields=schema, definition=definition
    )
    print(res)
    # >>> 'OK'
    return True


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


def retrieve_docs(client, query: str, kb_name: str):
    s = get_short_url(kb_name)
    name = "doc:" + s
    query = Query(f"@doc:({query})")
    res = client.ft(name).search(query).docs
    print(res)
    return res


if __name__ == '__main__':

    client = redis.Redis(host="127.0.0.1", port=6389, decode_responses=True)

    res = client.ping()
    print(res)
    # >>> True

    kb_name = "yby"
    create_schema(client, kb_name)

    results = retrieve_docs(client, "江苏扬州园", kb_name)

    for x in results:
        print(x)
