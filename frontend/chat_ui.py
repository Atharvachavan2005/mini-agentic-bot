import streamlit as st
from backend.agent import agent_graph
from langchain_core.agents import AgentFinish

st.title("Project Management AI Assistant 🤖")


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you manage your projects today?"}]

if "checkpoint" not in st.session_state:
    st.session_state.checkpoint = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Ask me to manage tasks or users..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        full_response = ""
        

        if st.session_state.thread_id:
            response_generator = agent_graph.stream(
                {"input": prompt}, 
                config={"configurable": {"thread_id": st.session_state.thread_id}}
            )
        else:
            inputs = {"input": prompt, "chat_history": []}
            response_generator = agent_graph.stream(inputs, config={"configurable": {"thread_id": "main"}})
            st.session_state.thread_id = "main"

        current_state = None
        final_chunk = None
        
        all_chunks = []
        for chunk in response_generator:
            all_chunks.append(chunk)
            if "__end__" not in chunk:
                current_state = list(chunk.values())[0]

        if current_state:
            final_outcome = current_state.get("agent_outcome")
            if isinstance(final_outcome, AgentFinish):
                full_response = final_outcome.return_values['output']
            elif current_state.get("pending_action"):
                summary = current_state["pending_action"]["summary"]
                full_response = summary + "\n\nAre you sure you want to proceed? (yes/no)"

            else:
                if st.session_state.thread_id and len(all_chunks) > 0:
                    last_chunk = all_chunks[-1]
                    if "__end__" in last_chunk:
                        full_response = "Task completed successfully!"
                    else:
                        full_response = "Processing your request..."
                else:
                    full_response = "An unexpected error occurred. Please try again."
        else:
            full_response = "Sorry, I couldn't process that. Please try again."

    with st.chat_message("assistant"):
        st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})