import streamlit as st
# Import the chain and retriever from your backend file
# IMPORTANT: Ensure there is no 'while True' loop at the bottom of medical_rag_agent.py!
from medical_rag_agent import rag_chain, retriever

# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(
    page_title="Medical RAG Agent",
    page_icon="🧬",
    layout="centered"
)

# ==========================================
# 2. UI Header & Description
# ==========================================
st.title("🧬 Medical Multimodal Retrieval Agent")
st.markdown("An expert AI system dedicated to **smart healthcare, medical imaging, and multi-omics data analysis**.")
st.markdown("---")

# ==========================================
# 3. Chat History Initialization
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# 4. User Interaction & Agent Logic
# ==========================================
if prompt := st.chat_input("💡 Ask a question about medical imaging or genomic analysis..."):

    # Append and display user input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent processing
    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent is retrieving knowledge and reasoning..."):
            try:
                # Execute RAG Chain
                response = rag_chain.invoke(prompt)
                source_docs = retriever.invoke(prompt)

                # Display LLM Response
                st.markdown(response)

                # Display Citations in an expander
                with st.expander("📚 View Reference Sources"):
                    if source_docs:
                        for i, doc in enumerate(source_docs):
                            st.markdown(f"**Source {i + 1}:** `{doc.metadata.get('source', 'Unknown')}`")
                            st.caption(f"{doc.page_content[:150]}...")
                    else:
                        st.text("No specific sources retrieved.")

                # Append assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                # Error handling to prevent the white screen of death
                st.error("🚨 An error occurred in the backend processing!")
                st.code(str(e))
                st.info("Did you remember to remove the 'while True' loop in medical_rag_agent.py?")