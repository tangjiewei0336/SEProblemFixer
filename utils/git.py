import subprocess
import os
from typing import Tuple


def checkout_to_parent_commit(project_root: str, commit_hash: str) -> Tuple[bool, str]:
    """
    将Git仓库检出到指定提交哈希值的父提交（上一次提交）。

    参数:
        project_root (str): 项目根目录的路径
        commit_hash (str): 指定提交的哈希值，将检出到它的父提交

    返回:
        Tuple[bool, Optional[str]]: (成功标志, 错误信息或父提交哈希)
    """
    try:
        # 确保project_root是一个有效的目录
        if not os.path.isdir(project_root):
            return False, f"指定的路径不是一个有效的目录: {project_root}"

        # 确保是一个Git仓库
        git_dir = os.path.join(project_root, ".git")
        if not os.path.isdir(git_dir):
            return False, f"指定的目录不是一个Git仓库: {project_root}"

        # 获取指定提交的父提交哈希值
        cmd_parent = ["git", "-C", project_root, "rev-parse", f"{commit_hash}~1"]
        result_parent = subprocess.run(cmd_parent, capture_output=True, text=True)

        if result_parent.returncode != 0:
            return (
                False,
                f"无法找到提交 {commit_hash} 的父提交: {result_parent.stderr.strip()}",
            )

        parent_hash = result_parent.stdout.strip()

        # 执行Git checkout命令检出到父提交
        cmd_checkout = ["git", "-C", project_root, "checkout", parent_hash]
        result_checkout = subprocess.run(cmd_checkout, capture_output=True, text=True)

        # 检查命令是否成功执行
        if result_checkout.returncode != 0:
            return False, f"检出失败: {result_checkout.stderr.strip()}"

        return True, f"成功检出到父提交 {parent_hash}"
    except Exception as e:
        return False, f"发生错误: {str(e)}"
