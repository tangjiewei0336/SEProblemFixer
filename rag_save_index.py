import pathlib
from os import path

from utils.rag.rag_system import RAGSystem
from utils.rag.content_provider import RAGContentProvider


# 本脚本将从content_provider中读取数据，然后将数据保存到index.bin中
print("now creating index")

file_path = path.abspath(path.dirname(__file__))
content_provider = RAGContentProvider(".")
content_provider.add_excel_file("spring_boot_summaries.xlsx","摘要","文件路径")
rag_system = RAGSystem.from_content_provider(content_provider, None)
rag_system.save_index(pathlib.Path(file_path) / "index.bin")
print("Index saved to index.bin")

