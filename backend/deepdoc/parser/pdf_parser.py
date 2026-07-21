import pdfplumber
import re #role：正则表达式

class PdfParser:
    @staticmethod
    def parse(file_path:str) -> list[tuple[str,str]]:
        """
        输入：MinIO 下载到本地的 PDF 文件路径
        输出：[(文本内容, 位置标识), ...]
        位置标识格式： "page_0", "page_1"...
        """
        sections=[]
        with pdfplumber.open(file_path) as pdf:
            for i,page in enumerate(pdf.pages):
                text=page.extract_text() or ""
                if text.strip():  # 只添加非空文本
                    sections.append((text, f"page_{i}"))
        return sections
    
    # 清空坐标标签
    @staticmethod
    def remove_tag(txt):
        return re.sub(r"@@[\t0-9.-]+?##", "", txt)