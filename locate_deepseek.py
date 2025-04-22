import asyncio
import datetime
import os
import time

from openai import OpenAI
from volcenginesdkarkruntime import AsyncArk

import config
import summarize_ark_bi
from config import project_root
from locate_with_questions import display_commit_list
from utils.files import concat_code_files, read_and_replace_prompt
from utils.git import checkout_to_parent_commit


if __name__ == "__main__":
    start_time = time.time()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    spring_boot_folder = project_root
    data_folder = "data"

    # 显示所有commit并让用户选择一个
    selected_commit = display_commit_list()
    selected_commit_type = selected_commit[0].rstrip(':')
    selected_commit_msg = selected_commit[1]
    selected_commit_hash = selected_commit[2]
    selected_commit_filename = selected_commit[3]

    print(f"\n已选择: Commit {selected_commit_hash} - {selected_commit_msg}")

    # 切换到目标commit的上一个commit
    checkout_result = checkout_to_parent_commit(project_root, selected_commit_hash)
    if not checkout_result[0]:
        print("git checkout 失败")
        print(checkout_result)
        exit()

    code_repo = concat_code_files(
        project_root, filter=lambda x: x.endswith(".java"), use_relative_path=True
    )

    system_prompt = read_and_replace_prompt(
        "prompt/deepseek/json_output.txt",
        {},
    )

    user_prompt = read_and_replace_prompt(
        "prompt/deepseek/locate.txt",
        {
            "commit_hash": selected_commit_hash,
            "commit_msg": selected_commit_msg,
            "commit_type": selected_commit_type,
            "code_repo": code_repo,
        },
    )

    if "{{summary}}" in user_prompt:
        print("正在生成摘要...")
        summary_time_start = time.time()

        ark_client = AsyncArk()
        summaries = asyncio.run(
            summarize_ark_bi.generate_summaries(spring_boot_folder, ark_client, config.deepseek_bi_model))
        user_prompt = user_prompt.replace("{{summary}}", summaries)

        summary_time_end = time.time()
        summary_time = summary_time_end - summary_time_start
        print(f"摘要生成完成，耗时: {summary_time:.2f}秒")

    print("=== System Prompt ===\n", end="")
    print(system_prompt, end="")
    print("\n\n=== User Prompt ===\n", end="")
    print(user_prompt, end="")

    client = OpenAI(
        api_key=config.deepseek_api_key,
        base_url=config.deepseek_base_url,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    completion = client.chat.completions.create(
        model=config.deepseek_model,
        messages=messages,
        response_format={
            'type': 'json_object'
        },
        stream=True,
    )

    reasoning_content = ""
    content = ""

    reasoning_content_log = False
    content_log = False

    for chunk in completion:
        if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
            if not reasoning_content_log:
                reasoning_content_log = True
                print("\n\n=== Reasoning Content ===\n", end="")
            reasoning_content += chunk.choices[0].delta.reasoning_content
            print(chunk.choices[0].delta.reasoning_content, end="")
        else:
            if not content_log:
                content_log = True
                print("\n\n=== Content ===\n", end="")
            content += chunk.choices[0].delta.content
            print(chunk.choices[0].delta.content, end="")

    # 结果
    result_dir = f"result/locate_deepseek/{selected_commit_filename}/{selected_commit_hash}"
    os.makedirs(result_dir, exist_ok=True)
    result_file = f"{result_dir}/{timestamp}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        f.write(content)  # 保存最终回答

    # 日志
    logs_dir = f"logs/locate_deepseek/{selected_commit_filename}/{selected_commit_hash}"
    os.makedirs(logs_dir, exist_ok=True)
    logs_file = f"{logs_dir}/{timestamp}.txt"
    with open(logs_file, "w", encoding="utf-8") as f:
        f.write("=== System Prompt ===\n")
        f.write(system_prompt)
        f.write("\n\n=== User Prompt ===\n")
        f.write(user_prompt)
        f.write("\n\n=== Reasoning Content ===\n")
        f.write(reasoning_content)
        f.write("\n\n=== Content ===\n")
        f.write(content)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"总耗时: {total_time:.2f}秒")
