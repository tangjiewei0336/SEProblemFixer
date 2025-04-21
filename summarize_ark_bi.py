"""
使用火山引擎的批量推理实现的总结文件
"""
import asyncio
import datetime
import os
from volcenginesdkarkruntime import AsyncArk

import config
from summarize import generate_prompt


async def summarize_file(file_path, ark_client, ark_bi_model, rel_path=False, project_root=None, print_log=False):
    """
    读取文件内容，生成摘要。
    rel_path为True时，返回的也是相对路径而非绝对路径。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 {file_path} 失败：{e}")
        return file_path, None, None

    prompt = generate_prompt(file_path, content, rel_path, project_root)

    file_path_rel = file_path
    if rel_path:
        file_path_rel = os.path.relpath(file_path, project_root)

    if print_log:
        print(f"prompt: \n{prompt}\n")

    try:
        completion = await ark_client.batch_chat.completions.create(
            model=ark_bi_model,
            messages=[
                {"role": "system", "content": prompt},
            ],
        )

        summary = completion.choices[0].message.content

        if print_log:
            print(f"summary：\n{summary}\n")

        if rel_path:
            return file_path_rel, summary, prompt
        else:
            return file_path, summary, prompt
    except Exception as e:
        print(f"生成摘要失败：{e}")

        if rel_path:
            return file_path_rel, None, prompt
        else:
            return file_path, None, prompt


async def summarize_spring_boot_folder(root_folder, ark_client, ark_bi_model, rel_path=False, print_log=False):
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

    tasks = [summarize_file(file, ark_client, ark_bi_model, rel_path, root_folder, print_log) for file in file_paths]

    results = await asyncio.gather(*tasks)

    return results


async def generate_summaries(root_folder, ark_client, ark_bi_model):
    summaries_data = await summarize_spring_boot_folder(
        root_folder,
        ark_client,
        ark_bi_model,
        rel_path=True
    )

    # 格式化摘要
    formatted_summaries = ""
    for file_path, summary, _ in summaries_data:
        if summary:
            formatted_summaries += f"文件: {file_path}\n摘要:\n{summary}\n"

    return formatted_summaries


if __name__ == "__main__":
    spring_boot_folder = config.project_root

    ark_client = AsyncArk()


    async def run():
        result = await summarize_spring_boot_folder(spring_boot_folder, ark_client, config.deepseek_bi_model,
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


    asyncio.run(run())
