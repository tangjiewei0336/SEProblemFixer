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


def get_code_change_result(sb_project_root, commit_hash, commit_type, commit_message, model_type, locate_result):
    checkout_result = checkout_to_parent_commit(sb_project_root, commit_hash)
    if not checkout_result[0]:
        print("git checkout 失败")
        print(checkout_result)
        exit()
    
    locate_result = locate_result.replace("```json", "").replace("```", "").strip()
    locate_result_json = json.loads(locate_result)
    related_files = dict()
    for item in locate_result_json:
        related_files[item["file"]] = get_file_content(item["file"])

    prompt = read_and_replace_prompt(
        "prompt/code_change.txt",
        {
            "commit_hash": commit_hash,
            "commit_msg": commit_message,
            "commit_type": commit_type,
            "code_modification_example": get_file_content("modifier/code_modification_example.json"),
            "locate_result": locate_result,
            "repo_name": "autodrive",
            "code_change_schema": get_file_content("modifier/code-change.schema.json"),
            "related_files": str(related_files),
        },
    )

    print("\n\n==========Prompt for Code Change==========")
    print(prompt)
    print("==========End of Prompt for Code Change==========\n\n")
    print("Asking LLM for Code Changing...")

    model = ChatGLM(model_type=model_type)

    result = model(prompt)

    return str(result)


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

    locate_result_json, locate_conversation = locate_with_questions(spring_boot_folder,
                                                                    selected_commit_hash, selected_commit_msg,
                                                                    selected_commit_type,
                                                                    selected_commit_data_type,
                                                                    ModelType.GLM_4, timestamp)

    locate_result_str = json.dumps(locate_result_json, indent=2, ensure_ascii=False)

    print("\n\n正在获取代码修改结果...\n\n")

    code_change_result = get_code_change_result(spring_boot_folder, selected_commit_hash, selected_commit_type,
                                                selected_commit_msg, ModelType.GLM_4, locate_result_str)

    print("Model Answers: \n", code_change_result)

    result_path = f"result/code_change/{selected_commit_data_type}/{selected_commit_hash}/{timestamp}.txt"
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as result_file:
        result_file.write(code_change_result)
    print(f"结果已保存至: {result_path}")

    log_path = f"logs/code_change/{selected_commit_data_type}/{selected_commit_hash}/{timestamp}.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("=== 完整对话历史 ===\n\n")
        # 格式化输出对话历史
        for i, msg in enumerate(locate_conversation):
            role = msg["role"].capitalize()
            content = msg["content"]
            log_file.write(f"--- {role} [{i + 1}/{len(locate_conversation)}] ---\n")
            log_file.write(f"{content}\n\n")

        log_file.write("\n=== 定位最终结果 ===\n\n")
        log_file.write(locate_result_str)
        log_file.write("\n=== 代码修改最终结果 ===\n\n")
        log_file.write(code_change_result)
