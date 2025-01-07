import getpass
from os import getenv, environ
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pipeline.retry import bind as bind_with_retry
from pipeline.patched import bind as bind_with_patch_retry


def _set_env(var: str):
    api_key = getenv("OPENAI_API_KEY")
    if not api_key:
        environ.setdefault("OPENAI_API_KEY", getpass.getpass("OPENAI_API_KEY:"))

_set_env("OPENAI_API_KEY")

class LLMChainSimple:
    def __init__(self, prompt: ChatPromptTemplate, tools: list):
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o", streaming=True)
        bound_llm = bind_with_retry(self.llm, tools=tools)
        self.chain = prompt | bound_llm


class LLMChainPatched:
    def __init__(self, prompt: ChatPromptTemplate, tools: list):
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o", streaming=True)
        bound_llm = bind_with_patch_retry(self.llm, tools=tools)
        self.chain = prompt | bound_llm
