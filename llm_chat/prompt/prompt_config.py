# prompt模板使用Jinja2语法，简单点就是用双大括号代替f-string的单大括号
# 本配置文件支持热加载，修改prompt模板后无需重启服务。

# LLM对话支持的变量：
#   - input: 用户输入内容

# 知识库和搜索引擎对话支持的变量：
#   - context: 从检索结果拼接的知识文本
#   - question: 用户提出的问题

# Agent对话支持的变量：

#   - tools: 可用的工具列表
#   - tool_names: 可用的工具名称列表
#   - history: 用户和Agent的对话历史
#   - input: 用户输入内容
#   - agent_scratchpad: Agent的思维记录

PROMPT_TEMPLATES = {
    "llm_chat": {
        "default":
            '{{ input }}',

        "关键词提取": """你是一个关键词捕捉专家，请将用户每一个问题提取出1个最重要的关键词（只要名词，通常为2~4个字）。
例如：
问题：使用shell工具查询当前系统的磁盘情况
关键词：磁盘、shell
问题：照壁有什么用
关键词：照壁
问题：使用arxiv工具查询关于transformer的论文
关键词：transformer、arxiv

下面是用户的问题：
{{ input }}""",

        "充当英语翻译和改进":
            '**替代**：语法，谷歌翻译\n\n> 我希望你能担任英语翻译、拼写校对和修辞改进的角色。我会用任何语言和你交流，你会识别语言，将其翻译并用更为优美和精炼的英语回答我。请将我简单的词汇和句子替换成更为优美和高雅的表达方式，确保意思不变，但使其更具文学性。请仅回答更正和改进的部分，不要写解释。第一个需要翻译的是：\n'
            '"{{ input }}"',

        "把任何语言翻译成中文":
            '下面我让你来充当翻译家，你的目标是把任何语言翻译成中文，请翻译时不要带翻译腔，而是要翻译得自然、流畅和地道，使用优美和高雅的表达方式。第一个需要翻译的是：\n'
            '"{{ input }}"',

        "把任何语言翻译成英语":
            '下面我让你来充当翻译家，你的目标是把任何语言翻译成英文，请翻译时不要带翻译腔，而是要翻译得自然、流畅和地道，使用优美和高雅的表达方式。第一个需要翻译的是：\n'
            '"{{ input }}"',

        "充当词典(附中文解释)":
            '将英文单词转换为包括中文翻译、英文释义和一个例句的完整解释。请检查所有信息是否准确，并在回答时保持简洁，不需要任何其他反馈。第一个单词是: \n'
            '"{{ input }}"',

        "充当旅游指南":
            '我想让你做一个旅游指南。我会把我的位置写给你，你会推荐一个靠近我的位置的地方。在某些情况下，我还会告诉您我将访问的地方类型。您还会向我推荐靠近我的第一个位置的类似类型的地方。我的第一个建议请求是: \n'
            '"{{ input }}"',

        "扮演脱口秀喜剧演员":
            '我想让你扮演一个脱口秀喜剧演员。我将为您提供一些与时事相关的话题，您将运用您的智慧、创造力和观察能力，根据这些话题创建一个例程。您还应该确保将个人轶事或经历融入日常活动中，以使其对观众更具相关性和吸引力。我的第一个请求是: \n'
            '"{{ input }}"',

        "二次元语气":
            'You are a helpful assistant. 请用二次元可爱语气回答问题。我的第一个请求是: \n'
            '"{{ input }}"',

        "充当医生":
            '我想让你扮演医生的角色，提出合理的治疗方法来治疗疾病。您应该能够推荐常规药物、草药和其他天然替代品。在提供建议时，您还需要考虑患者的年龄、生活方式和病史。我的第一个建议请求是：\n'
            '{{ input }}',

        "with_history":
            'The following is a friendly conversation between a human and an AI. '
            'The AI is talkative and provides lots of specific details from its context. '
            'If the AI does not know the answer to a question, it truthfully says it does not know.\n\n'
            'Current conversation:\n'
            '{{ history }}\n'
            'Human: {{ input }}\n'
            'AI:',

        "with_text": """参考信息：
已知（提供知识）xxxxxxxxxxxxxxxxxxxxxxxxxx
---
我的问题或指令：
{{ input }}
---
请根据上述参考信息回答我的问题或回复我的指令。前面的参考信息可能有用，也可能没用，你需要从我给出的参考信息中选出与我的问题最相关的那些，来为你的回答提供依据。回答一定要忠于原文，简洁但不丢信息，不要胡乱编造。我的问题或指令是什么语种，你就用什么语种回复,
你的回复：""",
    },

    "yby_chat": {
        "default":
            '<指令>这是我搜索到的相关信息，请你根据这些信息进行提取并有调理，简洁的回答问题。'
            '如果无法从中得到答案，请说 “无法搜索到能回答问题的内容”。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "fast": """使用 <Data></Data> 标记中的内容作为你的知识:

<Data>
{{ context }}
</Data>

回答要求：
- 如果你不清楚答案，你需要澄清。
- 避免提及你是从 <Data></Data> 获取的知识。
- 保持答案与 <Data></Data> 中描述的一致。
- 使用 Markdown 语法优化回答格式。

问题:\"\"\"{{ question }}\"\"\"""",

        "youdao": """参考信息：
{{ context }}
---
我的问题或指令：
{{ question }}
---
请根据上述参考信息回答我的问题或回复我的指令。前面的参考信息可能有用，也可能没用，你需要从我给出的参考信息中选出与我的问题最相关的那些，来为你的回答提供依据。回答一定要忠于原文，简洁但不丢信息，不要胡乱编造。我的问题或指令是什么语种，你就用什么语种回复,
你的回复：""",

        "search":
            '<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，答案请使用中文。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',
    },

    "knowledge_base_chat": {
        "default":
            '<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，'
            '不允许在答案中添加编造成分，答案请使用中文。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "text":
            '<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，答案请使用中文。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "direct":
            '<指令>请根据下面信息回答问题</指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "quming":
            '<指令>你是一个文学大师、取名专家，请根据下面信息回答问题</指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "youdao": """参考信息：
{{ context }}
---
我的问题或指令：
{{ question }}
---
请根据上述参考信息回答我的问题或回复我的指令。前面的参考信息可能有用，也可能没用，你需要从我给出的参考信息中选出与我的问题最相关的那些，来为你的回答提供依据。回答一定要忠于原文，简洁但不丢信息，不要胡乱编造。我的问题或指令是什么语种，你就用什么语种回复,
你的回复：""",

        "empty":  # 搜不到知识库的时候使用
            '请你回答我的问题:\n'
            '{{ question }}\n\n',
    },

    "doc_chat": {
        "summary1": """请简洁和专业的总结下面文档内容。文档内容如下：


"{{ text }}"


文档总结为：""",

        "summary2": """<指令>请简洁和专业的总结下面文档内容。请用中文总结。</指令>

<文档>"{{ text }}"</文档>


文档总结为：""",

        "summary3":
            '请简洁和专业的总结下面文档内容。'
            '文档内容如下：\n'
            '\n\n{{text}}\n\n'
            '文档总结为：\n',

        "summary4":
            '<指令>请简洁和专业的总结下面文档内容。</指令>\n'
            '<文档>{{ text }}</文档>\n',

        "summary5": """<指令>请简洁和专业的总结下面文档内容。</指令>

<文档>"{{text}}"</文档>


以上文档总结为：\n""",

        "summary6": """<指令>请总结下面文档，然后将它以简洁的方式重写。</指令>

<文档>"{{text}}"</文档>


文档重写为：\n""",

        "summary_lc":
            """Write a concise summary of the following:


"{{ text }}"


CONCISE SUMMARY:""",

        "summary_lc_zh":
            """Write a concise summary of the following:


"{{ text }}"


CONCISE SUMMARY IN CHINESE:""",

        "refine":
            """\
Your job is to produce a final summary.
We have provided an existing summary up to a certain point: {existing_answer}
We have the opportunity to refine the existing summary (only if needed) with some more context below.
------------
{{ text }}
------------
Given the new context, refine the original summary.
If the context isn't useful, return the original summary.\
""",

        "relate_qa": """根据以下内容，生成几个相关的提问。内容如下：


"{{ text }}"


相关的提问：""",

    },

    "search_engine_chat": {
        "default":
            '<指令>这是我搜索到的互联网信息，请你根据这些信息进行提取并有调理，简洁的回答问题。'
            '如果无法从中得到答案，请说 “无法搜索到能回答问题的内容”。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',

        "search":
            '<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，答案请使用中文。 </指令>\n'
            '<已知信息>{{ context }}</已知信息>\n'
            '<问题>{{ question }}</问题>\n',
    },

    "agent_chat": {
        "default":
            'Answer the following questions as best you can. If it is in order, you can use some tools appropriately. '
            'You have access to the following tools:\n\n'
            '{tools}\n\n'
            'Use the following format:\n'
            'Question: the input question you must answer1\n'
            'Thought: you should always think about what to do and what tools to use.\n'
            'Action: the action to take, should be one of [{tool_names}]\n'
            'Action Input: the input to the action\n'
            'Observation: the result of the action\n'
            '... (this Thought/Action/Action Input/Observation can be repeated zero or more times)\n'
            'Thought: I now know the final answer\n'
            'Final Answer: the final answer to the original input question\n'
            'Begin!\n\n'
            'history: {history}\n\n'
            'Question: {input}\n\n'
            'Thought: {agent_scratchpad}\n',

        "ChatGLM3":
            'You can answer using the tools, or answer directly using your knowledge without using the tools. '
            'Respond to the human as helpfully and accurately as possible.\n'
            'You have access to the following tools:\n'
            '{tools}\n'
            'Use a json blob to specify a tool by providing an action key (tool name) '
            'and an action_input key (tool input).\n'
            'Valid "action" values: "Final Answer" or  [{tool_names}]'
            'Provide only ONE action per $JSON_BLOB, as shown:\n\n'
            '```\n'
            '{{{{\n'
            '  "action": $TOOL_NAME,\n'
            '  "action_input": $INPUT\n'
            '}}}}\n'
            '```\n\n'
            'Follow this format:\n\n'
            'Question: input question to answer\n'
            'Thought: consider previous and subsequent steps\n'
            'Action:\n'
            '```\n'
            '$JSON_BLOB\n'
            '```\n'
            'Observation: action result\n'
            '... (repeat Thought/Action/Observation N times)\n'
            'Thought: I know what to respond\n'
            'Action:\n'
            '```\n'
            '{{{{\n'
            '  "action": "Final Answer",\n'
            '  "action_input": "Final response to human"\n'
            '}}}}\n'
            'Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. '
            'Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation:.\n'
            'history: {history}\n\n'
            'Question: {input}\n\n'
            'Thought: {agent_scratchpad}',
    }
}
