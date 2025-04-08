import datetime
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import project_root
from glm import ChatGLM, ModelType
from summarize import summarize_spring_boot_folder
from utils.files import read_commit
from utils.git import checkout_to_parent_commit


def generate_summary_string(root_folder: str, commit_hash: str, max_workers=5) -> str:
    checkout_to_parent_commit(project_root, commit_hash)
    summary_result = summarize_spring_boot_folder(root_folder, max_workers)
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


def process_commit(commit, timestamp):
    commit_type, commit_msg, commit_hash, filename, summary = commit

    prompt_file_path = 'prompt\\locate_with_summary.txt'
    variables = {
        "commit_type": commit_type,
        "commit_msg": commit_msg,
        "summary": summary,
    }
    prompt = read_and_replace_prompt(prompt_file_path, variables)

    model = ChatGLM(model_type=ModelType.GLM_4)
    result = model(prompt)

    data_type = os.path.splitext(filename)[0]
    
    # 保存结果
    result_dir = os.path.join(f'result/locate_with_summary/{data_type}', commit_hash)
    os.makedirs(result_dir, exist_ok=True)
    result_file_path = os.path.join(result_dir, f"{timestamp}.txt")
    with open(result_file_path, 'w', encoding='utf-8') as result_file:
        result_file.write(str(result))
    
    # 保存日志（包含prompt和模型返回）
    logs_dir = os.path.join(f'logs/locate_with_summary/{data_type}', commit_hash)
    os.makedirs(logs_dir, exist_ok=True)
    logs_file_path = os.path.join(logs_dir, f"{timestamp}.txt")
    with open(logs_file_path, 'w', encoding='utf-8') as logs_file:
        logs_file.write(f"Prompt:\n{prompt}\n\nResponse:\n{result}")


if __name__ == "__main__":
    spring_boot_folder = project_root

    start_time = time.time()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    data_folder = 'data'
    # commit = [(commit_type, commit_msg, commit_hash, filename, summary)]
    commits = []
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        commit = read_commit(file_path)
        for commit_tuple in commit:
            commit_type, commit_msg, commit_hash = commit_tuple
            summary = generate_summary_string(spring_boot_folder, commit_hash, 50)
            new_commit = (commit_type, commit_msg, commit_hash, filename, summary)
            commits.append(new_commit)

    total_amount = len(commits)

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for commit in commits:
            futures.append(
                executor.submit(process_commit, commit, timestamp))

        for future in as_completed(futures):
            future.result()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.2f} seconds")
