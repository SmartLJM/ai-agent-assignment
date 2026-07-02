DL and LS Final Assignment Project Proposal
I. Basic Project Information
Project Title: Medical-RAG-Agent: A Multimodal Knowledge Retrieval Agent Based on Large-Model Medical Imaging and Genomics
Team Leader: Feiyu He
Team Members: Jiawei Ding
Research Direction: Smart Healthcare, Medical Imaging, and Genomic Data Analysis
Weight Allocation: Direction A (Knowledge Assets and Evaluation) 50%, Direction B (Agent Applications) 50%

II. Project Background and Motivation
In current smart healthcare research, the fusion analysis of medical images (such as ultrasound, MRI, CT) and genomic data (such as single-cell sequencing, multi-omics features) has become a core driving force for precision medicine. However, the cutting-edge literature on data mining in this field is vast and the textbooks are complex. Researchers often face problems such as low knowledge retrieval efficiency and difficulty in cross-modal concept fusion when performing feature extraction, dimensionality reduction visualization, and classification model construction.

This project aims to explore the cross-application value of AI Agent technology and data mining in the field of medical multimodality. By constructing a vertical domain-specific RAG (Retrieval Augmentation Generative) agent, this system vectorizes and reorganizes obscure medical deep learning textbooks, academic papers, and course notes, providing researchers with a high-precision automated literature reading and knowledge question answering expert system.

III. Core Objectives and Application Value

**Constructing a High-Quality Domain Knowledge Base:** Deeply mine at least 20 effective medical images and multi-omics authoritative knowledge sets (including academic papers, textbook PDFs, MIT course notes, etc.), completing keyword extraction and data cleaning.

**Bridging Cross-Modal Semantic Barriers:** Utilize the agent to bridge the semantic gap between "data mining algorithms" and "medical application scenarios," such as automatically explaining "the role of t-SNE/UMAP in genomic clustering" or "feature fusion strategies of attention mechanisms in medical image segmentation."

**Achieving an Efficient Automated Question Answering Pipeline:** Develop an end-to-end retrieval and inference pipeline capable of accurately locating knowledge sources, rejecting the illusion of large models, and ensuring the rigor of academic question answering.


**Achieving an Efficient Automated Question Answering Pipeline:** Develop an end-to-end retrieval and inference pipeline capable of accurately locating knowledge sources, rejecting the illusion of large models, and ensuring the rigor of academic question answering. IV. Technical Architecture and Implementation Scheme

This project plans to utilize cutting-edge large-scale model ecosystem tools. The specific technology stack and core module design are as follows:

Core Framework: Adopting the LangChain framework and fully upgrading to the latest LCEL (LangChain Expression Language) declarative pipeline architecture to improve the robustness of data flow.

Large Language Model (LLM): Integrating the Qwen-Plus model from Alibaba Cloud's Bailian platform, setting an extremely low Temperature (0.1) to ensure the logic and rigor of academic answers.

Data Processing and Vectorization:

Document Parsing: Integrating PyPDFLoader and TextLoader to achieve parallel parsing of complex medical textbooks and plain text data.

Advanced Retrieval Strategy (Data Mining): Using the FAISS local lightweight vector database for fast similarity calculation.

Abandoning traditional Top-K retrieval, innovatively introducing the MMR (Maximal Marginal Relevance) algorithm. Building upon an expanded recall pool (fetch_k=30), a diverse selection of text blocks (k=8) is employed to effectively address the local optimum retrieval problem for long-tail knowledge, enhancing the Agent's comprehensive perspective in complex academic queries.

V. Expected Deliverables

Complete Dataset and Benchmarks: Includes a compliant knowledge asset folder (containing content, keywords.json, and source.json) and at least 20 professional benchmark questions in JSON format.

A Runnable Agent System: A robust local CLI interactive terminal capable of smoothly answering questions related to medical image and genomics data mining, and displaying cited literature sources in real time.

Technical Documentation and Demonstrations: Includes a detailed final report on the architecture design and screenshots/screen recordings demonstrating successful system operation.