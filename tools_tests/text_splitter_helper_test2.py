import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
get_runtime_root_dir() = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(get_runtime_root_dir())


if __name__ == "__main__":
    from pprint import pprint
    import importlib

    from tools.text_splitter_helper import do_split_docs

    from langchain.docstore.document import Document

    docs = []
#     docs.append(Document(page_content="""
#     镇江园根据展园的用地条件，采用“以小见大”的手法，通过地形塑造，建筑、树木、花卉、铺地的组合，营造“水漫金山”的意境。金山位于江苏镇江市，有“神话山”之称。“金山”为土石堆叠而成，坡上满种黄色花卉植物，寓意“金山”。 而位于山顶上的金山寺相传是当年法海和尚藏匿许仙的地方。
# 　　在“水漫金山寺”的神话故事中，白蛇娘子水漫金山，法海搬来天兵天将来对付白蛇，将白蛇压在雷峰塔下。除《白蛇传》“水漫金山寺”的神话故事外，《说岳全传》《水浒》对金山都做过细腻的描写；清代皇帝康熙、乾隆多次南巡都住过金山；历代诗人、书法家、名人雅士，如白居易、李白、苏东坡、王安石、范仲淹、赵孟頫、王阳明等都曾登临观景。
#     """, metadata={}))
    docs.append(Document(page_content="""
        重庆园博园资源体量巨大，其中地文景观、水域风光、生物景观、天象与气候景观、遗址遗迹、建筑与设施、旅游商品、人文活动8大主类齐全、包含23个亚类，65个基本类型和109个资源单体。园区以传统风、古典风、经典风为设计理念，根据现状地形因地制宜地布局为“山拥水环、一轴两星一环”的格局，形成入口区、景园区、展园区和生态区四大分区。拥有云顶、卧龙石、悠园等14个园区共26处特色景点，主展馆、巴渝园、龙景书院、重云塔、风雨廊桥5大主题建筑及40余座亭廊，7座古典石桥，12.8公里环湖路，25.2公里步游道。园区共有国内外134个城市、单位和个人参与建成的10大展区共127个展园，充分地展示了中外园林精髓和不同城市园林景观的地域特色。园区动植物种类丰富，景观特色突出，园内共有植物128 科，359属，660种，其中蕨类植物5科，5属，5种；裸子植物9科，17属，35种；被子植物114科，337属，620种。尤其珍贵的是，重庆园博园内有1000余株植物来自三峡库区，这些库区植物更是三峡库区生态系统研究特别是植被生态系统演变、三峡库区生物多样性变化和保护研究的天然样本。目前园内共发现野生动物300余种，其中鸟类超过150种，在园内观察到的红腹鹰、红翅绿鸠、火冠雀、灰背伯劳和普通朱雀等鸟在重庆极为罕见，园内共有9种国家II级重点保护野生动物。
        """, metadata={}))

    docs = do_split_docs(docs, text_splitter_name="ChineseRecursiveTextSplitter", chunk_size = 200,
        chunk_overlap = 0)
    # for doc in docs:
    #     print(doc.metadata)
    #     pprint(doc)
    # pprint(docs[0])
    # pprint(docs[-1])

    # document_loaders_module = importlib.import_module('tools.document_loaders')
    # FilteredCSVLoader = getattr(document_loaders_module, "FilteredCSVLoader")
    #
    # doc_loader = FilteredCSVLoader("D:/__SYNC3/BaiduSyncdisk/misc/test_files/langchain-ChatGLM_closed.csv",
    #                                columns_to_read=["title","file","url","detail","id"],
    #                                encoding="utf-8")
    #
    # docs = doc_loader.load()
    # pprint(docs[0])
    # pprint(docs[-1])
    #
    # from tools.document_loaders_helper import load_file_docs
    #
    # docs = load_file_docs(
    #     "D:/__SYNC3/BaiduSyncdisk/misc/test_files/附件2：爱康国宾体检注意事项.txt",
    #     filename="附件2：爱康国宾体检注意事项.txt",
    # )
    # # kb_file.text_splitter_name = "RecursiveCharacterTextSplitter"
    # pprint(docs[0])
    # pprint(docs[-1])
