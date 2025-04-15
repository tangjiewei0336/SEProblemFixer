import os


def read_and_replace_prompt(file_path: str, variables: dict) -> str:
    """
    从指定文件中读取文本，
    并将其中的{{var}}替换成对应的文本。
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        prompt = file.read()
    for key, value in variables.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)
    return prompt


def concat_code_files(root_path: str, filter: callable, use_relative_path: bool = False) -> str:
    """
    递归遍历路径下所有文件夹中的代码文件，
    将文件名和内容组合成一个字符串
    
    参数：
    root_path: 要遍历的根路径
    filter: 用于过滤文件的函数
    use_relative_path: 是否使用相对路径作为文件名，默认为False
    """
    result = ""

    for root, dirs, files in os.walk(root_path):
        for file in files:
            file_path = os.path.join(root, file)
            if filter(file):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if use_relative_path:
                            relative_path = os.path.relpath(file_path, root_path)
                            file_display = relative_path
                        else:
                            file_display = file
                        result += f"文件名: {file_display}\n内容:\n{content}\n\n"
                except Exception as e:
                    print(f"无法读取文件: {file_path}, 原因: {e}")

    return result


def read_commit(file: str) -> list:
    """
    获取文件中的commit msg和提交哈希值
    返回一个列表，每个元素是一个元组(commit type, commit msg, commit hash)
    """
    if not os.path.exists(file):
        raise FileNotFoundError(f"文件 {file} 不存在")
    if not os.path.isfile(file):
        raise ValueError(f"路径 {file} 不是一个文件")
    result = []
    with open(file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            commit = line.strip().split(" ")
            if len(commit) != 3:
                raise ValueError(f"文件 {file} 中的行格式不正确: {line.strip()}")
            result.append(tuple(commit))
    return result


def read_prompt(content: str) -> str:
    """
    返回prompt, 将{{content}}替换为传入的字符串
    """
    file_path = "prompt_convention"
    with open(file_path, "r", encoding="utf-8") as file:
        prompt = file.read()
        prompt = prompt.replace("{{content}}", content)
        return prompt
