# 导入异步编程相关库，用于处理异步任务，异步编程中协程是核心概念
import asyncio
# 导入系统相关库，可用于与 Python 解释器和系统进行交互，如标准错误输出
import sys
# 导入操作系统相关库，用于访问操作系统的功能，如读取环境变量
import os
# 导入日期时间处理库，用于记录和计算程序的执行时间
from datetime import datetime
# 导入火山引擎异步 Ark 客户端库，用于与火山引擎的 Ark 服务进行异步通信
from volcenginesdkarkruntime import AsyncArk

import config
from utils.files import read_commit, read_and_replace_prompt, concat_code_files
from utils.git import checkout_to_parent_commit


def get_all_commits(data_folder="./data"):
    """
    commit = [(commit_type, commit_msg, commit_hash, filename)]
    """
    commits = []
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        commit = read_commit(file_path)
        for commit_tuple in commit:
            commit_type, commit_msg, commit_hash = commit_tuple
            new_commit = (commit_type, commit_msg, commit_hash, filename)
            commits.append(new_commit)
    return commits


async def worker(
        # asyncio task 的协程唯一标识，用���区分不同的工作协程
        worker_id: int,
        # 异步 Ark 客户端实例，用于调用批量聊天完成接口处理请求
        client: AsyncArk,
        # 待处理请求的队列，存储需要处理的请求
        requests: asyncio.Queue[dict],
):
    """
    异步协程函数，负责从队列中获取请求并处理。

    :param worker_id: 协程的唯一标识，用于在日志中区分不同的协程
    :param client: 异步 Ark 客户端实例，通过该实例调用服务接口处理请求
    :param requests: 待处理请求的队列，存储待处理的请求信息
    """
    while True:
        # 从队列中获取一个请求，若队列为空则会阻塞等待
        # 这里的 await 关键字用于暂停协程的执行，等待队列中有元素可供获取
        task_data = await requests.get()
        request = task_data['request']
        commit_info = task_data['commit_info']
        timestamp = task_data['timestamp']
        system_prompt = task_data['system_prompt']
        user_prompt = task_data['user_prompt']
        
        try:
            # 调用客户端的批量聊天完成接口处理请求，使用解包操作将请求字典作为参数传递
            # 同样使用 await 关键字暂停协程，等待接口调用完成
            completion = await client.batch_chat.completions.create(**request)

            reasoning_content = completion.choices[0].message.reasoning_content
            content = completion.choices[0].message.content

            # commit_info
            commit_type = commit_info["commit_type"]
            commit_msg = commit_info["commit_msg"]
            commit_hash = commit_info["commit_hash"]
            filename = commit_info["filename"]

            # 结果
            result_dir = f"result/locate_ark_bi/{filename}/{commit_hash}"
            os.makedirs(result_dir, exist_ok=True)
            result_file = f"{result_dir}/{timestamp}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                f.write(content)  # 保存最终回答

            # 日志
            logs_dir = f"logs/locate_ark_bi/{filename}/{commit_hash}"
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

        except Exception as e:
            # 若处理请求过程中出现异常，将错误信息打印到标准错误输出
            print(f"Error processing commit {commit_info['commit_hash']}: {e}", file=sys.stderr)
        finally:
            # 标记该请求已处理完成，通知队列该任务已结束
            requests.task_done()


async def main(project_root=config.project_root):
    """
    主函数，负责初始化客户端、生成请求、启动协程并监控任务完成情况。

    使用协程来实现并发处理请求，避免了使用线程带来的较大开销。
    多个协程可以在一个线程中并发执行，提高程序的性能。
    """
    # 记录程序开始执行的时间
    start = datetime.now()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # 定义协程数量和任务数量
    worker_num = 1000
    # 创建一个异步队列用于存储请求，该队列支持异步操作
    requests = asyncio.Queue()
    # 初始化异步 Ark 客户端
    client = AsyncArk(
        # 从环境变量中获取 API 密钥，确保密钥的安全性
        api_key=config.deepseek_api_key,
        # 设置超时时间为24小时，建议超时时间设置尽量大些，推荐24小时~72小时，避免因网络等原因导致请求超时
        timeout=24 * 3600,
    )

    # 获取所有的commit
    commits = get_all_commits()
    task_num = len(commits)

    # 将请求信息添加到队列中
    for i in range(task_num):
        commit_type = commits[i][0].rstrip(':')
        commit_msg = commits[i][1]
        commit_hash = commits[i][2]
        filename = commits[i][3]

        # 切换到目标commit的上一个commit
        checkout_result = checkout_to_parent_commit(project_root, commit_hash)
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
                "commit_hash": commit_hash,
                "commit_msg": commit_msg,
                "commit_type": commit_type,
                "code_repo": code_repo,
            },
        )

        request = {
            # 替换为你的批量推理接入点 ID，指定要调用的服务端点
            "model": config.deepseek_bi_model,
            "messages": [
                {
                    # 系统角色消息，用于设置��话的初始信息
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    # 用户角色消息，包含用户的具体问题
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }
        
        # 在队列中同时存储请求和commit信息
        commit_info = {
            "commit_type": commit_type,
            "commit_msg": commit_msg,
            "commit_hash": commit_hash,
            "filename": filename
        }
        
        await requests.put({
            "request": request,
            "commit_info": commit_info,
            "timestamp": timestamp,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        })
        
    # 创建 `worker_num` 个 asyncio task 的协程，并启动它们，每个协程负责处理队列中的请求
    # 这些协程会在一个线程中并发执行，通过协程的切换来提高效率
    tasks = [
        asyncio.create_task(worker(i, client, requests))
        for i in range(worker_num)
    ]
    # 等待所有请求处理完成，即队列中的所有任务都被标记为已完成
    await requests.join()
    # 停止所有协程，取消所有正在运行的任务
    for task in tasks:
        task.cancel()
    # 等待所有协程取消完成，确保所有任务都已停止
    await asyncio.gather(*tasks, return_exceptions=True)
    # 关闭客户端连接，释放资源
    await client.close()
    # 记录程序结束执行的时间
    end = datetime.now()
    # 打印程序总执行时间和处理的总任务数
    print(f"Total time: {end - start}, Total task: {task_num}")


if __name__ == "__main__":
    # 运行异步主函数，启动整个程序
    # asyncio.run() 会创建一个事件循环，并在这个事件循环中运行主协程
    asyncio.run(main())
