import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
RUNTIME_ROOT_DIR = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(RUNTIME_ROOT_DIR)

if __name__ == "__main__":
    from pprint import pprint
    from tools.document_loaders_helper import load_file_docs
    from tools.text_splitter_helper import do_split_docs

    docs = load_file_docs(
        "/ai/apps/misc/test_files/附件2：爱康国宾体检注意事项.txt",
        filename="附件2：爱康国宾体检注意事项.txt",
    )
    # kb_file.text_splitter_name = "RecursiveCharacterTextSplitter"
    pprint(docs[0])
    pprint(docs[-1])

    docs = do_split_docs(docs)
    pprint(docs[0])
    pprint(docs[-1])
