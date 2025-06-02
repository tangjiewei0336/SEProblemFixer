import os
import pathlib
from typing import List

import pandas as pd

from config import project_root
from glm import ChatGLM, ModelType
from locate_with_questions import display_commit_list
from summarize import summarize_spring_boot_folder
from utils.file_format_detect import detect_response_format
from utils.files import concat_code_files, read_and_replace_prompt
from utils.git import checkout_to_parent_commit
from utils.rag.content_provider import RAGContentProvider
from utils.rag.rag_system import RAGSystem
from utils.tool.file_viewer import ToolParser, get_file_content


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
    print(f"Saving RAG Index...")
    rag_system.save_index(output_path)
    print(f"RAG Index Saved to {output_path}.")


def rag_query(rag_index_filepath, rag_prompt_filepath, variables):
    rag_prompt = read_and_replace_prompt(rag_prompt_filepath, variables)
    rag_system = RAGSystem.load_index(rag_index_filepath, rag_prompt)
    return rag_system.get_assembled_prompt(rag_prompt, None)


def chating(prompt, model):
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = model.chat(messages).content
        messages.append({
            "role": "assistant",
            "content": response,
        })
        response_format = detect_response_format(response)

        if response_format == 'text':
            print("Please answer LLM's question:")
            print(response)
            user_input = input("Your answer: ")
            messages.append({
                "role": "user",
                "content": user_input,
            })
        elif response_format == 'xml':
            print("LLM is viewing file:")
            print(response)

            tool_info_str = (
                "<tool>"
                + response.split("<tool>")[1].split("</tool>")[0]
                + "</tool>"
            )
            parser = ToolParser(tool_info_str)
            parser.parse()
            tool_info = parser.get_tool_info()
            content = get_file_content(os.path.join(pathlib.Path(project_root).parent, tool_info["filepath"]))

            print("File content retrieved:")
            print(content)

            messages.append({"role": "user", "content": content})
        
        elif response_format == 'json':
            print('LLM output final answer:')
            print(response)
            break

    return messages


def get_summary_string(summary_excel):
    summary_df = pd.read_excel(summary_excel)
    summary_items = []
    for _, row in summary_df.iterrows():
        file_path = str(row[summary_source_column])
        content = str(row[summary_content_column])
        summary_items.append(f"文件路径: {file_path}\n摘要: {content}")
    result = "\n\n".join(summary_items)
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

    code_repo = concat_code_files(
        project_root, filter=lambda x: x.endswith(".java"), use_relative_path=True
    ).replace("{", "{{").replace("}", "}}")

    print("RAG querying...")
    prompt_path = "prompt/locate.md"
    rag_result = rag_query(rag_index_path, prompt_path, {
        "commit_type": commit_type,
        "commit_msg": commit_msg, 
        "commit_hash": commit_hash,
    })
    print("RAG query result:")
    print(rag_result)

    chating(rag_result, ChatGLM(model_type=ModelType.GLM_4))
