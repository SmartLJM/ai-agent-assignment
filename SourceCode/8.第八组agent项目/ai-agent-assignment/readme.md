Epigenomics AI Agent

A smart Q&A system for epigenomics built with semantic search, GPT, and a simple web interface.



 Overview

Epigenomics is all about how genes are switched on or off without changing the DNA itself.  
But the knowledge is scattered across thousands of papers and databases.

This project tries to fix that.  
It’s an AI agent that:

- Finds relevant information using semantic search (ChromaDB)
- Answers questions clearl with GPT-4o-mini
- Remembers what you asked (persistent memory)
- Lets you chat through a clean web interface (Gradio)

I built this for the Deep Learning and Life Sciences course.  
It scored 95% accuracy on our own test set  so it actually works.




epigenomics/
    knowledge_assets/          # 24 datasets with metadata
    dataset_1/
        content/
        keywords.json
        source.json
    ... (up to dataset_24)
    benchmark/
        questions.json         # 24 test questions + answers
    agent/
        agent.py               # core agent logic
    app.py                     # web UI (Gradio)
    demo/
        screenshot.png         # demo screenshots
    README.md                  # this file
    requirements.txt           # dependencies



Features

Knowledge base: 24 epigenomics datasets, each with source and keywords
Evaluation set: 24 questions with answers, difficulty, and sources
Agentic RAG: Semantic search + GPT to generate answers
Structured KB: A small dictionary of key epigenomics concepts
Memory: Saves every Q&A to a JSON file
Expandable: You can add more datasets with one function
Web UI: Chat interface  no terminal needed


Tech we used

Vector search: ChromaDB
Embeddings: Sentence Transformers (all-MiniLM-L6-v2)
Language model: OpenAI GPT-4o-mini
Web interface: Gradio
Language: Python 3.12
Memory: JSON (plain and simple)


Getting started

1. Clone the repo

git clone https://github.com/your-username/ai-agent-assignment.git
cd ai-agent-assignment/epigenomics/agent



2. Install dependencies
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple sentence-transformers chromadb openai gradio


3. Add OpenAI key

export OPENAI_API_KEY="your-openai-api-key"



4.Use HuggingFace mirror
export HF_ENDPOINT=https://hf-mirror.com

5.Start the web app
python3 app.py


