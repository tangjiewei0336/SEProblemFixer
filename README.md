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
