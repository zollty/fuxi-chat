from typing import AsyncIterable, Optional, Union
import json
from jian.llm_chat.chat.utils import format_jinja2_prompt_tmpl
from jian.llm_chat.chat.worker_direct_chat import chat_iter, ChatCompletionRequest
from jian.llm_chat.config import file_chat_summary_model, file_chat_default_temperature, summary_max_length

MAX_LENGTH = summary_max_length()


async def summary_doc(doc: str,
                      stream: bool = False,
                      model_name: str = None,
                      max_tokens: int = 0,
                      temperature: Optional[float] = None,
                      prompt_name: str = "summary1",
                      src_info=None,
                      ) -> AsyncIterable[str]:
    if not model_name:
        model_name = file_chat_summary_model()
    if not temperature:
        temperature = file_chat_default_temperature()
    if max_tokens > 0:
        use_max_tokens = max_tokens
    else:
        use_max_tokens = MAX_LENGTH

    if len(doc) > MAX_LENGTH:
        doc = doc[:MAX_LENGTH]

    history = [format_jinja2_prompt_tmpl(tmpl_type="doc_chat", tmpl_name=prompt_name, text=doc)]

    request = ChatCompletionRequest(model=model_name,
                                    messages=history,
                                    temperature=temperature,
                                    max_tokens=use_max_tokens,
                                    stream=stream,
                                    )

    print("start" + "-" * 20)
    for chunk in chat_iter(request):
        # handle the chunk data here
        print(json.dumps(chunk, ensure_ascii=False))
        if chunk.get("choices") is not None:
            # res.choices[0].delta.content
            json.dumps({"answer": chunk["choices"][0]["delta"]["content"]}, ensure_ascii=False)
        else:
            yield json.dumps(chunk, ensure_ascii=False)

    if not src_info:
        yield json.dumps({"docs": src_info}, ensure_ascii=False)
    print("end" + "-" * 20)

    # if stream:
    #     for chunk in chat_iter(request):
    #         # handle the chunk data here
    #         if chunk["error_code"] != 0:
    #             yield json.dumps(chunk, ensure_ascii=False)
    #         elif chunk["text"] is not None:
    #             json.dumps({"answer": chunk["text"]}, ensure_ascii=False)
    #         else:
    #             json.dumps({"docs": src_info}, ensure_ascii=False)
    #
    # else:
    #     res = await create_not_stream_chat_completion(request)
    #     if isinstance(res, ChatCompletionResponse):
    #         answer = res.choices[0].message.content
    #         yield json.dumps({"answer": answer, "docs": src_info}, ensure_ascii=False)
    #     else:
    #         yield
