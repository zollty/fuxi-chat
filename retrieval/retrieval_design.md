

# 核心设计


### 1、Redis向量库

结构如下：

```python
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
```
这个设计是通用的、灵活的：

- 其中，nid和key对应的都是文档在某个src下的唯一ID/KEY，可以根据不同场景二选一。而src，是一个标签，可以表示文档的上级来源（例如某某文件，src就是文件名）。

- nid是数字类型，是由数据库ID或者唯一ID生成器，来生成的。key也类似，但为string类型，例如文档的MD5值或者shortURL、gitcommitID算法得到的值。

- doc字段，存储文档原文内容，也可以留空（不保存原文，原文在其他数据库中保存，那么这里可以留空或者存一个MD5/SHA值也行）。


### 2、向量值（embed字段，存储向量数组）
为了提高向量查询精度，embedding文本长度默认设置短一点，例如100~250，然后通过前后文映射成一个长文本段落（例如映射成单段3000字）。

这就需要，文档分段存储的ID，与向量库的向量nid/key做一个映射。这个可以借助src字段，存储文档分段的ID即可解决。

需要注意是短文本处于长文本段落边界的问题，例如处于最末位，这时可能下一个段落与当前短文本相关，所以保险起见，是将一个短文本，对应的长文本id扩展到id-1、id、id+1三个段落。然后将返回的数据，从映射文本位置前后各取一定长度（例如1500）


### 3、全文检索及文本存储




