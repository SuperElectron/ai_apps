# Getting Started

- you will need an account with chatGPT, and an API key
- set up virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```


# Files

| File Name                                     | Description                                                         |
|-----------------------------------------------|---------------------------------------------------------------------|
| return_json.py                                | Shows how to structure the LLM output                               |
| customer_support  .py                         | Create a simple chatbot with openAI rag (files)                     |
| gpt_vision.py                                 | Using promting and images to detect and classify people with smiles |
| gpt_audio.py                                  | Real-time voice chat with GPT                                       |

__requirements for gpt_audio.py__

```bash
# mac
brew install portaudio
# linux
sudo apt-get install -y portaudio19-dev
```

# Run

- before running each file, you will need to export the OPENAI_API_KEY variable in your terminal.

```bash
export OPENAI_API_KEY="your-key"
python3 a_file.py

```
