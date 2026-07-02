from __future__ import annotations

from rag_core import ask_rag


# PyCharm can run this file directly. Edit this question for a one-shot run.
QUESTION = "Nicheformer 这篇论文主要解决了单细胞和空间组学中的什么问题？"

# Set to True if you want to type questions in the PyCharm console.
INTERACTIVE = False


def run_one_question(question: str) -> None:
    result = ask_rag(question)
    print()
    print("Question:")
    print(result["question"])
    print()
    print("Answer:")
    print(result["answer"])
    print()
    print("Retrieved sources:")
    for source in result["sources"]:
        page = source.get("page")
        page_text = f", page={page}" if page not in ("", None) else ""
        score = source.get("similarity")
        score_text = f", score={score:.4f}" if isinstance(score, float) else ""
        print(f"- [{source['rank']}] {source.get('title')}{page_text}{score_text}")
    if result.get("memory_context"):
        print()
        print("Memory context used:")
        print(result["memory_context"])
    if result.get("memory_episode_id"):
        print()
        print(f"Memory episode id: {result['memory_episode_id']}")


def main() -> None:
    if INTERACTIVE:
        while True:
            question = input("\n请输入问题，直接回车退出：").strip()
            if not question:
                break
            run_one_question(question)
        return

    run_one_question(QUESTION)


if __name__ == "__main__":
    main()
