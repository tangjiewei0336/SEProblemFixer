# SEProblemFixer

## locate_with_questions_deepseek

### 环境配置

1. 安装pip模块

```shell
pip install --upgrade "openai>=1.0"
pip install --upgrade "volcengine-python-sdk[ark]"
```

2. 在`config.py`中配置`API_KEY`和`base_url`。

DeepSeeK官方的R1的API不支持JSON Output和Function Call，但火山引擎中的DeepSeeK-R1支持。

同时，获取摘要的函数使用了火山引擎批量推理功能降低成本，因此运行代码必须配置火山引擎。

```python
import os

deepseek_api_key = os.environ.get("ARK_API_KEY") # 记得设置系统环境变量`ARK_API_KEY`。
deepseek_base_url = "https://ark.cn-beijing.volces.com/api/v3"
deepseek_model = "" # your 在线推理 model Endpoint ID 
deepseek_bi_model = "" # your 批量推理 model Endpoint ID
```

### 运行说明

1. 在`prompt/deepseek/locate_with_questions.txt`中，可以自己定义提示词，提示词支持的变量有以下几种：
   - commit_hash, commit_message, commit_type
   - code_repo, summary
   
   通过定义这些提示词，你可以自定义输入的是代码仓库还是代码总结。

2. locate_deepseek.py支持summary, 修改`prompt/deepseek/locate_with_questions.txt`即可。

3. locate_ark_bi.py是调用火山引擎批量推理进行多线程批量处理所有的测试用例，暂不支持summary。

### 实验笔记

1. 最终实验代码还是没有使用Function Calling功能，因为火山引擎的文档中对Function Calling功能做了以下陈述。
   > Function Calling并不会增强模型能力， 并且FC模型综合能力不如pro
   > 
   > 不推荐使用其试图完成模型正常情况下做不到的事
   > 
   > 写代码、写sql、（无插件）解题等
   > 
   > 参考资料: [Function Calling 使用说明](https://www.volcengine.com/docs/82379/1262342#function-calling%E9%80%82%E7%94%A8%E5%9C%BA%E6%99%AF)

2. 使用DeepSeeK-R1进行多轮对话效果不好，无论如何修改System Prompt和User Prompt，模型从不询问问题。
