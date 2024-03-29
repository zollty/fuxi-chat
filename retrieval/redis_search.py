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
import redis
from redis.commands.search.field import (
    NumericField,
    TagField,
    NumericField,
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


def create_and_run_index(client: redis.Redis, kb_name: str):
    s = get_short_url(kb_name)
    prefix = "f:" + s
    name = "doc:" + s

    schema = (
        NumericField("nid"),
        TagField("key"),
        TagField("src"),
        TextField("doc"),
    )

    definition = IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)
    res = client.ft(name).create_index(
        fields=schema, definition=definition
    )
    print(res)
    # >>> 'OK'

    if res == "OK":
        return True
    return False


def insert_doc(client: redis.Redis, docs: List[DocSchema], kb_name: str, use_id: str = None):
    s = get_short_url(kb_name)
    prefix = "f:" + s
    name = "doc:" + s

    pipeline = client.pipeline()
    ft = pipeline.ft(name)
    for i, t in enumerate(docs, start=1):
        redis_key = f"{prefix}:{i}"
        # pipeline.hset(redis_key, "doc", doc.doc)
        # pipeline.hset(redis_key, "key", doc.key)
        # pipeline.hset(redis_key, "src", doc.src)

        fields = {"doc": t.doc,
                  "nid": i,
                  "key": t.key,
                  "src": t.src}
        ft.add_document(redis_key, language="chinese", **fields)
        # pipeline.hset(redis_key, mapping={"doc": t.doc,
        #                                   "key": t.key,
        #                                   "src": t.src})

    res = pipeline.execute()
    print(res)


def retrieve_docs(client: redis.Redis, query: str, kb_name: str):
    s = get_short_url(kb_name)
    name = "doc:" + s
    # query = Query(f"@doc:%%{query}%%")
    # res = client.ft(name).search(query, {"language": "chinese"}).docs
    # print(res)
    res = client.execute_command('FT.SEARCH', name, f"@doc:{query}", "language", "chinese")
    # print(res)
    return res


def list_to_dict(ls):
    b = {}
    for i in range(0, len(ls), 2):
        b[ls[i]] = ls[i + 1]
    return b


if __name__ == '__main__':

    client = redis.Redis(host="127.0.0.1", port=6389, decode_responses=True)

    res = client.ping()
    print(res)
    # >>> True

    kb_name = "yby"
    # create_and_run_index(client, kb_name)

    # insert_doc

    results = retrieve_docs(client, "江苏扬州园", kb_name)

    for x in results:
        print(list_to_dict(x))
