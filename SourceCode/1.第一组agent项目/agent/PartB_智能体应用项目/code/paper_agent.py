import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ================= 1. 配置参数与环境 =================
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key")  # 务必替换

PROJECT_ROOT = r"D:\demo_torch\agent"
DATA_DIR = os.path.join(PROJECT_ROOT, "PartA_知识资产与评测基准", "data")
FAISS_INDEX_PATH = os.path.join(PROJECT_ROOT, "PartB_智能体应用项目", "code", "faiss_index")

# ================= 2. 加载与处理知识库 =================
print("🧠 正在初始化医学图像与多组学数据分析 Agent...")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

if os.path.exists(FAISS_INDEX_PATH):
    print("📂 发现已存在的知识向量库，直接加载...")
    vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
else:
    print("🔍 正在读取 Part A 知识资产，构建检索向量库 (这可能需要十几秒)...")
    docs = []
    txt_files = glob.glob(os.path.join(DATA_DIR, "**", "main.txt"), recursive=True)

    for file_path in txt_files:
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            docs.extend(loader.load())
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(docs)

    vector_store = FAISS.from_documents(split_docs, embeddings)
    vector_store.save_local(FAISS_INDEX_PATH)
    print("✅ 知识库构建完成！")

# ================= 3. 组装 RAG 问答链 (最新 LCEL 纯净写法) =================
llm = ChatOpenAI(
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    max_tokens=1024,
    temperature=0.1
)

template = """
你是一个专注于智慧医疗、医学图像与基因组数据分析领域的 AI 专家。
请严格基于以下检索到的【知识库内容】来回答用户的问题。
如果你在已知内容中找不到答案，请直接回答“根据当前知识库无法得出结论”，不要凭空捏造。

【知识库内容】：
{context}

用户问题：{question}
请给出逻辑清晰、连贯且专业的中文回答：
"""
prompt = ChatPromptTemplate.from_template(template)

# 将向量库转为检索器
retriever = vector_store.as_retriever(search_kwargs={"k": 3})


# 定义格式化文档的辅助函数
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# 核心：一条极其优雅的 LCEL 数据流链条 (完全摆脱老版 chains 模块)
rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

# ================= 4. 开启交互式对话终端 =================
print("\n" + "=" * 50)
print("🚀 医学多模态文献 Agent 已启动！(输入 'exit' 或 'quit' 退出)")
print("=" * 50 + "\n")

while True:
    user_query = input("💡 请提问：")
    if user_query.lower() in ['exit', 'quit']:
        print("感谢使用，再见！")
        break
    if not user_query.strip():
        continue

    print("🤖 Agent 正在检索知识库并思考...")

    # 执行生成
    response = rag_chain.invoke(user_query)
    # 单独拿取引用源（LCEL 链式调用的清晰之处）
    source_docs = retriever.invoke(user_query)

    print("\n" + "-" * 40)
    print(f"📝 【回答】:\n{response}")

    print("\n📚 【参考来源】:")
    for i, doc in enumerate(source_docs):
        # 提取来源文件的路径名作为展示
        source_name = doc.metadata.get('source', 'Unknown').split(os.sep)[-3:]
        print(f"  [{i + 1}] {'/'.join(source_name)}")
    print("-" * 40 + "\n")
