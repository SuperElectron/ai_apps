from pprint import pprint as pp
import os
from getpass import getpass
import aisuite as ai


def pprint(data, width=80):
    """Pretty print data with a specified width."""
    pp(data, width=width)


def ask(message, sys_message="You are a helpful agent.", model="groq:llama-3.2-3b-preview"):
    # Initialize the AI client for accessing the language model
    client = ai.Client()

    # Construct the messages list for the chat
    messages = [
        {"role": "system", "content": sys_message},
        {"role": "user", "content": message}
    ]

    # Send the messages to the model and get the response
    response = client.chat.completions.create(model=model, messages=messages)

    # Return the content of the model's response
    return response.choices[0].message.content


if __name__ == "__main__":
    os.environ['GROQ_API_KEY'] = getpass('Enter your GROQ API key: ')
    os.environ['OPENAI_API_KEY'] = getpass('Enter your OPENAI API key: ')

    # PART 1: Confirm each model is using a different provider

    print(ask("Who is your creator?", model="groq:llama-3.2-3b-preview"))
    print(ask('Who is your creator?', model='openai:gpt-4o'))

    # Part 2: Querying Multiple AI Models for a Common Question (Using Grok)
    models = [
        'llama-3.1-8b-instant',
        'llama-3.2-1b-preview',
        'llama-3.2-3b-preview',
        'llama3-70b-8192',
        'llama3-8b-8192'
    ]

    # Loop through each model and get a response for the specified question
    ret = []
    for x in models:
        ret.append(ask('Write a short one sentence explanation of the origins of AI?', model=f'groq:{x}'))
    # Print the model's name and its corresponding response
    for idx, x in enumerate(ret):
        pprint(models[idx] + ': \n ' + x + ' ')

    # PART 3: Querying Different AI Providers for a Common Question
    providers = [
        'groq:llama3-70b-8192',
        'openai:gpt-4o',
    ]

    # Loop through each provider and get a response for the specified question
    ret = []
    for x in providers:
        ret.append(ask('Write a short one sentence explanation of the origins of AI?', model=x))
    # Print the provider's name and its corresponding response
    for idx, x in enumerate(ret):
        pprint(providers[idx] + ': \n' + x + ' \n\n')
