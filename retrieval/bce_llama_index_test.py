# We provide the advanced preproc tokenization for reranking.
from BCEmbedding.tools.llama_index import BCERerank

import os
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index import VectorStoreIndex, ServiceContext, SimpleDirectoryReader
from llama_index.node_parser import SimpleNodeParser
from llama_index.llms import OpenAI
from llama_index.retrievers import VectorIndexRetriever

OPENAI_BASE_URL="http://127.0.0.1:20000/v1"
OPENAI_API_KEY = "EMPTY"

# 读取原始文档
raw_documents_sanguo = SimpleDirectoryReader(input_files=['/ai/apps/data/园博园参考资料.txt']).load_data()
raw_documents_xiyou = SimpleDirectoryReader(input_files=['/ai/apps/data/园博园介绍.txt']).load_data()
raw_documents_fw = SimpleDirectoryReader(input_files=['/ai/apps/data/园博园服务.txt']).load_data()
documents = raw_documents_sanguo + raw_documents_xiyou + raw_documents_fw

# init embedding model and reranker model
embed_args = {'model_name': '/ai/models/bce-embedding-base_v1', 'max_length': 512, 'embed_batch_size': 32, 'device': 'cuda:0'}
embed_model = HuggingFaceEmbedding(**embed_args)

reranker_args = {'model': '/ai/models/bce-reranker-base_v1', 'top_n': 5, 'device': 'cuda:1'}
reranker_model = BCERerank(**reranker_args)

# example #1. extract embeddings
query = 'apples'
passages = [
        'I like apples',
        'I like oranges',
        'Apples and oranges are fruits'
    ]
query_embedding = embed_model.get_query_embedding(query)
passages_embeddings = embed_model.get_text_embedding_batch(passages)

# example #2. rag example
llm = OpenAI(model='Qwen1.5-7B-Chat', api_key=OPENAI_API_KEY, api_base=OPENAI_BASE_URL)
service_context = ServiceContext.from_defaults(llm=llm, embed_model=embed_model)


node_parser = SimpleNodeParser.from_defaults(chunk_size=400, chunk_overlap=80)
nodes = node_parser.get_nodes_from_documents(documents[0:36])
index = VectorStoreIndex(nodes, service_context=service_context)

query = "What is Llama 2?"

# example #2.1. retrieval with EmbeddingModel and RerankerModel
vector_retriever = VectorIndexRetriever(index=index, similarity_top_k=10, service_context=service_context)
retrieval_by_embedding = vector_retriever.retrieve(query)
retrieval_by_reranker = reranker_model.postprocess_nodes(retrieval_by_embedding, query_str=query)

# example #2.2. query with EmbeddingModel and RerankerModel
query_engine = index.as_query_engine(node_postprocessors=[reranker_model])
query_response = query_engine.query(query)