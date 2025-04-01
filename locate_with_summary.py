import datetime
import json
import os

from config import project_root
from glm import ChatGLM, ModelType
from summarize import summarize_spring_boot_folder
from utils.files import read_commit, read_prompt
from utils.git import checkout_to_parent_commit


def generate_summary_string(root_folder: str) -> str:
    summary_result = summarize_spring_boot_folder(root_folder)
    summary_return = ""
    for file, summary in summary_result.items():
        summary_return += f"\n文件：{file}\n摘要：{summary}\n"
    return summary_return


def generate_summary_string_cached(root_folder: str, comment_hash: str) -> str:
    cache_dir = 'cache'
    os.makedirs(cache_dir, exist_ok=True)
    cache_file_path = os.path.join(cache_dir, f"{comment_hash}.json")

    if os.path.exists(cache_file_path):
        with open(cache_file_path, 'r', encoding='utf-8') as cache_file:
            summary_result = json.load(cache_file)
    else:
        summary_result = summarize_spring_boot_folder(root_folder)
        with open(cache_file_path, 'w', encoding='utf-8') as cache_file:
            json.dump(summary_result, cache_file, ensure_ascii=False, indent=4)

    summary_return = ""
    for file, summary in summary_result.items():
        summary_return += f"\n文件：{file}\n摘要：{summary}\n"
    return summary_return


if __name__ == "__main__":
    spring_boot_folder = project_root

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # 遍历data文件夹
    data_folder = 'data'
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        commits = read_commit(file_path)
        for commit in commits:
            commit_type, commit_msg, commit_hash = commit
            checkout_to_parent_commit(project_root, commit_hash)

            # summary_string = generate_summary_string(spring_boot_folder)
            summary_string = generate_summary_string_cached(spring_boot_folder, commit_hash)

            message = (f"Your mission whose type is {commit_type} is to {commit_msg}, here are the summary of "
                       f"codespace.\n")

            prompt = read_prompt(message + summary_string)

            model = ChatGLM(model_type=ModelType.GLM_4)

            result = model(prompt)

            filename_without_extension = os.path.splitext(filename)[0]
            result_dir = os.path.join(f'result/locate_with_summary/{timestamp}', filename_without_extension)
            os.makedirs(result_dir, exist_ok=True)
            result_file_path = os.path.join(result_dir, f"{commit_hash}.txt")
            with open(result_file_path, 'w', encoding='utf-8') as result_file:
                result_file.write(str(result))
