import gradio as gr
from agent import EpigenomicsAgent

agent = EpigenomicsAgent()

def respond(message, history):
    result = agent.query(message)
    return result.get("answer", "No answer generated.")

with gr.Blocks(title="Epigenomics AI Agent") as demo:
    gr.Markdown("""
    #  Epigenomics AI Agent
    """)

    gr.ChatInterface(
        fn=respond,
        title="Epigenomics Q&A",
        description="By Sabij"
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())