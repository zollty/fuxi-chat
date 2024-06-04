from typing import (
    List,
    Dict,
)
from fuxi.utils.api_base import ApiRequest
import jian.common.base_config as bc

api = ApiRequest(base_url=bc.internet_tools_address())

def search_engine(
        query: str,
) -> str:
    data = {
        "query": query,
    }
    print("start to query search_engine---------------------------------")
    response = api.post(
        "/internet/search_engine",
        data=data
    )
    return api.get_response_value(response, as_json=True, value_func=lambda r: r.get("data", ""))
