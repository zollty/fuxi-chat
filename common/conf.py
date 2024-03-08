import tomli
from common.utils import detect_device
from typing import (Any, List)


class BaseCfg():
    '''
    llm.device
    embed.device
    '''
    toml_dict: dict[str, Any]

    def __init__(self, conf_path: str, is_path: bool = True):
        if is_path:
            with open(conf_path, "rb") as f:
                try:
                    self.toml_dict = tomli.load(f)
                    print(self.toml_dict)
                except tomli.TOMLDecodeError:
                    print("Yep, definitely not valid.")
        else:
            try:
                self.toml_dict = tomli.loads(conf_path)
                print(self.toml_dict)
            except tomli.TOMLDecodeError:
                print("Yep, definitely not valid.")
        _auto = None
        if self.iget("llm.device") == "auto":
            _auto = detect_device()
            self.set("llm.device", _auto)

        if self.iget("embed.device") == "auto":
            if _auto is None:
                _auto = detect_device()
            self.set("embed.device", _auto)

    def set(self, key: str, val=None):
        self.toml_dict[key] = val

    def get(self, key: str, default_val=None):
        return self.iget(key, default_val)

    def _dict(self, obj, key: str):
        s = key.find("[")
        e = key.find("]")
        if s != -1 and e != -1:
            return obj[key[0:s]][int(key[s + 1:e])]
        else:
            return obj[key]

    def _get(self, keys: List[str]):
        obj = self.toml_dict
        for k in keys:
            obj = self._dict(obj, k)
        return obj

    def iget(self, key: str, default_val=None):
        sv = key.split(".")
        le = len(sv)
        # print(f"get key: {sv}")
        ret = None
        try:
            ret = self._get(sv[0:le])
        except:
            print(f"this key \"{key}\" not exist!")
        if default_val is None:
            return ret
        elif ret:
            return ret
        else:
            return default_val


class Cfg(BaseCfg):
    parent_cfg: BaseCfg

    def __init__(self, conf_path: str, is_path: bool = True, parent_cfg: BaseCfg = None):
        super().__init__(conf_path, is_path)
        self.parent_cfg = parent_cfg

    def get(self, key: str, default_val=None):
        ret = super().get(key)
        if ret:
            return ret
        elif self.parent_cfg is not None:
            return self.parent_cfg.get(key, default_val)
        return default_val
