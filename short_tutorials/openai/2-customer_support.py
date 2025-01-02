import os
import time
from openai import OpenAI

COMPANY_NAME = "Alphawise"

# Initialize the OpenAI client
client = OpenAI()
OpenAI.api_key = os.getenv('OPENAI_API_KEY')

# Step 1: Upload a File with an "assistants" purpose
my_file = client.files.create(
    file=open("2-client.txt", "rb"),
    purpose='assistants'
)
print(f"File uploaded: {my_file} \n")
print(f"File Status: {my_file.status}")

# Step 2: Create an Assistant
my_assistant = client.beta.assistants.create(
    model="gpt-4o",
    instructions=(
        "You are a helpful customer support chatbot for Alphawise. "
        "Answer customer questions based on your knowledge base from the information included in 2-client.txt. "
        "Be helpful, polite, and detailed."
    ),
    name="Customer Support Chatbot",
    tools=[{"type": "file_search"}]
)
print(f"Assistant created: {my_assistant} \n")
print(f"Assistant Configuration: {my_assistant}")

# Step 3: Create a Thread
my_thread = client.beta.threads.create()
print(f"Thread created: {my_thread} \n")

# Step 4: Continuous Chat Loop
def chat_with_user():
    print(f"{'='*30}\n")
    print(f" -- Type 'exit' or 'quit' to end the chat -- \n")

    user_name = input(f"Assistant: Welcome to {COMPANY_NAME}! What's your name?  : ")
    print("Assistant: How can I help you today?")
    
    while True:
        user_message = input(f"{user_name}: ")

        if user_message.lower() in ['exit', 'quit']:
            print("Assistant: Ending the chat. Goodbye!")
            break

        # Send the user's message to the assistant
        user_message_obj = client.beta.threads.messages.create(
            thread_id=my_thread.id,
            role="user",
            content=user_message
        )
        print(f"Debug - User Message Object: {user_message_obj}")

        # Run the assistant and retrieve its response
        assistant_run = client.beta.threads.runs.create(
            thread_id=my_thread.id,
            assistant_id=my_assistant.id,
            instructions=f"Please address the user as {user_name}."
        )
        print(f"Debug - Assistant Run: {assistant_run}")

        # Wait for the assistant's response
        while assistant_run.status in ["queued", "in_progress"]:
            time.sleep(1)  # Avoid rapid polling
            assistant_run = client.beta.threads.runs.retrieve(
                thread_id=my_thread.id,
                run_id=assistant_run.id
            )
            print(f"Assistant Run Status: {assistant_run.status}")

        if assistant_run.status == "completed":
            all_messages = client.beta.threads.messages.list(thread_id=my_thread.id)
            print(f"Debug - All Messages: {all_messages}")

            try:
                # Find the latest assistant message
                assistant_message = None
                for message in all_messages.data:
                    if message.role == "assistant":
                        assistant_message = message.content[0].text.value
                        break

                if assistant_message:
                    print(f"Assistant: {assistant_message}")
                else:
                    print("Assistant: Sorry, I had trouble responding.")
            except (IndexError, AttributeError):
                print("Assistant: Sorry, I had trouble responding.")
        else:
            print("Assistant: There was a problem with your request. Please try again.")


chat_with_user()
