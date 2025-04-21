"""
使用openai接口实现的总结文件
"""

import datetime
import os
import concurrent.futures

from openai import OpenAI

import config
from summarize import generate_prompt


def summarize_file(file_path, openai_client, openai_model, rel_path=False, project_root=None, print_log=False):
    """
    读取文件内容，生成摘要。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 {file_path} 失败：{e}")
        return file_path, None, None

    prompt = generate_prompt(file_path, content, rel_path, project_root)

    if print_log:
        print(f"prompt: \n{prompt}\n")

    completion = openai_client.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": prompt},
        ],
    )

    summary = completion.choices[0].message.content

    if print_log:
        print(f"summary：\n{summary}\n")

    return file_path, summary, prompt


def summarize_spring_boot_folder(root_folder, openai_client, openai_model, max_workers=5, rel_path=False,
                                 print_log=False):
    """
    递归遍历 root_folder 下所有 Java 文件，并发生成摘要。
    返回按文件路径排序的三元组列表(文件路径，摘要，prompt)。
    """
    # 收集所有 .java 文件路径
    file_paths = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(".java"):
                file_paths.append(os.path.join(dirpath, filename))

    results = []

    # 使用 ThreadPoolExecutor 并发处理文件
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(summarize_file, file, openai_client, openai_model, rel_path, root_folder, print_log): file
            for file in file_paths
        }

        for future in concurrent.futures.as_completed(future_to_file):
            file_path, summary, prompt = future.result()
            if summary:
                results.append((file_path, summary, prompt))

    # 按文件路径排序
    results.sort(key=lambda x: x[0])

    return results


if __name__ == "__main__":
    spring_boot_folder = config.project_root

    client = OpenAI(
        api_key=config.deepseek_api_key,
        base_url=config.deepseek_base_url,
    )

    result = summarize_spring_boot_folder(spring_boot_folder, client, config.deepseek_model, max_workers=1,
                                          rel_path=True, print_log=True)

    # 创建保存目录
    log_dir = os.path.join("logs", "summary_deepseek")
    os.makedirs(log_dir, exist_ok=True)

    # 创建带时间戳的文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{timestamp}.txt")

    # 写入文件
    with open(log_file, 'w', encoding='utf-8') as f:
        for file_path, summary, prompt in result:
            f.write(f"\nprompt: {prompt}\n文件：{file_path}\n摘要：{summary}\n")

    print(f"摘要结果已保存到 {log_file}")
