import os
import re
import concurrent.futures
from glm import ModelType, ChatGLM


import re

def extract_functions(file_content):
    pattern = r"""
        (?:@\w+(?:\s*\([^)]*\))?\s*)*
        (?:public|private|protected)?
        \s*
        (?:static\s+)?
        [\w<>\[\]]+
        \s+
        (\w+)
        \s*
        \([^)]*\)
        \s*
    """
    matches = re.finditer(pattern, file_content, re.VERBOSE | re.DOTALL)
    return [match.group(1) for match in matches]



def generate_prompt(file_path, file_content, rel_path=False, project_root=None):
    """
    生成摘要提示词，包括文件整体概述及函数功能描述。
    如果rel_path=True并且传入了project_root，则生成的prompt中包含的路径为相对路径。
    """
    functions = extract_functions(file_content)
    if (not rel_path) or (project_root is None):
        prompt = f"请用中文概括文件：{file_path}\n\n"
    else:
        # 计算相对路径
        rel_path = os.path.relpath(file_path, project_root)
        prompt = f"请用中文概括文件：{rel_path}\n\n"
    prompt += "【文件整体概括】：请总结该文件的主要功能和作用。\n\n"
    if functions:
        prompt += "【函数概括】：请分别概括下列函数的功能：\n" + "\n".join(f"- {func}" for func in functions) + "\n"
    else:
        prompt += "该文件未检测到明显的函数定义，请直接概括文件主体内容，如果它是一个实体类，则需要具体地概括其中每一个字段的作用。\n"
    prompt += "\n文件内容如下：\n" + file_content
    return prompt


def summarize_file(file_path, model):
    """
    读取文件内容，生成摘要。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 {file_path} 失败：{e}")
        return file_path, None

    prompt = generate_prompt(file_path, content)
    summary = model(prompt)
    return file_path, summary


def summarize_spring_boot_folder(root_folder, max_workers=5):
    """
    递归遍历 root_folder 下所有 Java 文件，并发生成摘要。
    """
    # 初始化 ChatGLM 模型
    model = ChatGLM(model_type=ModelType.GLM_4)

    # 收集所有 .java 文件路径
    file_paths = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(".java"):
                file_paths.append(os.path.join(dirpath, filename))

    summaries = {}

    # 使用 ThreadPoolExecutor 并发处理文件
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(summarize_file, file, model): file for file in file_paths}

        for future in concurrent.futures.as_completed(future_to_file):
            file, summary = future.result()
            if summary:
                summaries[file] = summary

    return summaries


if __name__ == "__main__":
    spring_boot_folder = "/Users/tangxiaoxia/IdeaProjects/autodrive"
    result = summarize_spring_boot_folder(spring_boot_folder, max_workers=10)

    for file, summary in result.items():
        print(f"\n文件：{file}\n摘要：{summary}\n")

    # 导出为excel
    import pandas as pd
    df = pd.DataFrame(list(result.items()), columns=['文件路径', '摘要'])
    output_file = "spring_boot_summaries.xlsx"
