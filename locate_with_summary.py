import datetime
import json
import os
import time

from config import project_root
from glm import ChatGLM, ModelType
from summarize import summarize_spring_boot_folder
from utils.files import read_commit
from utils.git import checkout_to_parent_commit


def generate_summary_string(root_folder: str, commit_hash: str, max_workers=5, use_cache=False) -> str:
    if not use_cache:
        summary_result = summarize_spring_boot_folder(root_folder, max_workers)
        summary_return = ""
        for file, summary in summary_result.items():
            summary_return += f"\n文件：{file}\n摘要：{summary}\n"
        return summary_return
    else:
        cache_dir = 'cache'
        os.makedirs(cache_dir, exist_ok=True)
        cache_file_path = os.path.join(cache_dir, f"{commit_hash}.json")

        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as cache_file:
                summary_result = json.load(cache_file)
        else:
            summary_result = summarize_spring_boot_folder(root_folder, max_workers)
            with open(cache_file_path, 'w', encoding='utf-8') as cache_file:
                json.dump(summary_result, cache_file, ensure_ascii=False, indent=4)

        summary_return = ""
        for file, summary in summary_result.items():
            summary_return += f"\n文件：{file}\n摘要：{summary}\n"
        return summary_return


def read_and_replace_prompt(file_path: str, variables: dict) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        prompt = file.read()
    for key, value in variables.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)
    return prompt


if __name__ == "__main__":
    spring_boot_folder = project_root

    use_cache = input("Do you want to use cache? (N/y): ").strip().lower() == 'y'

    start_time = time.time()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # 遍历data文件夹
    data_folder = 'data'
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        commits = read_commit(file_path)
        for commit in commits:
            commit_type, commit_msg, commit_hash = commit
            checkout_to_parent_commit(project_root, commit_hash)

            if use_cache:
                summary_string = generate_summary_string(spring_boot_folder, commit_hash, 30, use_cache)
            else:
                summary_string = generate_summary_string(spring_boot_folder, commit_hash, 30, use_cache)

            prompt_file_path = 'prompt\\locate_with_summary.txt'
            variables = {
                "commit_type": commit_type,
                "commit_msg": commit_msg,
                "summary": summary_string,
            }
            prompt = read_and_replace_prompt(prompt_file_path, variables)

            model = ChatGLM(model_type=ModelType.GLM_4)

            result = model(prompt)

            # 提交对应类别 etc. single, multi, ...
            data_type = os.path.splitext(filename)[0]

            result_dir = os.path.join(f'result/locate_with_summary/{data_type}', commit_hash)
            os.makedirs(result_dir, exist_ok=True)
            result_file_path = os.path.join(result_dir, f"{timestamp}.txt")
            with open(result_file_path, 'w', encoding='utf-8') as result_file:
                result_file.write(str(result))

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.2f} seconds")
