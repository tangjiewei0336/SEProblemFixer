import os

import pandas as pd

from config import project_root
from locate_with_questions import display_commit_list
from summarize import summarize_spring_boot_folder
from utils.rag.content_provider import RAGContentProvider
from utils.rag.rag_system import RAGSystem


def save_summary_xlsx(spring_boot_folder, output_path, content_column, source_column, max_workers=50):
    print("Saving Summary to Excel...")
    result = summarize_spring_boot_folder(spring_boot_folder, max_workers=max_workers)
    df = pd.DataFrame(list(result.items()), columns=[source_column, content_column])
    df.to_excel(output_path, index=False)
    print(f"Summary Excel Saved to {output_path}.")


def create_index(summary_xlsx_path, content_column, source_column, output_path):
    print("Creating RAG Index...")

    content_provider = RAGContentProvider(".")
    content_provider.add_excel_file(summary_xlsx_path,content_column,source_column)
    rag_system = RAGSystem.from_content_provider(content_provider, None)
    rag_system.save_index(output_path)
    print(f"RAG Index Saved to {output_path}.")


if __name__ == "__main__":
    commit_type, commit_msg, commit_hash, commit_filename = display_commit_list()
    commit_data_type = os.path.splitext(commit_filename)[0]
    summary_content_column = "摘要"
    summary_source_column = "文件路径"

    summary_path = f"summary/{commit_data_type}/{commit_hash}.xlsx"
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)

    if os.path.exists(summary_path):
        print("Summary Excel already exists. Skipping summary generation.")
    else:
        save_summary_xlsx(project_root, summary_path, summary_content_column, summary_source_column, max_workers=50)

    rag_index_path = f"rag_index/{commit_filename}/{commit_hash}.index"
    os.makedirs(os.path.dirname(rag_index_path), exist_ok=True)
    if os.path.exists(rag_index_path):
        print("RAG Index already exists. Skipping index creation.")
    else:
        create_index(summary_path, summary_content_column, summary_source_column, rag_index_path)
