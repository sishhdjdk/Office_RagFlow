import re
from common.token_utils import num_tokens_from_string
import logging

def naive_merge(sections:str | list,chunk_token_num=2048, delimiter="\n。；！？", overlapped_percent=0):
    from deepdoc.parser.pdf_parser import PdfParser

    """
    将文本段落合并为指定 token 数量的块。
    输入：
        sections: 文本段落列表或单个字符串
        chunk_token: 每个块的最大 token 数量
    """
    if not sections:
        return []
    if isinstance(sections, str):
        sections = [sections]
    if isinstance(sections[0],str):
        sections=[(s,"") for s in sections]
     # Normalize line endings so delimiter ``\n`` matches ``\r\n`` and standalone ``\r``.
    sections = [(s.replace("\r\n", "\n").replace("\r", "\n"), pos) for s, pos in sections]
    cks = [""]
    tk_nums = [0]
    
    # 追加块
    def add_chunk(t,pos):
        nonlocal cks, tk_nums, delimiter
        tnum = num_tokens_from_string(t)
        if not pos:
            pos = ""
        if tnum < 8:
            pos = ""
        # Ensure that the length of the merged chunk does not exceed chunk_token_num
        #role： 允许重叠的百分比，默认为0
        if cks[-1] == "" or tk_nums[-1] > chunk_token_num * (100 - overlapped_percent) / 100.0:
            if cks:
                overlapped = PdfParser.remove_tag(cks[-1])
                t = overlapped[int(len(overlapped) * (100 - overlapped_percent) / 100.0) :] + t
                # Recount with the overlap prefix included, else chunks overshoot chunk_token_num.
                tnum = num_tokens_from_string(t)
            if t.find(pos) < 0:
                t += pos
            cks.append(t)
            tk_nums.append(tnum)
        else:
            if cks[-1].find(pos) < 0:
                t += pos
            cks[-1] += t
            tk_nums[-1] += tnum
            
    # 自定义切分符号处理
    custom_delimiters = [m.group(1) for m in re.finditer(r"`([^`]+)`", delimiter)]
    has_custom = bool(custom_delimiters)
    if has_custom:
        # Custom delimiters ignore chunk_token_num: each segment is its own chunk.
        custom_pattern = "|".join(re.escape(t) for t in sorted(set(custom_delimiters), key=len, reverse=True))
        cks, tk_nums = [], []
        for sec, pos in sections:
            split_sec = re.split(r"(%s)" % custom_pattern, sec, flags=re.DOTALL)
            for sub_sec in split_sec:
                if re.fullmatch(custom_pattern, sub_sec or ""):
                    continue
                text = "\n" + sub_sec
                local_pos = pos
                if num_tokens_from_string(text) < 8:
                    local_pos = ""
                if local_pos and text.find(local_pos) < 0:
                    text += local_pos
                cks.append(text)
                tk_nums.append(num_tokens_from_string(text))
        return cks
    
    # Split oversized sections at sentence delimiters; add_chunk re-merges to size.
    dels = get_delimiters(delimiter)
    for sec, pos in sections:
        if not dels or num_tokens_from_string(sec) < chunk_token_num:
            add_chunk("\n" + sec, pos)
            continue
        for sub_sec in re.split(r"(%s)" % dels, sec, flags=re.DOTALL):
            if not sub_sec or re.fullmatch(dels, sub_sec):
                continue
            add_chunk("\n" + sub_sec, pos)
            
    logging.debug("naive_merge: %d sections -> %d chunks (delimiter=%r)", len(sections), len(cks), delimiter)
    return cks

#role: 获取自定义分隔符
def get_delimiters(delimiters: str):
    dels = []
    s = 0
    for m in re.finditer(r"`([^`]+)`", delimiters, re.I):
        f, t = m.span()
        dels.append(m.group(1))
        dels.extend(list(delimiters[s:f]))
        s = t
    if s < len(delimiters):
        dels.extend(list(delimiters[s:]))

    dels.sort(key=lambda x: -len(x))
    dels = [re.escape(d) for d in dels if d]
    dels = [d for d in dels if d]
    dels_pattern = "|".join(dels)

    return dels_pattern