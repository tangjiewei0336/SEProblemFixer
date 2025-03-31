import os


def concat_code_files(root_path: str, filter: callable) -> str:
    """
    递归遍历路径下所有文件夹中的代码文件，
    将文件名和内容组合成一个字符串
    """
    result = ""

    for root, dirs, files in os.walk(root_path):
        for file in files:
            file_path = os.path.join(root, file)
            if filter(file):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        result += f"文件名: {file}\n内容:\n{content}\n\n"
                except Exception as e:
                    print(f"无法读取文件: {file_path}, 原因: {e}")

    return result


def read_commit(file: str) -> list:
    """
    获取文件中的commit msg和提交哈希值
    返回一个列表，每个元素是一个元组(commit type, commit msg, commit hash)
    """
    with open(file, "r", encoding="utf-8") as f:
        return [tuple(line.strip().split(" ")) for line in f.readlines()]
