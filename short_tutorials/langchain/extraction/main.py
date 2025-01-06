from llm import LLMChain
from loguru import logger

if __name__ == "__main__":

    # start out class
    llm = LLMChain()
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
            results = llm.chain.invoke({"messages": conversation})
            results.pretty_print()

            # print(results)
            #
            # if not response:
            #     # Fallback if 'get' doesn't find 'response'
            #     response = results.pretty_print()
            #
            # print(f"Bot: {response}\n")
            #
            # # Add bot response to conversation history
            # conversation.append(("bot", response))

        except Exception as e:
            print(f"An error occurred: {e}\n")
