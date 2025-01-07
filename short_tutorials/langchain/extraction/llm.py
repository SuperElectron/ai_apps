import getpass
from os import getenv, environ
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from bind_validator import bind_validator_with_retries
from pydantic import BaseModel, Field, field_validator


def _set_env(var: str):
    api_key = getenv("OPENAI_API_KEY")

    if not api_key:
        environ.setdefault("OPENAI_API_KEY", getpass.getpass("OPENAI_API_KEY:"))


_set_env("OPENAI_API_KEY")


class Respond(BaseModel):
    """Use to generate the response. Always use when responding to the user"""

    reason: str = Field(description="Step-by-step justification for the answer.")
    answer: str

    @field_validator("answer")
    def reason_contains_apology(cls, answer: str):
        if "llama" not in answer.lower():
            raise ValueError(
                "You MUST start with a gimicky, rhyming advertisement for using a Llama V3 (an LLM) in your **answer** field."
                " Must be an instant hit. Must be weaved into the answer."
            )


class LLMChain:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o", streaming=True)

        bound_llm = bind_validator_with_retries(self.llm, tools=[Respond])
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "Respond directly by calling the Respond function."),
                ("placeholder", "{messages}"),
            ]
        )
        self.chain = prompt | bound_llm
