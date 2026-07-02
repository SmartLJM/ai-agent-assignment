import os
import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader

# ================= 1. 配置路径 (直接指向你的现有文件夹) =================
# ⚠️ 记得填入你的全英文真实 API Key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

PROJECT_ROOT = r"D:\demo_torch\agent"
PART_A_DIR = os.path.join(PROJECT_ROOT, "PartA_知识资产与评测基准")

# 输入路径：直接读取你解压的原始文件夹
SOURCE_DIR = os.path.join(PART_A_DIR, "data", "03-course", "static_resources")

# 输出路径：老师严格要求的规范路径
OUTPUT_DIR = os.path.join(PART_A_DIR, "data", "03-course")
BENCHMARK_DIR = os.path.join(PART_A_DIR, "benchmark")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BENCHMARK_DIR, exist_ok=True)

# 初始化云端大脑
llm = ChatOpenAI(
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    max_tokens=2048,
    temperature=0.1
)

# ================= 2. 课程讲义专用 Prompt =================
template = """
你现在是一位麻省理工学院(MIT)的计算生物学与基因组数据科学教授。
请阅读以下课程讲义（PPT/PDF）的前几页文本，提取这节课的核心知识点。

课程内容：
{text}

请严格按照以下 JSON 格式输出，不要包含任何Markdown标记：
{{
    "content_summary": "提取这节课的核心教学内容、讲解的算法或生物学概念（如基因组序列分析、机器学习在生物学中的应用等）。",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "qa_pair": {{
        "question": "根据讲义内容，出一道适合本科生或研究生的专业考题。",
        "answer": "对该考题的详细准确回答。"
    }}
}}
"""
prompt = PromptTemplate(template=template, input_variables=["text"])
chain = prompt | llm

# ================= 3. 智能过滤与遍历 =================
# 核心逻辑：自动过滤掉静态网页、图片和压缩包，只挑 PDF 读
all_files = os.listdir(SOURCE_DIR)
pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]

print(f"📂 在庞杂的资源包中，Agent 成功锁定了 {len(pdf_files)} 份纯净的 PDF 课件！开始学习...\n")

# 这里我们只取前 4 篇课件做演示（你可以把 [:4] 删掉来处理所有课件）
for idx, filename in enumerate(pdf_files):
    file_path = os.path.join(SOURCE_DIR, filename)
    doc_id = f"course_{idx + 1:03d}"  # 自动生成合规编号 course_001
    print(f"[{idx + 1}/{len(pdf_files[:4])}] 正在研读 MIT 课件: {filename}")

    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        # 提取前3页文本
        paper_text = "".join([page.page_content for page in pages[:3]])

        response = chain.invoke({"text": paper_text})
        clean_json_str = re.sub(r'```json\n|\n```|```', '', response.content).strip()
        result_dict = json.loads(clean_json_str)

        # 创建标准化的知识集独立文件夹
        item_dir = os.path.join(OUTPUT_DIR, doc_id)
        os.makedirs(os.path.join(item_dir, "content"), exist_ok=True)

        # 1. 写入 content/main.txt
        with open(os.path.join(item_dir, "content", "main.txt"), "w", encoding="utf-8") as f:
            f.write(result_dict["content_summary"])

        # 2. 写入 source.json
        source_data = {
            "url": "[https://ocw.mit.edu/courses/6-047-computational-biology-fall-2015/](https://ocw.mit.edu/courses/6-047-computational-biology-fall-2015/)",
            "course_name": "Computational Biology",
            "filename": filename
        }
        with open(os.path.join(item_dir, "source.json"), "w", encoding="utf-8") as f:
            json.dump(source_data, f, ensure_ascii=False, indent=4)

        # 3. 写入 keywords.json
        with open(os.path.join(item_dir, "keywords.json"), "w", encoding="utf-8") as f:
            json.dump({"computational-biology": result_dict["keywords"]}, f, ensure_ascii=False, indent=4)

        # 4. 写入 benchmark 题库
        benchmark_data = {
            "id": f"Q2{idx + 1:03d}",  # 使用Q2前缀与之前的论文题库区分
            "question": result_dict["qa_pair"]["question"],
            "type": "short-answer",
            "difficulty": 5,
            "answer": {
                "type": "similar",
                "content": result_dict["qa_pair"]["answer"]
            },
            "sources": [{"knowledge_set_id": doc_id, "original_text": "MIT Lecture Notes"}],
            "theme": [{"genomic-data-science": result_dict["keywords"]}]
        }
        with open(os.path.join(BENCHMARK_DIR, f"Q2{idx + 1:03d}.json"), "w", encoding="utf-8") as f:
            json.dump(benchmark_data, f, ensure_ascii=False, indent=4)

        print(f"   ✅ 成功转化为规范的知识库资产")

    except Exception as e:
        print(f"   ❌ 处理失败: {e}")

print("\n🎉 MIT 课程资源全自动转化完毕！")
