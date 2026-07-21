import json
import os
import time
import requests

class ChatModel:
    def __init__(self, api_base: str = "", api_key: str = "", model_name: str = ""):
        api_base = api_base or os.getenv("LLM_API_BASE", "")
        api_key = api_key or os.getenv("LLM_API_KEY", "")
        model_name = model_name or os.getenv("LLM_MODEL_NAME", "")
        self.api_base = api_base.rstrip("/") if api_base else ""
        self.api_key = api_key
        self.model_name = model_name

    def _is_configured(self):
        return bool(self.api_base and self.api_key and self.model_name)

    def chat(self, messages: list[dict]) -> str:
        if not self._is_configured():
            return _mock_answer()

        resp = requests.post(
            f"{self.api_base}/chat/completions",
            json={"model": self.model_name, "messages": messages},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120,
        )
        return resp.json()["choices"][0]["message"]["content"]

    def stream_chat(self, messages: list[dict]):
        if not self._is_configured():
            for ch in _mock_answer():
                yield ch
                time.sleep(0.03)
            return

        resp = requests.post(
            f"{self.api_base}/chat/completions",
            json={"model": self.model_name, "messages": messages, "stream": True},
            headers={"Authorization": f"Bearer {self.api_key}"},
            stream=True,
            timeout=120,
        )
        print(f"[LLM] HTTP {resp.status_code} from {self.api_base}/chat/completions")
        for line in resp.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    data = decoded_line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        token = chunk["choices"][0]["delta"].get("content")
                        if token:
                            yield token
                    except Exception as e:
                        print(f"[LLM] 解析流式响应出错: {e}, 原始数据: {data[:200]}")
                else:
                    # 非标准 SSE（如阿里百炼兼容模式直接返回 JSON）
                    try:
                        data = json.loads(decoded_line)
                        text = data.get("text", "")
                        if text:
                            for ch in text:
                                yield ch
                                time.sleep(0.03)
                            break
                    except json.JSONDecodeError:
                        print(f"[LLM] 无法解析响应: {decoded_line[:300]}")


def _mock_answer():
    return "这是一个模拟回答。实际使用时请在 .env 中配置 LLM_API_BASE、LLM_API_KEY、LLM_MODEL_NAME。"
