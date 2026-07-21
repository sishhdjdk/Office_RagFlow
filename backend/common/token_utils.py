import tiktoken


encoder = tiktoken.get_encoding("cl100k_base")

#role: 计算文本的 token 数量
def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    try:
        code_list = encoder.encode(string)
        return len(code_list)
    except Exception:
        return 0