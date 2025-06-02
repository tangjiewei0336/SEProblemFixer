import os
import tempfile
import json
import sys
from datetime import datetime
from contextlib import redirect_stdout
from code_change import get_code_change_result
from glm import ModelType
from locate import locate
from locate_with_questions import display_commit_list
from modifier.modify_code import JavaCodeModifier
from utils.git import checkout_to_parent_commit
from config import project_root

class TeeOutput:
    """同时输出到文件和控制台"""
    def __init__(self, file_path):
        self.terminal = sys.stdout
        self.log = open(file_path, 'w', encoding='utf-8')
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()

if __name__ == "__main__":
    # 获取需要测试的commit
    commit_type, commit_msg, commit_hash, commit_filename = display_commit_list()
    commit_data_type = os.path.splitext(commit_filename)[0]

    # 创建日志文件
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_filename = f"logs/{commit_data_type}/{commit_hash}/{timestamp}.txt"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)

    # 重定向输出
    tee = TeeOutput(log_filename)
    sys.stdout = tee
    
    try:
        checkout_result = checkout_to_parent_commit(project_root, commit_hash)
        if not checkout_result[0]:
            print("git checkout fail:")
            print(checkout_result)
            exit()
        else:
            print("git checkout success")
        
        locate_history = locate(commit_type, commit_msg, commit_hash, commit_data_type)
        locate_result = locate_history[-1]["content"]

        code_change_result = get_code_change_result(project_root, commit_hash, commit_type, commit_msg, ModelType.GLM_4, locate_result)
        
        if code_change_result.startswith("```json"):
            code_change_result = code_change_result[7:]  # 去除前置的```json
        if code_change_result.endswith("```"):
            code_change_result = code_change_result[:-3]  # 去除后置的```
        code_change_result = code_change_result.strip()  # 去除首尾空白字符

        print("Model Code Change Answers: \n", code_change_result)

        print("Applying Code Changes...")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(code_change_result)
            temp_file_path = temp_file.name

        modifier = JavaCodeModifier(temp_file_path)
        modifier.apply_changes()
        
        print("Pipeline execution completed")
        
    finally:
        # 恢复标准输出
        sys.stdout = tee.terminal
        tee.close()
        print(f"日志已保存到: {log_filename}")