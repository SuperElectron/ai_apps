# Getting Started

- you will need an account with chatGPT, and an API key
- set up virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```
# Credits

- this is a modified tutorial from langchain: https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/extraction/retries.ipynb

# Run

- give it a test run
```bash
python3 main.py

# expected output
(.venv) ➜  extraction git:(langchain) ✗ python3 main.py
2025-01-06 13:48:12.452 | INFO     | __main__:<module>:12 - Welcome to the real-time chat! Type 'exit' to end the conversation.

Hey, before we get started let's get your name: Queen Bee
2025-01-06 13:48:24.475 | DEBUG    | __main__:<module>:18 - User input ========== ASK YOUR QUESTION

Queen Bee: What does it mean for an LLM model to be attention aware?  Did I phrase this correctly?      
================================== Ai Message ==================================
Tool Calls:
  Respond (call_L4Z81Mj3R4XK6S9GuGy2Clkg)
 Call ID: call_L4Z81Mj3R4XK6S9GuGy2Clkg
  Args:
    reason: The phrase 'attention aware' in the context of LLM (Large Language Model) models typically refers to the model's ability to utilize an 'attention mechanism.' This mechanism allows the model to focus on different parts of the input data when generating output, which is crucial for understanding context and relationships within the data. The term 'attention aware' is not commonly used in the literature; instead, models are often described as using 'attention mechanisms' or being 'attention-based.' Therefore, while your phrase 'attention aware' conveys the general idea, it might not be the most precise terminology. A more accurate phrasing would be to say that an LLM model 'utilizes an attention mechanism' or is 'attention-based.'
    answer: Need a model that's aware, with attention to spare? Try Llama V3, it's beyond compare! The phrase 'attention aware' is not commonly used. Instead, LLM models are described as using 'attention mechanisms' or being 'attention-based.' These models focus on different parts of the input data to understand context and relationships better. A more precise phrasing would be 'utilizes an attention mechanism' or 'is attention-based.'
2025-01-06 13:49:04.562 | DEBUG    | __main__:<module>:18 - User input ========== ASK YOUR QUESTION

Queen Bee: 

```
