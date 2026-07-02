import os
import glob
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader, PyPDFLoader
# ================= 1. 配置参数与环境 =================
# 填入你的阿里云百炼 API Key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

# 🔥 核心修正：全部采用最安全的“相对路径”，彻底绕过 Windows 底层盘符权限和反斜杠的 Bug
# 只要你在 code 目录下运行脚本，它就会直接在当前目录读写
FAISS_INDEX_DIR = "faiss_index"
DATA_DIR = r"..\..\PartA_知识资产与评测基准\data"

# 强制保障当前目录下必定有这个文件夹，供底层 C++ 写入
os.makedirs(FAISS_INDEX_DIR, exist_ok=True)

# ================= 2. 加载与处理知识库 =================
print("nitializing medical image and genome data analysis agent...")

# 初始化嵌入模型
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 检查当前目录下是否已经成功生成了 index.faiss 文件
if os.path.exists(os.path.join(FAISS_INDEX_DIR, "index.faiss")):
    print("An existing knowledge vector library was discovered and loaded directly...")
    vector_store = FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
else:
    print("Reading Part A knowledge assets and building a retrieval vector library (this may take several seconds)....")
    docs = []
    # 读取数据
    txt_files = glob.glob(os.path.join(DATA_DIR, "**", "*.txt"), recursive=True)
    pdf_files = glob.glob(os.path.join(DATA_DIR, "**", "*.pdf"), recursive=True)
    all_files = txt_files + pdf_files

    print(f"共找到 {len(txt_files)} 个 TXT 文件 和 {len(pdf_files)} 个 PDF 文件，准备解析...")

    for file_path in all_files:
        try:
            # 根据文件后缀，自动分发给不同的解析器
            if file_path.lower().endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
            elif file_path.lower().endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            else:
                continue

            docs.extend(loader.load())
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")

    # 切分文本
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(docs)

    # 构建并保存向量库 (使用相对路径直接写入)
    vector_store = FAISS.from_documents(split_docs, embeddings)
    vector_store.save_local(FAISS_INDEX_DIR)
    print("The knowledge base has been built successfully! The vector index has been successfully persisted to disk!")

# ================= 3. 组装 RAG 问答链 (纯净 LCEL 架构) =================
# 配置大模型
llm = ChatOpenAI(
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    max_tokens=1024,
    temperature=0.1
)

# 定制专业提示词
template = """
You are an AI expert specializing in smart healthcare, medical imaging, and genomic data analysis.

Please answer the user's question strictly based on the following retrieved knowledge base content.

If you cannot find the answer in the known content, you can translate the user's Chinese question into English and search again in the knowledge base content, as knowledge base materials are often in English. Alternatively, you can find explanations related to the user's question in the knowledge base content.

If you still cannot find the answer in the known content, please directly answer "Based on the current knowledge base, no conclusion can be drawn," and do not fabricate answers.

Knowledge Base Content:
{context}

User Question: {question} Please provide a clear, coherent, and professional English answer. Avoid bullet points and strange symbols; a concise answer is sufficient.
"""
prompt = ChatPromptTemplate.from_template(template)

# 将向量库转为检索器，每次找最相关的3段文本
retriever = vector_store.as_retriever(
    search_type="mmr",  # 开启多样性检索，避免找出来的文本全是重复的废话
    search_kwargs={
        "k": 8,          # 最终喂给大模型的文本块数量（从 3 扩大到 8，提供更多上下文）
        "fetch_k": 30    # 底层先粗筛出 30 个相关片段，再从中精挑细选 8 个最不重复的
    }
)


# 格式化检索到的文档
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# 构建处理流
rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

print("\n" + "=" * 50)
print("Agent has beenn started！(input 'exit' or 'quit' to quit)")
print("=" * 50 + "\n")

# while True:
#     user_query = input("plz ask a question：")
#     if user_query.lower() in ['exit', 'quit']:
#         print("Thank you for using this service, goodbye!")
#         break
#     if not user_query.strip():
#         continue
#
#     print("Agent is Searching the knowledge base and thinking...")
#
#     # 生成回答
#     response = rag_chain.invoke(user_query)
#     # 获取引用的源文档
#     source_docs = retriever.invoke(user_query)
#
#     print("\n" + "-" * 40)
#     print(f"【answer】:\n{response}")
#
#     print("\n【Reference】:")
#     for i, doc in enumerate(source_docs):
#         # 安全获取来源路径并展示
#         source_name = doc.metadata.get('source', 'Unknown').split(os.sep)[-3:]
#         print(f"  [{i + 1}] {'/'.join(source_name)}")
#     print("-" * 40 + "\n")
