# SEProblemFixer

## locate_with_questions_deepseek

### 环境配置

1. 安装pip模块

```shell
pip install --upgrade "openai>=1.0"
pip install --upgrade "volcengine-python-sdk[ark]"
```

2. 在`config.py`中配置`API_KEY`和`base_url`。

DeepSeeK官方的R1的API不支持JSON Output和Function Call，但火山引擎中的DeepSeeK-R1支持，因此，这里以火山引擎配置为例。

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
