import os

import requests
from typing import List, Optional, Any
from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document



class GLMEmbeddings(Embeddings):
    api_url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
    api_key: Optional[str] = None


    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key if api_key else os.getenv('GLM_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as a parameter or through the API_KEY environment variable")

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        embeddings = []
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        for doc in documents:
            doc_text = clean_doc_format(doc)
            response = requests.post(
                self.api_url,
                headers=headers,
                json={"model": "embedding-2", "input": doc_text}
            )
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code} {response.text}")
            json_response = response.json()
            embeddings.append(json_response['data'][0]['embedding'])
            # self.logger.log(
            #     f"Embedding Serv Summary: token={str(json_response['usage']['prompt_tokens'])}+"
            #     f"{str(json_response['usage']['completion_tokens'])} "
            #     f"spending={json_response['usage']['total_tokens'] * 0.0005 / 1000:.4f}CNY",
            #     level='WARNING')
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        response = requests.post(
            self.api_url,
            headers=headers,
            json={"model": "embedding-2", "input": query}
        )
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} {response.text}")
        json_response = response.json()
        return json_response['data'][0]['embedding']


# clean format to support JSON format
def clean_doc_format(text: Document) -> str:
    return (str(text).replace("\n", " ").replace("\r", " ").replace("\t", " ")
            .replace("  ", " ").replace("{","").replace("}","").replace("[","").replace("]",""))