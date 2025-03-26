import os
import re

from glm import ModelType, ChatGLM


def extract_functions(file_content):
    """
    利用正则从文件内容中提取函数定义部分（适用于 Java 文件的简单匹配）。
    这里的匹配规则仅为示例，实际情况中可能需要更复杂的解析逻辑。
    """
    # 匹配 public/private/protected 开头，后面跟着返回类型、函数名及括号
    pattern = r'(public|private|protected)\s+(static\s+)?[\w<>\[\]]+\s+(\w+)\s*\(.*?\)\s*\{'
    matches = re.finditer(pattern, file_content, re.DOTALL)
    functions = []
    for match in matches:
        # 提取函数名称
        func_name = match.group(3)
        functions.append(func_name)
    return functions


def generate_prompt(file_path, file_content):
    """
    构造对文件的概括请求，要求摘要中包含文件主体以及每个函数的说明。
    """
    # 提取函数列表
    functions = extract_functions(file_content)
    prompt = f"请用中文概括文件：{file_path}\n\n"
    prompt += "【文件整体概括】：请总结该文件的主要功能和作用。\n\n"
    if functions:
        prompt += "【函数概括】：请分别概括下列函数的功能：\n"
        for func in functions:
            prompt += f"- {func}\n"
    else:
        prompt += "该文件未检测到明显的函数定义，请直接概括文件主体内容。\n"
    prompt += "\n文件内容如下：\n"
    prompt += file_content
    return prompt


def summarize_file(file_path, model):
    """
    读取文件内容，构造 prompt 并调用 ChatGLM 生成摘要。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 {file_path} 失败：{e}")
        return None

    prompt = generate_prompt(file_path, content)
    summary = model(prompt)
    return summary


def summarize_spring_boot_folder(root_folder):
    """
    递归遍历 root_folder 下所有文件，对每个文件生成摘要，
    返回一个字典，key 为文件路径，value 为摘要内容。
    """
    summaries = {}
    # 初始化 ChatGLM 模型
    model = ChatGLM(model_type=ModelType.GLM_4)

    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            # 根据需要过滤文件类型，比如只处理 .java 文件
            if not filename.endswith(".java"):
                continue
            file_path = os.path.join(dirpath, filename)
            print(f"处理文件：{file_path}")
            summary = summarize_file(file_path, model)
            if summary:
                summaries[file_path] = summary
    return summaries


if __name__ == "__main__":
    # 指定 Spring Boot 项目的根目录
    spring_boot_folder = "/Users/tangxiaoxia/IdeaProjects/autodrive"
    result = summarize_spring_boot_folder(spring_boot_folder)
    # 输出结果
    for file, summary in result.items():
        print(f"\n文件：{file}\n摘要：{summary}\n")
