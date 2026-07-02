from __future__ import annotations

from expert_qa_agent import MedicalExpertAgent
from medical_agent import MedicalDataMinerAgent
from path_config import KNOWLEDGE_BASE_DIR


class RouterAgent:
    ACTION_TERMS = ("处理", "预处理", "清洗", "nifti", "数据集", "重采样", "生成数组")

    def __init__(self):
        self.medical_worker = MedicalDataMinerAgent()
        self.qa_expert = MedicalExpertAgent(KNOWLEDGE_BASE_DIR)

    def classify_intent(self, user_input: str) -> str:
        text = user_input.lower()
        return "ACTION" if any(term in text for term in self.ACTION_TERMS) else "QA"

    def dispatch(self, user_input: str):
        if self.classify_intent(user_input) == "ACTION":
            return {"intent": "ACTION", "result": self.medical_worker.chat_and_execute(user_input)}
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
