import streamlit as st
from langgraph_backend import chatbot,retrive_all_threads
from langchain_core.messages import HumanMessage
import uuid

# -------------------------------
# Utility Functions
# -------------------------------

def generate_thread_id():
    """Generate a unique thread ID."""
    return uuid.uuid4()

def add_thread(thread_id):
    """Add a new thread ID if not already in session."""
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def reset_chat():
    """Start a new conversation thread."""
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def load_conversation(thread_id):
    """Load past conversation messages for a thread."""
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    if state and 'messages' in state.values:
        return state.values['messages']
    return []

# -------------------------------
# Initialize Session State
# -------------------------------

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrive_all_threads()

add_thread(st.session_state['thread_id'])

# -------------------------------
# Sidebar UI
# -------------------------------

st.sidebar.title("LangGraph Chatbot")

# Start new chat
if st.sidebar.button("New Chat"):
    reset_chat()

# Display existing threads
st.sidebar.header("My Conversations")
for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)): 
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)
        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        st.session_state['message_history'] = temp_messages

# -------------------------------
# Chat UI
# -------------------------------

st.title("LangGraph Chat Assistant")

# Show message history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Show user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    # Prepare configuration for the current chat thread
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # Stream AI response
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content # pyright: ignore[reportAttributeAccessIssue]
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG, # pyright: ignore[reportArgumentType]
                stream_mode='messages'
            )
        )

    # Save AI response to message history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
