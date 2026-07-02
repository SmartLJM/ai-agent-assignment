from app import answer_question

if __name__ == "__main__":
    examples = [
        "What is target identification in drug discovery?",
        "Compare pharmacokinetics and pharmacodynamics.",
        "What is the molecular weight of aspirin?"
    ]
    for q in examples:
        print("\nQ:", q)
        print("A:", answer_question(q, show_trace=False))
