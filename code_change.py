import datetime
import json
import os
import time

from config import project_root
from glm import ModelType, ChatGLM
from locate_with_questions import display_commit_list, locate_with_questions
from utils.files import concat_code_files, read_and_replace_prompt
from utils.git import checkout_to_parent_commit
from utils.tool.file_viewer import get_file_content


def get_code_change_result(sb_project_root, commit_hash, commit_type, commit_message, data_type, model_type,
                           locate_result):
    checkout_result = checkout_to_parent_commit(sb_project_root, commit_hash)
    if not checkout_result[0]:
        print("git checkout 失败")
        print(checkout_result)
        exit()

    code_repo = concat_code_files(
        sb_project_root, filter=lambda x: x.endswith(".java"), use_relative_path=True
    )

    prompt = read_and_replace_prompt(
        "prompt/code_change.txt",
        {
            "commit_hash": commit_hash,
            "commit_msg": commit_message,
            "commit_type": commit_type,
            "code_repo": code_repo,
            "code_modification_example": get_file_content("modifier", "code_modification_example.json"),
            "locate_result": locate_result,
            "repo_name": "autodrive",
        },
    )

    model = ChatGLM(model_type=model_type)

    result = model(prompt)

    return result


if __name__ == "__main__":
    start_time = time.time()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    spring_boot_folder = project_root

    selected_commit = display_commit_list()
    selected_commit_type = selected_commit[0]
    selected_commit_msg = selected_commit[1]
    selected_commit_hash = selected_commit[2]
    selected_commit_filename = selected_commit[3]
    selected_commit_data_type = os.path.splitext(selected_commit_filename)[0]

    print(f"\n已选择: Commit {selected_commit_hash} - {selected_commit_msg}")

    locate_result_json = locate_with_questions(spring_boot_folder,
                                               selected_commit_hash, selected_commit_msg, selected_commit_type,
                                               selected_commit_data_type,
                                               ModelType.GLM_4, timestamp)[0]

    locate_result_str = json.dumps(locate_result_json, indent=2, ensure_ascii=False)

    print("\n\n正在获取代码修改结果...\n\n")

    code_change = get_code_change_result(spring_boot_folder, selected_commit_hash, selected_commit_type,
                                         selected_commit_msg, selected_commit_data_type, ModelType.GLM_4,
                                         locate_result_str)

    print("Model Answers: \n", code_change)
