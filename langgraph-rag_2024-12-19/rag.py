import getpass, os
from typing import Annotated, Sequence, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.graph.message import add_messages
from langchain import hub


# Document retrieval setup
def setup_retriever():
    urls = [
        "https://lilianweng.github.io/posts/2023-06-23-agent/",
        "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
        "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
    ]
    docs = [item for url in urls for item in WebBaseLoader(url).load()]

    doc_splits = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-3.5-turbo",
        chunk_size=100,
        chunk_overlap=50
    ).split_documents(docs)

    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=OpenAIEmbeddings()
    )

    return create_retriever_tool(
        vectorstore.as_retriever(),
        "retrieve_blog_posts",
        "Search and return information about Lilian Weng blog posts on LLM agents, prompt engineering, and adversarial attacks."
    )


# Agent State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Data model for grade_document, the decision function
class Grade(BaseModel):
    """Binary score for relevance check."""
    binary_score: str = Field(description="Relevance score 'yes' or 'no'")


# Decision functions
def grade_documents(state: AgentState) -> Literal["generate", "rewrite"]:
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (messages): The current state

    Returns:
        str: A decision for whether the documents are relevant or not
    """

    # LLM with tool and validation
    model = ChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True)
    llm_with_tool = model.with_structured_output(Grade)

    # Prompt
    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
        Here is the retrieved document: \n\n {context} \n\n
        Here is the user question: {question} \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.""",
        input_variables=["context", "question"],
    )

    # create invokable chain
    chain = prompt | llm_with_tool

    # Invoke the chain with inputs (question = first_message, doc or context = last_message) to get results
    scored_result = chain.invoke({"question": state["messages"][0].content, "context": state["messages"][-1].content})
    score = scored_result.binary_score

    if score == "yes":
        return "generate"
    else:
        return "rewrite"


def agent(state: AgentState, tools):
    return {"messages": [ChatOpenAI(temperature=0, model="gpt-4-turbo").bind_tools(tools).invoke(state["messages"])]}


def rewrite(state: AgentState):
    model = ChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True)
    msg = [HumanMessage(content=f"Rephrase this question: {state['messages'][0].content}")]
    return {"messages": [model.invoke(msg)]}


def generate(state: AgentState):
    prompt = hub.pull("rlm/rag-prompt")
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, streaming=True)
    response = (prompt | llm | StrOutputParser()).invoke(
        {"context": state["messages"][-1].content, "question": state["messages"][0].content}
    )
    return {"messages": [response]}


# Main entry point
if __name__ == "__main__":
    os.environ.setdefault("OPENAI_API_KEY", getpass.getpass("OPENAI_API_KEY:"))
    retriever_tool = setup_retriever()
    tools = [retriever_tool]

    # Allow the user to set the question dynamically
    # Default question is: What is prompt engineering?
    question = input("Enter your question: ").strip()

    # Example usage of the system
    state = AgentState(messages=[HumanMessage(content=question)])

    action = grade_documents(state)
    if action == "generate":
        state = generate(state)
    elif action == "rewrite":
        state = rewrite(state)
    else:
        state = agent(state, tools)

    # Output the resulting state
    print(state)

