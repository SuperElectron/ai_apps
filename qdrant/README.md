# Getting Started

Step-back prompting for RAG, implemented in Langchain.
Makes use of OpenAI, Qdrant, Cohere, and Langchain.

__important notes__

- you can reference the docs, where this code is copied from: https://github.com/vineetp6/qdrant-examples
- you need to set up an API KEY for cohere and Qdrant. 
  - Cohere: https://dashboard.cohere.com/api-keys
  - Qdrant: https://cloud.qdrant.io

__NOTES__

The QDRANT_URL variable is found in your (1) URL or (2) dashboard _Overview_
 
---


# Run

- install dependencies

```bash
# set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
# install deps
pip3 install -r requirements.txt
```

- run it

```bash
export export QDRANT_URL="your-url"
export QDRANT_API_KEY="your-api-key"
export COHERE_API_KEY="your-api-key"
python3 main.py
```

- alternatively, you can run the jupyter notebook to explore it.


