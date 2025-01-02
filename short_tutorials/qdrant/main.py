from datasets import load_dataset
import pandas as pd
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

from langchain_community.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Qdrant

def get_dataset(name: str):
    d = load_dataset(name)
    print(f"{'='*30}")
    print(d)
    print(f"{'=' * 30}")
    return d

def check_vars() -> dict:
    # Load the API key from the environment
    keys = {
        "COHERE_API_KEY": os.getenv("COHERE_API_KEY"),
        "QDRANT_URL": os.getenv("QDRANT_URL"),
        "QDRANT_API_KEY": os.getenv("QDRANT_API_KEY"),
    }

    if not keys["COHERE_API_KEY"]:
        raise ValueError("COHERE_API_KEY environment variable is not set.")
    if not keys["QDRANT_URL"]:
        raise ValueError("QDRANT_URL environment variable is not set.")
    if not keys["QDRANT_API_KEY"]:
        raise ValueError("QDRANT_API_KEY environment variable is not set.")

    return keys


def print_q(txt: str):
    print(f"{'='*30}")
    print(txt)
    print(f"{'=' * 30}")

if __name__ == "__main__":
    import os

    # Load the environment variables
    keys = check_vars()

    dataset = get_dataset("mugithi/ubuntu_question_answer")

    train_df = pd.DataFrame(dataset["train"])
    print(train_df.head(n=10))

    text_pattern = """
    Example question: {question}
    Example answer: {answer}
    """

    texts, metadatas = [], []
    for entry in train_df.itertuples():
        text = text_pattern.format(question=entry.question, answer=entry.answer)

        texts.append(text.strip())
        metadatas.append({"question": entry.question, "answer": entry.answer})

    embeddings = CohereEmbeddings(model="embed-multilingual-v3.0")

    facts_store = Qdrant.from_texts(
        texts, embeddings, metadatas,
        location=keys["QDRANT_URL"],
        api_key=keys["QDRANT_API_KEY"],
        collection_name="facts",
        force_recreate=True,
    )


    q = facts_store.similarity_search("How do I format the disk?")
    print_q(q)

    # All examples come from the original paper on step-back prompting
    # Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models
    # See: https://arxiv.org/abs/2310.06117

    examples = [
        {
            "input": "Estella Leopold went to which school between Aug 1954 and Nov 1954?",
            "output": "What was Estella Leopold's history?",
        },
        {
            "input": "Could the members of The Police perform lawful arrests?",
            "output": "What can the members of The Police do?",
        },
        {
            "input": "At year saw the creation of the region where the county of Hertfordshire is located?",
            "output": "which region is the county of Hertfordshire located?"
        },
    ]


    single_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{output}"),
        ]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=single_prompt,
        examples=examples,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are simplifying the user questions, so they are more general and easier to answer. Use the following examples:"),
        few_shot_prompt,
        ("user", "{input}"),
    ])

    chat_model = ChatOpenAI(temperature=0)
    question_generator = prompt | chat_model | StrOutputParser()
    question_generator.invoke({"input": "How do I format the disk?"})


    facts_retriever = facts_store.as_retriever()

    rag_prompt = ChatPromptTemplate.from_template("""
    Answer the question based only on the provided context and step-back context. Do not make up the answer if it's not given, but answer "I don't know".
    Context, step-back context and question are enclosed with HTML-like tags.

    <context>
    {context}
    </context>

    <step-back-context>
    {step_back_context}
    </step-back-context>

    <question>{input}</question>
    """)

    extract_input = RunnableLambda(lambda x: x["input"])
    step_back_rag = (
            {
                "context": extract_input | facts_retriever,
                "step_back_context": question_generator | facts_retriever,
                "input": extract_input
            }
            | rag_prompt
            | chat_model
            | StrOutputParser()
    )

    q = step_back_rag.invoke({"input": "What is wayland used for?"})
    print_q(q)
