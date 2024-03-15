import datetime
import hashlib
import json
import os
import time

import requests

from fastchat.constants import (
    LOGDIR,
    WORKER_API_TIMEOUT,
    ErrorCode,
    RATE_LIMIT_MSG,
    SERVER_ERROR_MSG,
)
# from fastchat.serve.api_provider import get_api_provider_stream_iter
from fastchat.utils import (
    build_logger,
    load_image,
)

logger = build_logger("gradio_web_server", "gradio_web_server.log")

headers = {"User-Agent": "FastChat Client"}

controller_url = None
# enable_moderation = None

def set_global_vars(controller_url_, enable_moderation_):
    global controller_url, enable_moderation
    controller_url = controller_url_
    enable_moderation = enable_moderation_

def model_worker_stream_iter(
    conv,
    model_name,
    worker_addr,
    prompt,
    temperature,
    repetition_penalty,
    top_p,
    max_new_tokens,
    images,
):
    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": prompt,
        "temperature": temperature,
        "repetition_penalty": repetition_penalty,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
        "stop": conv.stop_str,
        "stop_token_ids": conv.stop_token_ids,
        "echo": False,
    }

    logger.info(f"==== request ====\n{gen_params}")

    if len(images) > 0:
        gen_params["images"] = images

    # Stream output
    response = requests.post(
        worker_addr + "/worker_generate_stream",
        headers=headers,
        json=gen_params,
        stream=True,
        timeout=WORKER_API_TIMEOUT,
    )
    for chunk in response.iter_lines(decode_unicode=False, delimiter=b"\0"):
        if chunk:
            data = json.loads(chunk.decode())
            yield data


def bot_response(
    state,
    temperature,
    top_p,
    max_new_tokens,
    # request: gr.Request,
    # apply_rate_limit=True,
):
    # ip = get_ip(request)
    # logger.info(f"bot_response. ip: {ip}")
    start_tstamp = time.time()
    temperature = float(temperature)
    top_p = float(top_p)
    max_new_tokens = int(max_new_tokens)

    # if apply_rate_limit:
    #     ret = is_limit_reached(state.model_name, ip)
    #     if ret is not None and ret["is_limit_reached"]:
    #         error_msg = RATE_LIMIT_MSG + "\n\n" + ret["reason"]
    #         logger.info(f"rate limit reached. ip: {ip}. error_msg: {ret['reason']}")
    #         state.conv.update_last_message(error_msg)
    #         yield (state, state.to_gradio_chatbot()) + (no_change_btn,) * 5
    #         return

    conv, model_name = state.conv, state.model_name
    # model_api_dict = (
    #     api_endpoint_info[model_name] if model_name in api_endpoint_info else None
    # )
    images = conv.get_images()

    # Query worker address
    ret = requests.post(
        controller_url + "/get_worker_address", json={"model": model_name}
    )
    worker_addr = ret.json()["address"]
    logger.info(f"model_name: {model_name}, worker_addr: {worker_addr}")

    # No available worker
    if worker_addr == "":
        conv.update_last_message(SERVER_ERROR_MSG)
        return

    # Construct prompt.
    # We need to call it here, so it will not be affected by "▌".
    prompt = conv.get_prompt()

    # Set repetition_penalty
    if "t5" in model_name:
        repetition_penalty = 1.2
    else:
        repetition_penalty = 1.0

    stream_iter = model_worker_stream_iter(
        conv,
        model_name,
        worker_addr,
        prompt,
        temperature,
        repetition_penalty,
        top_p,
        max_new_tokens,
        images,
    )

    conv.update_last_message("▌")
    # yield (state, state.to_gradio_chatbot()) + (disable_btn,) * 5

    try:
        for i, data in enumerate(stream_iter):
            if data["error_code"] == 0:
                output = data["text"].strip()
                conv.update_last_message(output + "▌")
                # yield (state, state.to_gradio_chatbot()) + (disable_btn,) * 5
            else:
                output = data["text"] + f"\n\n(error_code: {data['error_code']})"
                conv.update_last_message(output)
                # yield (state, state.to_gradio_chatbot()) + (
                #     disable_btn,
                #     disable_btn,
                #     disable_btn,
                #     enable_btn,
                #     enable_btn,
                # )
                return
        output = data["text"].strip()
        conv.update_last_message(output)
        # yield (state, state.to_gradio_chatbot()) + (enable_btn,) * 5
    except requests.exceptions.RequestException as e:
        conv.update_last_message(
            f"{SERVER_ERROR_MSG}\n\n"
            f"(error_code: {ErrorCode.GRADIO_REQUEST_ERROR}, {e})"
        )
        return
    except Exception as e:
        conv.update_last_message(
            f"{SERVER_ERROR_MSG}\n\n"
            f"(error_code: {ErrorCode.GRADIO_STREAM_UNKNOWN_ERROR}, {e})"
        )
        return

    # finish_tstamp = time.time()
    logger.info(f"{output}")