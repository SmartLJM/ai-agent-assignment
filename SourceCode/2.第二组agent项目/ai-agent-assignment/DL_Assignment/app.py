"""Drug Discovery Agentic Q&A App

Default mode is deterministic RAG + dynamic orchestration. Put the optional Phi-3
GGUF file into models/ and set USE_LLM=true only if you want to extend synthesis.
"""
from src.orchestrator import DynamicOrchestrator

orchestrator = DynamicOrchestrator()

def answer_question(question, show_trace=False):
    answer, trace = orchestrator.answer(question, return_trace=True)
    if show_trace:
        import json
        return answer + "\n\n--- Execution trace ---\n" + json.dumps(trace, indent=2, ensure_ascii=False)
    return answer

if __name__ == "__main__":
    try:
        import gradio as gr
        with gr.Blocks(title="Drug Discovery Agentic Q&A") as demo:
            gr.Markdown("# Drug Discovery Agentic Q&A\nMulti-level memory + advanced dynamic orchestration + PubChem SKILL")
            q = gr.Textbox(label="Question", placeholder="Example: What is the molecular weight of aspirin?")
            show_trace = gr.Checkbox(label="Show execution trace", value=False)
            a = gr.Textbox(label="Answer", lines=12)
            btn = gr.Button("Ask")
            btn.click(fn=answer_question, inputs=[q, show_trace], outputs=a)
            gr.Examples([
                ["What is target validation?", False],
                ["Compare pharmacokinetics and pharmacodynamics.", True],
                ["What is the molecular weight of aspirin?", True],
                ["Why is a docking score not enough to approve a drug?", True]
            ], inputs=[q, show_trace])
        demo.launch()
    except Exception as e:
        print("Gradio UI could not start:", e)
        print("CLI fallback. Type a question or blank line to exit.")
        while True:
            query = input("Question: ").strip()
            if not query:
                break
            print(answer_question(query, show_trace=False))
