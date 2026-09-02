import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

HOME = Path.home()


def _load_opencode_key(provider):
    cfg_path = HOME / ".config" / "opencode" / "opencode.jsonc"
    raw = cfg_path.read_text()
    raw = re.sub(r"^\s*//.*$", "", raw, flags=re.M)
    cfg = json.loads(raw)
    return cfg.get("provider", {}).get(provider, {}).get("options", {}).get("apiKey", "")


def _load_auth_key(provider):
    auth = json.loads((HOME / ".local" / "share" / "opencode" / "auth.json").read_text())
    return auth.get(provider, {}).get("key", "")


@dataclass
class BackendConfig:
    name: str = "mock"
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.3
    max_tokens: int = 2048
    timeout: int = 600
    retries: int = 2
    seed: int = 0
    extra: dict = None


class MockBackend:
    def __init__(self, seed=0):
        self.rng = __import__("random").Random(seed)

    def complete(self, system, user, schema=None):
        return json.dumps({"answer": "MOCK", "echo": user[:64]})


class HTTPBackend:
    def __init__(self, config: BackendConfig):
        self.config = config

    def complete(self, system, user, schema=None):
        cfg = self.config
        payload = {
            "model": cfg.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
        }
        if cfg.extra:
            payload.update(cfg.extra)
        last_err = None
        for attempt in range(cfg.retries + 1):
            try:
                req = urllib.request.Request(
                    cfg.base_url.rstrip("/") + "/chat/completions",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json",
                             **({"Authorization": f"Bearer {cfg.api_key}"} if cfg.api_key else {})})
                with urllib.request.urlopen(req, timeout=cfg.timeout) as r:
                    out = json.loads(r.read())
                return out["choices"][0]["message"]["content"]
            except Exception as e:
                last_err = e
                time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"{cfg.name}/{cfg.model} failed: {str(last_err)[:200]}")

    def embed(self, texts):
        cfg = self.config
        req = urllib.request.Request(
            cfg.base_url.rstrip("/") + "/embeddings",
            data=json.dumps({"model": cfg.model, "input": texts}).encode(),
            headers={"Content-Type": "application/json",
                     **({"Authorization": f"Bearer {cfg.api_key}"} if cfg.api_key else {})})
        with urllib.request.urlopen(req, timeout=cfg.timeout) as r:
            out = json.loads(r.read())
        return [d["embedding"] for d in sorted(out["data"], key=lambda d: d["index"])]


def make_backend(role, **override):
    cfg = BACKENDS[role]()
    for k, v in override.items():
        setattr(cfg, k, v)
    if cfg.name == "mock":
        return MockBackend(seed=cfg.seed)
    return HTTPBackend(cfg)


_LOCAL = "http://10.125.125.64:1234/v1"
_ZEN = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
_KIMI = "https://api.kimi.com/coding/v1"

BACKENDS = {
    "local_main": lambda: BackendConfig("local_main", "qwen3.8-27b-mlx", _LOCAL, "", 0.3, 2048, 1200, 2),
    "local_small": lambda: BackendConfig("local_small", "ornith-1.5-35b", _LOCAL, "", 0.3, 2048, 1200, 2),
    "local_embed": lambda: BackendConfig("local_embed", "text-embedding-nomic-embed-text-v1.5", _LOCAL, "", 0.0, 512, 300, 2),
    "online_strong": lambda: BackendConfig("online_strong", "qwen3.8-max", _ZEN, _load_auth_key("alibaba-token-plan-cn"), 0.3, 2048, 300, 2, extra={"enable_thinking": False}),
    "online_fast": lambda: BackendConfig("online_fast", "qwen3.8-flash", _ZEN, _load_auth_key("alibaba-token-plan-cn"), 0.3, 2048, 300, 2, extra={"enable_thinking": False}),
    "online_alt": lambda: BackendConfig("online_alt", "glm-5.2", _ZEN, _load_auth_key("alibaba-token-plan-cn"), 0.3, 2048, 300, 2, extra={"enable_thinking": False}),
    "kimi_k3": lambda: BackendConfig("kimi_k3", "k3", _KIMI, _load_opencode_key("kimi-code"), 0.3, 2048, 300, 2),
}

