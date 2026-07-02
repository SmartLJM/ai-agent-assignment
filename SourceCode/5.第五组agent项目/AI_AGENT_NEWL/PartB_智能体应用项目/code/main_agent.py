from __future__ import annotations

from expert_qa_agent import MedicalExpertAgent
from medical_agent import MedicalDataMinerAgent
from multimodal_kb import MultiModalKnowledgeBase
from path_config import DEFAULT_NPC_DATASET_DIR, KNOWLEDGE_BASE_DIR


class RouterAgent:
    ACTION_TERMS = ("处理", "预处理", "清洗", "nifti", "数据集", "重采样", "生成数组")
    MULTIMODAL_TERMS = (
        "多模态",
        "病例",
        "影像",
        "图像",
        "切片",
        "mask",
        "掩膜",
        "统计表",
        "统计",
        "体素",
        "前景",
        "bbox",
        "overlay",
    )

    def __init__(self):
        self.medical_worker = MedicalDataMinerAgent()
        self.qa_expert = MedicalExpertAgent(KNOWLEDGE_BASE_DIR)
        self.multimodal_kb = MultiModalKnowledgeBase(dataset_dir=DEFAULT_NPC_DATASET_DIR)

    def classify_intent(self, user_input: str) -> str:
        text = user_input.lower()
        if any(term in text for term in self.ACTION_TERMS):
            return "ACTION"
        if any(term in text for term in self.MULTIMODAL_TERMS):
            return "MULTIMODAL_QA"
        return "QA"

    def _multimodal_answer(self, user_input: str) -> str:
        labels = {"text": "文献证据", "image": "病例影像信息", "table": "结构化 mask 统计表"}
        evidence_by_modality = {}
        missing = []
        for modality in ("text", "image", "table"):
            hits = self.multimodal_kb.search(user_input, top_k=2, modalities=[modality])
            if hits:
                evidence_by_modality[modality] = hits
            else:
                missing.append(labels[modality])

        if not evidence_by_modality:
            return "本地多模态知识库未检索到相关证据。"

        lines = [
            "以下为本地多模态知识库检索结果，已分别纳入文献、病例影像和结构化 mask 统计表证据；这些内容用于复现检索与支撑分析，不包装成未经验证的诊断结论。",
            "",
        ]
        for modality in ("text", "image", "table"):
            hits = evidence_by_modality.get(modality, [])
            if not hits:
                continue
            lines.append(f"### {labels[modality]}")
            for index, item in enumerate(hits, start=1):
                metadata = item.get("metadata", {})
                if modality == "image":
                    detail = (
                        f"病例 `{metadata.get('case_id')}`，体数据尺寸 `{metadata.get('shape')}`，"
                        f"影像均值 `{metadata.get('image_mean')}`，标准差 `{metadata.get('image_std')}`。"
                    )
                elif modality == "table":
                    detail = (
                        f"病例 `{metadata.get('case_id')}`，前景体素 `{metadata.get('mask_voxels')}`，"
                        f"前景占比 `{metadata.get('mask_ratio')}`，bbox `{metadata.get('mask_bbox')}`。"
                    )
                else:
                    detail = item.get("text", "")[:260]
                lines.append(f"{index}. **{item.get('title')}**")
                lines.append(f"   - {detail}")
                lines.append(f"   - 证据 ID：`{item.get('record_id')}`；来源：`{item.get('source')}`")
            lines.append("")

        if missing:
            lines.append(f"> 未命中的模态：{'、'.join(missing)}。")
        return "\n".join(lines).strip()

    def dispatch(self, user_input: str):
        intent = self.classify_intent(user_input)
        if intent == "ACTION":
            return {"intent": "ACTION", "result": self.medical_worker.chat_and_execute(user_input)}
        if intent == "MULTIMODAL_QA":
            return {"intent": "MULTIMODAL_QA", "result": self._multimodal_answer(user_input)}
        return {"intent": "QA", "result": self.qa_expert.answer_question(user_input)}

    def run(self):
        print("3D 医疗影像智能全能助理已启动。输入‘退出’结束。")
        while True:
            user_input = input("\n> ").strip()
            if user_input == "退出":
                break
            if user_input:
                print(self.dispatch(user_input)["result"])


if __name__ == "__main__":
    RouterAgent().run()
