import pathlib
from os import path

from .rag_system import RAGSystem

file_path = path.abspath(path.dirname(__file__))

rag_binary = pathlib.Path(file_path).parent /  'index.bin'

template = """


=====================
检索到的代码库：
{history}
"""


_rag_system_hpv = RAGSystem.load_index(rag_binary, template)
