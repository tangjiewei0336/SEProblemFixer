import os
import time
from enum import Enum
from typing import List, Optional, Any, ClassVar

import jwt
import requests
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.outputs import ChatResult, ChatGeneration


class ModelType(Enum):
    GLM_4 = ("glm-4-plus", "通用模型", 0.1)
    GLM_4V = ("glm-4v-plus-0111", "通用模型", 0.05)
    GLM_3_TURBO = ("glm-3-turbo", "通用模型", 0.001)
    CHAR_GLM_3 = ("charglm-3", "超拟人大模型", 0.015)
    GLM_4_AIR = ("glm-4-air", "通用模型", 0.001)
    GLM_4_AIRX = ("glm-4-airx", "通用模型", 0.01)
    GLM_4_FLASH = ("glm-4-flash", "通用模型", 0.0001)
    CODE_GEE_X_4 = ("codegeex-4", "代码模型", 0.0001)
    GLM_4_ALL_TOOLS = ("glm-4-alltools", "通用模型", 0.1)

    def __init__(self, model_code, model_type, cost_per_thousand_tokens):
        self.model_code = model_code
        self.model_type = model_type
        self.cost_per_thousand_tokens = cost_per_thousand_tokens

    @property
    def name_lower(self):
        return self.name.lower()


class ChatGLM(BaseChatModel):
    post_url: ClassVar[str] = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    api_key: Optional[str] = None
    model_type: Optional[ModelType] = ModelType.GLM_4_AIR

    def __call__(self, *args, **kwargs):
        messages = [HumanMessage(content="".join(args))]
        result = self.invoke(messages)
        return result.content if result.content else ""

    def __init__(self, api_key: Optional[str] = None, model_type: Optional[ModelType] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key if api_key else os.getenv('GLM_API_KEY')
        if model_type is not None and model_type != self.model_type:
            ChatGLM.model_type = model_type

        if not self.api_key:
            raise ValueError(
                "API key must be provided either as a parameter or through the GLM_API_KEY environment variable")


    def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> ChatResult:
        last_message = messages[-1]
        prompt = last_message.content

        post_data = {"model": self.model_type.model_code,
                     "messages": [
                         {
                             "role": "user",
                             "content": prompt
                         }
                     ]}
        print(prompt)

        header = {"Content-Type": "application/json",
                  "Authorization": f"Bearer {generate_token(self.api_key, 6000)}"}
        res = post_req(self.post_url, post_data, header)
        if res.status_code != 200:
            raise Exception(f"Error: {res.status_code} {res.text}")
        json_res = res.json()
        response = json_res['choices'][0]['message']['content']


        message = AIMessage(content=response)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "glm-4"


def generate_token(apikey: str, exp_seconds: int):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)

    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


def post_req(url, data, headers=None):
    post_headers = {}
    if headers:
        post_headers.update(headers)
    rsp = requests.post(url, json=data, headers=post_headers)
    return rsp
