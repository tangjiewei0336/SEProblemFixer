# https://docs.qq.com/doc/DYVhNTG5RaUlYbVZO

import openai
import os
def query_gpt4(question):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.base_url = 'https://4.0.wokaai.com/v1/'

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    )
    print(response)
    return response.choices[0].message.content


