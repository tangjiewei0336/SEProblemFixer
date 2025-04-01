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


if __name__ == "__main__":
    spring_boot_folder = project_root

    # 遍历data文件夹
    data_folder = 'data'
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        commits = read_commit(file_path)
        for commit in commits:
            commit_type, commit_msg, commit_hash = commit
            checkout_to_parent_commit(project_root, commit_hash)

            summary_string = generate_summary_string(spring_boot_folder)

            message = (f"Your mission whose type is {commit_type} is to {commit_msg}, here are the summary of "
                       f"codespace.\n")

            prompt = read_prompt(message + summary_string)

            model = ChatGLM(model_type=ModelType.GLM_4)

            result = model(prompt)

            filename_without_extension = os.path.splitext(filename)[0]
            result_dir = os.path.join('result', filename_without_extension)
            os.makedirs(result_dir, exist_ok=True)
            result_file_path = os.path.join(result_dir, f"{commit_hash}.txt")
            with open(result_file_path, 'w', encoding='utf-8') as result_file:
                result_file.write(str(result))
