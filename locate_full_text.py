import datetime
import os

from config import project_root
from glm import ChatGLM, ModelType
from utils.files import concat_code_files, read_commit, read_prompt
from utils.git import checkout_to_parent_commit


def concat_java_code_files(root_folder: str) -> str:
    return concat_code_files(root_folder, filter=lambda x: x.endswith(".java"))


def generate_full_code_string_cached(root_folder: str, comment_hash: str) -> str:
    """带缓存的完整代码处理"""
    cache_dir = "cache/full_code"
    os.makedirs(cache_dir, exist_ok=True)
    cache_file_path = os.path.join(cache_dir, f"{comment_hash}.txt")

    if os.path.exists(cache_file_path):
        with open(cache_file_path, "r", encoding="utf-8") as cache_file:
            return cache_file.read()
    else:
        full_code = concat_java_code_files(root_folder)
        with open(cache_file_path, "w", encoding="utf-8") as cache_file:
            cache_file.write(full_code)
        return full_code


if __name__ == "__main__":
    # 遍历data文件夹中的提交记录
    data_folder = "data"
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        commits = read_commit(file_path)

        for commit in commits:
            commit_type, commit_msg, commit_hash = commit
            checkout_to_parent_commit(project_root, commit_hash)

            # 获取完整代码内容（带缓存）
            code_content = generate_full_code_string_cached(project_root, commit_hash)

            # 构建提示词
            message = (
                f"Your mission whose type is {commit_type} is to {commit_msg}, "
                "here is the FULL CODE CONTENT of the project:\n\n"
                f"{code_content}\n\nPlease analyze and locate the modification points."
            )

            prompt = read_prompt(message)

            # 调用模型
            model = ChatGLM(model_type=ModelType.GLM_4)
            result = model(prompt)

            # 保存结果

            data_type = os.path.splitext(filename)[0]
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

            result_dir = os.path.join(f'result/locate_full_text/{data_type}', commit_hash)
            os.makedirs(result_dir, exist_ok=True)
            result_file_path = os.path.join(result_dir, f"{timestamp}.txt")

            with open(result_file_path, "w", encoding="utf-8") as f:
                f.write(str(result))
