import os

import pandas as pd

from config import project_root
from locate_with_questions import display_commit_list
from summarize import summarize_spring_boot_folder
from utils.files import read_and_replace_prompt
from utils.git import checkout_to_parent_commit
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


def query(rag_index_filepath, rag_prompt_filepath, variables):
    rag_prompt = read_and_replace_prompt(rag_prompt_filepath, variables)
    rag_system = RAGSystem.load_index(rag_index_filepath, rag_prompt)
    return rag_system.query(rag_prompt)


def get_summary_string(summary_excel):
    print("Generating Summary String from Excel...")
    summary_df = pd.read_excel(summary_excel)
    summary_items = []
    for _, row in summary_df.iterrows():
        file_path = str(row[summary_source_column])
        content = str(row[summary_content_column])
        summary_items.append(f"文件路径: {file_path}\n摘要: {content}")
    result = "\n\n".join(summary_items)
    print("Summary String Generated.")
    return result


if __name__ == "__main__":
    commit_type, commit_msg, commit_hash, commit_filename = display_commit_list()
    commit_data_type = os.path.splitext(commit_filename)[0]

    checkout_result = checkout_to_parent_commit(project_root, commit_hash)
    if not checkout_result[0]:
        print("git checkout fail:")
        print(checkout_result)
        exit()
    else:
        print("git checkout success")

    summary_content_column = "摘要"
    summary_source_column = "文件路径"

    summary_path = f"summary/{commit_data_type}/{commit_hash}.xlsx"
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)

    if os.path.exists(summary_path):
        print("Summary Excel already exists. Skipping summary generation.")
    else:
        save_summary_xlsx(project_root, summary_path, summary_content_column, summary_source_column, max_workers=50)

    summary = get_summary_string(summary_path)

    rag_index_path = f"rag_index/{commit_data_type}/{commit_hash}.index"
    os.makedirs(os.path.dirname(rag_index_path), exist_ok=True)
    if os.path.exists(rag_index_path):
        print("RAG Index already exists. Skipping index creation.")
    else:
        create_index(summary_path, summary_content_column, summary_source_column, rag_index_path)

    rag_prompt_path = "prompt/rag.txt"
    rag_result = query(rag_index_path, rag_prompt_path, {
        "commit_type": commit_type,
        "commit_msg": commit_msg, 
        "commit_hash": commit_hash,
        "summary": summary,
    })
    print("RAG Query Result:")
    print(rag_result)
