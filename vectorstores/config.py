import os
from typing import List, Literal, Optional, Dict
from common.utils import detect_device

# 知识库匹配向量数量
VECTOR_SEARCH_TOP_K = 100

# 知识库匹配的距离阈值，一般取值范围在0-1之间，SCORE越小，距离越小从而相关度越高。
# 但有用户报告遇到过匹配分值超过1的情况，为了兼容性默认设为1，在WEBUI中调整范围为0-2
SCORE_THRESHOLD = 1.0

# 缓存临时向量库数量（针对FAISS），用于文件对话
CACHED_MEMO_VS_NUM = 10


# 选用的 Embedding 名称
CACHED_EMBEDDING_MODEL = "bge-large-zh-v1.5"


