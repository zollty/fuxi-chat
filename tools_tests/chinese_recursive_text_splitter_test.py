import sys
import os

# 获取当前脚本的绝对路径
__current_script_path = os.path.abspath(__file__)
# 将项目根目录添加到sys.path
get_runtime_root_dir = os.path.dirname(os.path.dirname(__current_script_path))
sys.path.append(get_runtime_root_dir)

if __name__ == "__main__":
    from tools.text_splitter import ChineseRecursiveTextSplitter

    text_splitter = ChineseRecursiveTextSplitter(
        keep_separator=True,
        is_separator_regex=True,
        chunk_size=100,
        chunk_overlap=0
    )
    ls = [
        """1.园博园建筑格局
重庆园博园内设有入口主题展示区、传统园林集锦区、国际园林展示区、现代园林展示区、三峡生态展示区和景观生态体验区等六大展区，建了5.1万平方米景观建筑和26个景区景点，荟萃了国外21个国家和地区的30个城市以及国内80多个城市的经典园林景观。园博园按功能设立入口区、景园区、展园区和生态区四大部分。
入口区：主要包括主入口、东次入口、西次入口三个。
景园区：位于平地展园区与山顶生态区之间的风景坡地，按照一轴两星一环”的结构规划，设置候鸟湿地、卧龙石、双亭瀑布、龙景书院、湿地花溪、青山茅庐、枫香秋停、荟萃园、云顶揽胜、悠园、巴渝园、环湖六景、风雨廊桥、莫纹世界等景区、景点。
展园区：根据规划设计的用地要求，利用园中较为平坦的区域安排城市展园，其中包括北方园林、江南园林、岭南园林、闽台园林、现代园林、荟萃园、西部园林、港澳园林、国际园林和企业园林等10个展园区，汇集了包括中华不同流派的园林和带有异国情调的国际园林在内的127个展园。
生态区：为维护园区整体优良的山体生态环境而设置的区域，既是园区各园林的绿色大背景，也是维持动植物多样性的天然宝库。

1.园博园自然资源
重庆园博园景区共有植物128科359属660种，其中蕨类植物5科5属5种，裸子植物9科17属35种，被子植物114科337属620种。有国家一级重点保护野生植物7种（四川苏铁、银杏、水杉、矮紫杉、红豆杉、曼迪亚红豆杉、南方红豆杉），国家二级重点保护野生植物7种（鹅掌楸、峨眉含笑、楠木、土沉香、喜树、董棕、桫椤）。园内有规模大、数量多的银杏树和桂花树，1.5千米的樱花大道上有2000株日本晚樱，每年3月底花期之际，花团锦簇，被誉为重庆“最美园路”。
重庆园博园共发现野生动物300种，其中鸟类超过150种。在园内有重庆罕见的红腹鹰、鸳鸯、红翅绿鸠、火冠雀、灰背伯劳和普通朱雀等鸟类，黄嘴白鹭、天鹅、鸳鸯、长脚秧鸡、白腹黑啄木鸟、鹦鹉、大壁虎、猫头鹰、红隼9种为国家二级重点保护野生动物。

1.园博园文物收藏（园博园中无文物）
除了自然美景，重庆园博园还提供丰富多样的文化体验。你可以参观各种展览馆，了解中国的传统文化和艺术，也可以参与互动活动，如举办的摄影比赛或园艺体验课程，还可以与其他游客交流分享，互相借鉴，让旅程更加丰富多彩。在园内的表演区域，还会有精彩纷呈的文艺演出，如舞蹈、音乐等，让你感受到中国传统文化的魅力。此外，你还可以参与手工艺制作活动，亲自动手制作一些传统工艺品，体验中国文化的独特之处。这些文化体验将让你更深入地了解中国的传统文化，增添旅行的乐趣和收获。

1.园博园主要建筑：重云塔
重庆园博园重云塔是园内唯一的塔式建筑，更是整个园博园的点睛之笔。重云塔高51.6米，共七层，是园博园内最高的单体建筑，游客可登塔望远，一览全园胜景。重云塔自身不仅是仿古建筑，而且其周边大都采用松柏类植物，辅以常绿孤植黄葛大树，显得古韵十足。
白天，重云塔在青山绿水之间，显得古香古色、肃静典雅。重云塔下的龙景湖波光滟潋，湖光山色，形成一幅古代水墨山水画，让人陶醉。夜色之中，重云塔华灯初上，金光耀目。镀上暖光的北京展园，与重云塔交相辉映，如一幅美丽的金色画卷。

1.园博园主要建筑：龙景书院
龙景书院是重庆园博园中唯一的书院建筑，位于园博园中部龙景湖畔的龙脊山上，结合山头较缓区域，按照中华传统建筑规则，在一条中轴线上呈轴对称布局“西北高，东南低”的两进院落，以传统书院空间结构展示中国传统文化魅力。
书院配套园林，是以松、竹、梅为主题打造的“三友园”。由于滨湖而建，整个龙景书院也是园博园中一方赏湖佳地。

Hard agree here. Once people understand rust, not read some bullet points on a blog they start to understand how useful even the tooling is.Only thing I'll add is. 8 times out of 10 if you are reaching for advanced rust, you are over engineering. Most software projects don't require it and when they do, you should always question whether there's a simpler more maintainable way or make a other design decision. There is no award for least lines of code, or most utilized compiler. Software is social.That's Go's biggest strength over Rust and Scala. Good luck getting job security in that language. It takes a few years to really know what I'm saying but in my opinion it's the difference between a senior engineer and a non senior.
        """,
    ]
    # text = """"""
    for inum, text in enumerate(ls):
        print(inum)
        chunks = text_splitter.split_text(text)
        for chunk in chunks:
            print(f"--------------------------------------{len(chunk)}: \n{chunk}")
