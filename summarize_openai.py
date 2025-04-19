import os
import concurrent.futures

from openai import OpenAI

import config
from summarize import generate_prompt


def summarize_file(file_path, openai_client, openai_model):
    """
    读取文件内容，生成摘要。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 {file_path} 失败：{e}")
        return file_path, None, None

    prompt = generate_prompt(file_path, content)

    completion = openai_client.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": prompt},
        ],
    )

    summary = completion.choices[0].message.content

    return file_path, summary, prompt


def summarize_spring_boot_folder(root_folder, openai_client, openai_model, max_workers=5):
    """
    递归遍历 root_folder 下所有 Java 文件，并发生成摘要。
    """
    # 收集所有 .java 文件路径
    file_paths = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(".java"):
                file_paths.append(os.path.join(dirpath, filename))

    summaries = {}

    # 使用 ThreadPoolExecutor 并发处理文件
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(summarize_file, file, openai_client, openai_model): file for file in file_paths
        }

        for future in concurrent.futures.as_completed(future_to_file):
            file, summary, prompt = future.result()
            if summary:
                summaries[file] = summary

    return summaries


if __name__ == "__main__":
    spring_boot_folder = config.project_root

    client = OpenAI(
        api_key=config.deepseek_api_key,
        base_url=config.deepseek_base_url,
    )

    result = summarize_spring_boot_folder(spring_boot_folder, client, config.deepseek_model, max_workers=100)

    for file, summary, prompt in result.items():
        print(f"\nprompt: {prompt}\n文件：{file}\n摘要：{summary}\n")
