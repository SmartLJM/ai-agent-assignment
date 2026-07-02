Final Report for Dl and LS

I. Project Overview
Project Title: Medical-RAG-Agent Based on Large Model
Project Objectives: This project focuses on the interdisciplinary field of "smart healthcare, medical image, and genomic data analysis,"

utilizing data mining techniques (text feature vectorization, high-dimensional spatial similarity retrieval) and large language models (LLM) to construct a RAG (Retrieval Enhanced Generation) agent. It aims to address the pain points faced by researchers in this field when dealing with massive amounts of multimodal literature and complex textbooks, including low information retrieval efficiency and difficulties in cross-modal concept fusion.

Research Direction Integration: The knowledge base (Part A) comprehensively covers vertical fields such as deep learning for medical images and multi-omics analysis; the agent (Part B) serves as an efficient domain knowledge question-answering system, successfully achieving end-to-end automated processing from massive amounts of unstructured text to precise structured insights.

II. System Design and Technical Architecture

This project abandons traditional keyword matching retrieval and adopts the cutting-edge LangChain Expression Language (LCEL) architecture to construct a streaming, declarative RAG question-answering chain. The system mainly consists of four modules:

Multi-source data parsing module: For the complex knowledge set collected in Part A, it integrates PyPDFLoader and TextLoader to achieve dual-track parallel parsing and text chunking of .pdf (professional textbooks, MIT courseware) and .txt (academic papers).

Feature vectorization module (Embedding): This is the core of data mining. It maps massive discrete text into a high-dimensional dense vector space, significantly improving the feature representation capability of medical terminology.

Vector database and retrieval engine (FAISS + MMR): It utilizes the lightweight FAISS library for local high-dimensional vector storage. In terms of retrieval strategy, it abandons the basic Top-K nearest neighbor search and adopts a data mining algorithm based on maximum marginal relevance (MMR).

Large Model Generation and Inference Module (LLM): Integrates with the Qwen-Plus model from Alibaba Cloud's Bailian platform, and uses carefully tuned professional prompts to generate logically coherent academic answers by using retrieved high-dimensional text fragments as context.

III. Key Implementation Details and Technical Breakthroughs

During project development, we overcame several data mining and engineering implementation challenges:

3.1 Introducing the MMR Algorithm to Solve the "Information Cocoon" Problem

In early tests, a retrieval strategy with k=3 often caused the large model to get stuck in local optima (e.g., three retrieved text fragments all came from the same chapter of the same document), resulting in an extremely narrow answer scope.

Solution: Introducing the MMR (Maximal Marginal Relevance) diversity retrieval algorithm.

Setting fetch_k=30 for coarse screening, and then further refining k=8 to feed to the large model. This allows the agent to simultaneously cite academic papers, classic textbooks, and course notes when answering complex questions, resulting in answers with greater depth and breadth.

IV. Results Analysis and Performance Demonstration

After the aforementioned data mining optimizations, Medical-RAG-Agent demonstrated exceptional question-answering capabilities:

Before Optimization (Overly Rigid): When faced with basic questions (such as "What is multimodality?"), the Agent would rigidly reply, "Based on the current knowledge base, no conclusion can be drawn," due to the overly advanced nature of the search content and the failure to hit the basic definition.

After Optimization (Comprehensive Understanding): The Prompt was modified to broaden the scope of basic concept explanations, and the search range was expanded in conjunction with MMR. Now, when asked the same question, the Agent can not only accurately provide a general definition of "multimodality" based on its internalized large-model knowledge, but also precisely cite MIT courseware and deep learning textbooks from the knowledge base, providing specific examples such as "CT and MRI fusion analysis in medical images," demonstrating a high level of professional competence.

V. Summary and Outlook
This project successfully integrated advanced large-model Agent technology with the data mining needs of medical images and genomics, constructing a highly available, locally deployed intelligent question-answering system. Future optimization directions could include integrating more streaming data sources (such as PubMed API for real-time retrieval) or introducing a multi-agent architecture, where one agent is responsible for searching literature and another agent is responsible for extracting and summarizing, further expanding the boundaries of academic automation.

