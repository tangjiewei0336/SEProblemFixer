from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from glm import ChatGLM
from .embedding import GLMEmbeddings
from .content_provider import RAGContentProvider


class RAGSystem:
    @classmethod
    def from_content_provider(cls, content_provider, template, embedding_model=GLMEmbeddings, llm=ChatGLM(), top_k=5):
        """

        :param content_provider:
        :param template: 如果只需要生成缓存，可以把本项设置为None。
        :param embedding_model:
        :param llm:
        :param top_k:
        :return:
        """
        index = FAISS.from_documents(content_provider.get_documents(), embedding_model())
        return cls(content_provider, embedding_model(), index, llm, template, top_k)

    def update_template(self, template):
        self.prompt = ChatPromptTemplate(template)
        self.rag_chain = (
            self.prompt |
            self.llm |
            StrOutputParser()
        )

    def __init__(self, content_provider, embedding_model, index, llm, prompt: str, k, index_fake = None):
        if prompt is not None:
            self.llm = llm
            self.prompt_str = prompt
            self.prompt = ChatPromptTemplate.from_template(prompt)
            self.k = k
            self.rag_chain = (
                    self.prompt
                    | self.llm
                    | StrOutputParser()
            )
            self.content_provider = content_provider
            self.embedding_model = embedding_model
        self.index: FAISS = index
        self.index_fake: FAISS = index_fake

    def get_assembled_prompt(self, query, history, enable_fake_detect=False):
        prompt = self.prompt_str
        prompt = prompt.replace("{question}", query)

        conversation_history = []
        if history is None:
            history = []
        for message in history:
            if message["role"] == "user":
                conversation_history.append(f"Human: {message['content']}")
            elif message["role"] == "assistant":
                conversation_history.append(f"AI: {message['content']}")

        prompt = prompt.replace("{history}", "\n".join(conversation_history))

        retrieved_context = self.index.as_retriever(search_kwargs={"k": self.k}).get_relevant_documents(
            query + "\n".join(conversation_history))

        prompt = prompt.replace("{context}", str(retrieved_context))

        if enable_fake_detect:
            fake_str = self.index_fake.as_retriever(search_kwargs={"k": 1}).get_relevant_documents(query)

            prompt = prompt.replace("{fake}", str(fake_str))

        return prompt


    def query(self, query, history: List[dict] = None, enable_fake_detect = False):
        conversation_history = []
        if history is None:
            history = []
        for message in history:
            if message["role"] == "user":
                conversation_history.append(f"Human: {message['content']}")
            elif message["role"] == "assistant":
                conversation_history.append(f"AI: {message['content']}")

        retrieved_context = self.index.as_retriever(search_kwargs={"k": self.k}).get_relevant_documents(
            query + "\n".join(conversation_history))
        
        if enable_fake_detect:
            fake_str = self.index_fake.as_retriever(search_kwargs={"k": 1}).get_relevant_documents(query)
            return self.rag_chain.invoke(
                {"context": retrieved_context, "question": query, "history": conversation_history,
                 "fake": fake_str})
        else:
            return self.rag_chain.invoke(
            {"context": retrieved_context, "question": query, "history": conversation_history})

    def save_index(self, path):
        bytes = self.index.serialize_to_bytes()
        with open(path, "wb") as f:
            f.write(bytes)

    @classmethod
    def load_index(cls, path, prompt, embedding_model=GLMEmbeddings(), path_fake : str = None):
        with open(path, "rb") as f:
            bytes = f.read()
        index = FAISS.deserialize_from_bytes(bytes, embedding_model, allow_dangerous_deserialization=True)
        if path_fake is not None:
            with open(path_fake, "rb") as f:
                bytes = f.read()
            index_fake = FAISS.deserialize_from_bytes(bytes, embedding_model, allow_dangerous_deserialization=True)
            return cls(None, embedding_model, index, ChatGLM(model_type=ModelType.GLM_4), prompt, 10, index_fake)

        return cls(None, embedding_model, index, ChatGLM(), prompt, 10, None)
