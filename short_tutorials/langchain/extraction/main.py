from llm import LLMChainSimple, LLMChainPatched
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger


""""
Here we show how validators + retry logic can ensure validity of generated tool calls.

In the BIND of each setup (LLMChainSimple, LLMChainPatched) there are 3 main parts:
     - tools - describes utility of the model.
     - a retry strategy - to know how to deal with invalid results
     - a validator node - to check out results.

In run_1, we use a simple tool to respond to user input (adds style).
In run_2, we introduce tools to extract parts (view extractor.py) of a transcript.
In run_3, we introduce the JSONPatch to fix the error response in from the nested conversation.

View more in llm.py for how each chain is setup with functions from retry.py and patched.py in the pipeline folder.

"""


def run_1():
    """
    This will run and correct itself. (but struggles on reasoning)
    """
    from pipeline.retry import Respond

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Respond directly by calling the Respond function."),
        ("placeholder", "{messages}"),
    ])

    llm_chain = LLMChainSimple(prompt=prompt, tools=[Respond])
    # invoke a question
    # Initialize conversation history
    conversation = []

    logger.info("Welcome to the real-time chat! Type 'exit' to end the conversation.\n")
    user_name = input("Hey, before we get started let's get your name: ")
    while True:
        # Prompt user for input
        logger.debug(f"User input {'=' * 10} ASK YOUR QUESTION\n")
        user_input = input(f"{user_name}: ")

        # Check for exit condition
        if user_input.strip().lower() == 'exit':
            logger.info("Chat ended. Goodbye!")
            break

        # Add user message to conversation history
        conversation.append(("user", user_input))

        try:
            # Invoke the LLMChain with the current conversation
            results = llm_chain.chain.invoke({"messages": conversation})
            results.pretty_print()

        except Exception as e:
            print(f"An error occurred: {e}\n")


def run_2():
    """
    Here we introduce tools to extracts parts (view TranscriptSummary) of a transcript

    There are 3 main parts:
     - tools - now we look at extracting parts, or components, or the transcript (view extractor.py)
     - a retry strategy - to know how to deal with invalid results
     - a validator node - to check out results.

    We expect this to struggle due to the nested nature of the conversation.
    Depending on the model, it may fail (like older gpt-3 turbo models) and gpt-4o will struggle to be correct itself.
    """
    from extractor import TranscriptSummary
    from utils.transcript import formatted

    # start out class
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Respond directly using the TranscriptSummary function."),
        ("placeholder", "{messages}"),
    ])
    llm_chain = LLMChainSimple(prompt=prompt, tools=[TranscriptSummary])

    try:
        results = llm_chain.chain.invoke({
            "messages": [(
                "user",
                f"Extract the summary from the following conversation:\n\n<convo>\n{formatted}\n</convo>"
                "\n\nRemember to respond using the TranscriptSummary function.",
            )]
        })
        results.pretty_print()
    except ValueError as e:
        print(repr(e))


def run_3():
    """
    Here we introduce the JSONPatch to fix the error response in from the nested conversation (pipeline/patched.py)

    This dynamically patches answers while it uses the TranscriptSummary tool to correct itself.

    """
    from extractor import TranscriptSummary
    from utils.transcript import formatted
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Respond directly using the TranscriptSummary function."),
        ("placeholder", "{messages}"),
    ])
    llm_chain = LLMChainPatched(prompt=prompt, tools=[TranscriptSummary])

    results = llm_chain.chain.invoke({
        "messages": [(
            "user",
            f"Extract the summary from the following conversation:\n\n<convo>\n{formatted}\n</convo>",
        )]
    })
    results.pretty_print()


if __name__ == "__main__":
    logger.info("Running DEMO1")
    run_1()
    logger.info("Running DEMO2")
    run_2()
    logger.info("Running DEMO3")
    run_3()
