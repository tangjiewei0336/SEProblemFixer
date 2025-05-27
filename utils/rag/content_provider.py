import pathlib
from abc import abstractmethod
from re import split
from typing import List

import pandas as pd
import pymupdf4llm
from langchain.docstore.document import Document
from langchain_text_splitters import CharacterTextSplitter


class BaseStrategy:
    def __init__(self, path):
        self.path: pathlib.Path = path

    @abstractmethod
    def process(self, **kwargs) -> List[Document]:
        ...

    def split_text(self, text: str, file_name = "") -> List[Document]:
        splitter = CharacterTextSplitter(chunk_size=1000, separator="\n", chunk_overlap=20)
        metadatas = [{"File Name": file_name}]
        documents = splitter.create_documents(
            [text], metadatas=metadatas
        )
        return documents


class ExcelStrategy(BaseStrategy):
    def __init__(self, path: pathlib.Path, content_column, source_column="", link_column="", sheet_name="Sheet1"):
        super().__init__(path)
        self.content_column: str = content_column
        self.source_column: str = source_column
        self.link_column: str = link_column
        self.sheet_name: str = sheet_name

    def process(self, **kwargs) -> List[Document]:
        print(f"Processing: {self.path}")
        df = pd.read_excel(self.path, sheet_name=self.sheet_name)
        documents = []
        for idx, row in df.iterrows():
            combined_content = f"{row[self.content_column]}"
            if len(combined_content) < 5:
                continue
            if self.source_column:
                combined_content = combined_content + f"\n Source: {row[self.source_column]}"
            if self.link_column:
                combined_content = combined_content + f"URL: {row[self.link_column]}"
            documents.append(Document(page_content=combined_content))
        return documents


def save_markdown_to_file(md_text: str, file_path: str):
    with open(file_path, "w+") as f:
        f.write(md_text)

class PDFStrategy(BaseStrategy):
    def __init__(self,path, use_cache=True):
        super().__init__(path)
        self.use_cache = use_cache

    def process(self, **kwargs) -> List[Document]:
        if self.use_cache:
            if (self.path.parent.parent / "cache" / (self.path.stem + ".md")).exists():
                print(f"Using cache for {self.path}")
                md_text = read_file(self.path.parent.parent / "cache" / (self.path.stem + ".md"))
                return self.split_text(md_text)
            else:
                print(f"Processing: {self.path}")
                md_text = pymupdf4llm.to_markdown(self.path)
                save_markdown_to_file(md_text, str(self.path.parent.parent / "cache" / (self.path.stem + ".md")))

                return self.split_text(md_text, self.path.stem)
        else:
            print(f"Processing: {self.path}")
            md_text = pymupdf4llm.to_markdown(self.path)

            return self.split_text(md_text)


class RawFileStrategy(BaseStrategy):
    def process(self, **kwargs) -> List[Document]:
        print(f"Processing: {self.path}")
        return self.split_text(read_file(self.path), self.path.stem)


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


class RAGContentProvider:

    def __init__(self, root_dir, pdf_output_dir="cache"):
        self.sources = []
        self.root_dir: pathlib.Path = pathlib.Path(root_dir.rstrip("/"))
        self.pdf_output_dir = self.root_dir / pdf_output_dir
        # build cache folder
        if not pathlib.Path(self.pdf_output_dir).exists():
            pathlib.Path(self.pdf_output_dir).mkdir(parents=True, exist_ok=True)

    def add_raw_file(self, path: str):
        self.sources.append(RawFileStrategy(self.root_dir / path))

    def add_raw_file_folder(self, path: str, suffix: str = "*"):
        input_path = self.root_dir / path
        for file_path in input_path.glob(suffix):
            self.sources.append(RawFileStrategy(file_path))

    def add_excel_file(self, path: str, content_column, source_column="", link_column="", sheet_name="Sheet1"):
        self.sources.append(ExcelStrategy(self.root_dir / path, content_column, source_column, link_column, sheet_name))

    def add_excel_file_folder(self, path: str, content_column, source_column="", link_column="", sheet_name="Sheet1"):
        input_path = self.root_dir / path
        for excel_path in input_path.glob("*.xlsx"):
            self.sources.append(ExcelStrategy(excel_path, content_column, source_column, link_column, sheet_name))

    def add_pdf_file(self, path: str):
        self.sources.append(PDFStrategy(self.root_dir / path))

    def add_pdf_file_folder(self, path: str):
        input_path = pathlib.Path(self.root_dir / path)
        for pdf_path in input_path.glob("*.pdf"):
            self.sources.append(PDFStrategy(pdf_path))

    def get_documents(self):
        documents = []
        for source in self.sources:
            documents.extend(source.process())
        return documents
