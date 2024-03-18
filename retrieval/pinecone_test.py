from langchain.document_loaders import TextLoader
from langchain.embeddings import ModelScopeEmbeddings
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
import pinecone
import chardet
import os

# initialize connection to pinecone (get API key at app.pinecone.io)
api_key = os.getenv("PINECONE_API_KEY") or "9193be36-c259-4631-9506-89be1fd71ec1"
# find your environment next to the api key in pinecone console
env = os.getenv("PINECONE_ENVIRONMENT") or "gcp-starter"

pinecone.init(api_key=api_key, environment=env)
print(pinecone.whoami())

# 读取原始文档
raw_documents_sanguo = TextLoader('/ai/apps/Fuxi-Chatchat/knowledge_base/yby_bgelargezh/content/园博园参考资料.txt', encoding='utf-8').load()
raw_documents_xiyou = TextLoader('/ai/apps/Fuxi-Chatchat/knowledge_base/yby_bgelargezh/content/园博园介绍.txt', encoding='utf-8').load()
raw_documents_fw = TextLoader('/ai/apps/Fuxi-Chatchat/knowledge_base/yby_bgelargezh/content/园博园服务.txt', encoding='utf-8').load()

# 分割文档
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
documents_sanguo = text_splitter.split_documents(raw_documents_sanguo)
documents_xiyou = text_splitter.split_documents(raw_documents_xiyou)
documents_fw = text_splitter.split_documents(raw_documents_fw)
documents = documents_sanguo + documents_xiyou + documents_fw
print("documents nums:", documents.__len__())


# 生成向量（embedding）
# model_id = "/ai/models/nlp_corom_sentence-embedding_chinese-base"
model_id = "/ai/models/nlp_gte_sentence-embedding_chinese-large"
embeddings = ModelScopeEmbeddings(model_id=model_id)
model_name = "/ai/models/BAAI_bge-large-zh-v1.5"
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': True} # set True to compute cosine similarity
embeddings1 = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
    query_instruction="为这个句子生成表示以用于检索相关文章："
)
embeddings2 = HuggingFaceBgeEmbeddings(
    model_name= "/ai/models/moka-ai_m3e-large", # "/ai/models/BAAI_bge-reranker-large", # "/ai/models/text2vec-bge-large-chinese",
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

index_name = "yby"
if index_name not in pinecone.list_indexes():
    # if does not exist, create index
    pinecone.create_index(
        index_name,
        dimension=1024,  # dimensionality of text-embedding-ada-002
        metric='cosine',
    )

# wait for index to be initialized
while not pinecone.describe_index(index_name).status['ready']:
    time.sleep(1)
#index = pinecone.Index(index_name)
index = pinecone.Index(index_name)
print(index.describe_index_stats())

# Now we upsert the data to Pinecone:
#index.upsert_from_dataframe(documents, batch_size=30)
#print(index.describe_index_stats())


# Create a unique namespace for the file
namespace_name = "Default"

# first
#db = Pinecone.from_documents(documents, embedding=embeddings, index_name=index_name, namespace=namespace_name)
# later      
db = Pinecone.from_existing_index(index_name=index_name, embedding=embeddings, namespace=namespace_name)


# db = Pinecone(index, embedding=embeddings)

# 检索
query = "白蛇娘子"
query2 = "美国"
query1 = "照壁"
docs = db.similarity_search(query, k=5)

# 打印结果
for doc in docs:
    print("===================================================")
    print("metadata:", doc.metadata)
    print("page_content:", doc.page_content)
