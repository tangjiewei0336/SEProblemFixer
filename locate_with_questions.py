import datetime
import os
import time
import json
import re

from config import project_root
from glm import ChatGLM, ModelType
from utils.files import read_commit, concat_code_files, read_and_replace_prompt
from utils.git import checkout_to_parent_commit
from utils.tool.file_viewer import ToolParser, get_file_content


def display_commit_list(commits=None, data_folder="./data"):
    """
    展示所有commit并让用户选择一个
    """
    if commits is None:
        # 将所有需要测试的commit取出
        # commit = [(commit_type, commit_msg, commit_hash, filename)]
        commits = []
        for filename in os.listdir(data_folder):
            file_path = os.path.join(data_folder, filename)
            commit = read_commit(file_path)
            for commit_tuple in commit:
                commit_type, commit_msg, commit_hash = commit_tuple
                new_commit = (commit_type, commit_msg, commit_hash, filename)
                commits.append(new_commit)

    print("\n可用的commit列表:")
    print("-" * 80)
    for i, commit in enumerate(commits):
        commit_type, commit_msg, commit_hash, filename = commit
        print(
            f"[{i + 1}] Hash: {commit_hash[:8]} | 类型: {commit_type} | 文件: {filename}"
        )
        print(f"    消息: {commit_msg}")
        print("-" * 80)

    while True:
        try:
            choice = int(input("\n请选择一个commit (输入对应的序号): "))
            if 1 <= choice <= len(commits):
                return commits[choice - 1]
            else:
                print(f"错误: 请输入1到{len(commits)}之间的数字")
        except ValueError:
            print("错误: 请输入有效的数字")


def interactive_code_analysis(model, initial_prompt):
    """
    与模型进行多轮对话，处理模型的问题直到获得最终结果
    返回分析结果和完整对话历史
    """
    print("\n开始多轮对话分析代码...\n")

    # 初始化对话历史
    messages = [{"role": "user", "content": initial_prompt}]

    while True:
        # 打印分隔线
        print("-" * 80)
        print("正在与模型交流，请稍候...")

        # 将对话历史发送给模型
        response = model.chat(messages)
        model_reply = response.content

        # 将模型回复添加到对话历史
        messages.append({"role": "assistant", "content": model_reply})

        # 检查模型回复是否包含JSON结果
        # 使用正则表达式更精确地匹配JSON数组
        json_pattern = r'\[\s*\{\s*"[^"]+"\s*:.*?\}\s*\]'
        json_matches = re.search(json_pattern, model_reply, re.DOTALL)

        if json_matches:
            try:
                json_str = json_matches.group(0)
                # 尝试清理JSON字符串中的可能干扰字符
                json_str = json_str.strip()
                print("\n检测到JSON结果，尝试解析...")
                result = json.loads(json_str)

                print("\n分析完成! 模型已确定需要修改的函数。")
                return result, messages  # 同时返回结果和对话历史
            except json.JSONDecodeError as e:
                print(f"\n检测到JSON格式但解析失败: {e}")
                print(f"原始JSON字符串: {json_str}")

                # 尝试手动提取结果
                if model_reply.strip().startswith("[") and "]" in model_reply:
                    json_start = model_reply.find("[")
                    json_end = model_reply.rfind("]") + 1
                    json_str = model_reply[json_start:json_end]
                    try:
                        result = json.loads(json_str)
                        print("\n使用备用方法成功解析JSON!")
                        return result, messages  # 同时返回结果和对话历史
                    except json.JSONDecodeError:
                        pass

        # 如果不是JSON结果，则是模型在提问
        print("\n模型的问题:")
        print(model_reply)

        # 如果模型的回复中包含xml格式的工具调用信息
        content = ""
        if "<tool>" in model_reply and "</tool>" in model_reply:
            print("\n检测到工具调用信息，正在解析...")

            # 提取工具调用信息
            tool_info_str = "<tool>" + model_reply.split("<tool>")[1].split("</tool>")[0] + "</tool>"
            parser = ToolParser(tool_info_str)
            parser.parse()
            tool_info = parser.get_tool_info()
            try:
                content = get_file_content(
                    project_root + tool_info["filepath"],
                    tool_info["filename"],
                )
            except Exception as e:
                print(f"获取文件内容时发生错误: {e}")

            print("工具调用信息解析完成!")
            print(content)

        # 获取用户回答
        user_reply = input("\n请回答模型的问题: ")
        messages.append({"role": "user", "content": content + user_reply})


if __name__ == "__main__":
    spring_boot_folder = project_root

    start_time = time.time()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    data_folder = "data"

    # 显示所有commit并让用户选择一个
    selected_commit = display_commit_list()
    selected_commit_type = selected_commit[0]
    selected_commit_msg = selected_commit[1]
    selected_commit_hash = selected_commit[2]
    selected_commit_filename = selected_commit[3]

    print(f"\n已选择: Commit {selected_commit_hash} - {selected_commit_msg}")

    checkout_result = checkout_to_parent_commit(project_root, selected_commit_hash)
    if not checkout_result[0]:
        print("git checkout 失败")
        print(checkout_result)
        exit()

    code_repo = concat_code_files(
        project_root, filter=lambda x: x.endswith(".java"), use_relative_path=True
    )

    prompt = read_and_replace_prompt(
        "prompt/locate_with_questions.txt",
        {
            "commit_hash": selected_commit_hash,
            "commit_msg": selected_commit_msg,
            "commit_type": selected_commit_type,
            "code_repo": code_repo,
        },
    ) + "\n\n" + get_file_content("prompt/tools", "general.md") + "\n\n" + get_file_content("prompt/tools", "file_viewer.md")

    model = ChatGLM(model_type=ModelType.GLM_4)

    # 使用多轮对话替代单次调用，并获取完整对话历史
    result, conversation_history = interactive_code_analysis(model, prompt)

    # 输出最终结果
    print("\n需要修改的函数:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 保存结果到文件
    data_type = os.path.splitext(selected_commit_filename)[0]

    # 保存结果
    result_dir = os.path.join(
        f"result/locate_with_questions/{data_type}", selected_commit_hash
    )
    os.makedirs(result_dir, exist_ok=True)
    result_file_path = os.path.join(result_dir, f"{timestamp}.txt")
    with open(result_file_path, "w", encoding="utf-8") as result_file:
        result_file.write(json.dumps(result, indent=2, ensure_ascii=False))

    # 保存日志（包含完整的对话历史）
    logs_dir = os.path.join(
        f"logs/locate_with_questions/{data_type}", selected_commit_hash
    )
    os.makedirs(logs_dir, exist_ok=True)
    logs_file_path = os.path.join(logs_dir, f"{timestamp}.txt")
    with open(logs_file_path, "w", encoding="utf-8") as logs_file:
        logs_file.write("=== 完整对话历史 ===\n\n")
        # 格式化输出对话历史
        for i, msg in enumerate(conversation_history):
            role = msg["role"].capitalize()
            content = msg["content"]
            logs_file.write(f"--- {role} [{i + 1}/{len(conversation_history)}] ---\n")
            logs_file.write(f"{content}\n\n")

        logs_file.write("=== 最终结果 ===\n\n")
        logs_file.write(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n结果已保存至: {result_file_path}")
    print(f"日志已保存至: {logs_file_path}")
