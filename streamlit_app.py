import streamlit as st
from PIL import Image
import io
import base64
from rag_chatbot import VisionChatbot
import tempfile
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the chatbot
@st.cache_resource
def get_chatbot():
    # Try to get token from Streamlit secrets first, then environment variables
    hf_token = st.secrets.get("HUGGING_FACE_TOKEN", os.getenv("HUGGING_FACE_TOKEN"))
    if not hf_token:
        st.error("Hugging Face API token not found!")
        st.stop()
    
    # Remove the api_token parameter since the class gets it from environment variables
    return VisionChatbot()

# Page configuration
st.set_page_config(
    page_title="RAGgle AI by Gokul",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Simplified and cleaner
st.markdown("""
    <style>
    /* Remove ALL default margins and padding */
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Remove top padding from main container */
    .main > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* Remove extra padding from Streamlit elements */
    .element-container, .stMarkdown {
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Adjust main content padding */
    .main {
        padding: 1rem !important;
        max-width: 1000px;
        margin: 0 auto !important;
    }

    /* Remove padding from title */
    .stTitle, h1 {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Remove default streamlit gaps */
    div[data-testid="stVerticalBlock"] > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Fix title visibility and styling */
    .stTitle {
        margin-top: 1rem !important;
        padding-top: 1rem !important;
        visibility: visible !important;
    }
    
    /* Custom title styling */
    .custom-title {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        
        margin: 0.5rem 0 !important;
        padding: 0.5rem 0 !important;
        line-height: 1.2 !important;
    }
    
    .custom-subtitle {
        font-size: 1.2rem !important;
        color: #666;
        margin-bottom: 1rem !important;
        font-weight: 400 !important;
    }

    /* Ensure header container is visible */
    header {
        visibility: visible !important;
        height: auto !important;
        min-height: 0 !important;
    }

    /* Chat UI Styles */
    .message {
        display: flex;
        align-items: flex-start;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 12px;
        max-width: 90%;
    }

    .user-message {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        margin-left: auto;
    }

    .assistant-message {
        background: rgba(17, 19, 26, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-right: auto;
    }

    .avatar {
        font-size: 1.5rem;
        margin-right: 1rem;
        min-width: 30px;
    }

    .message-content {
        color: #E2E8F0;
        font-size: 1.05rem;
        line-height: 1.7;
    }

    .user-message .message-content {
        color: #93C5FD;
    }

    /* Chat container */
    .chat-container {
        padding: 2rem;
        border-radius: 12px;
        background: rgba(17, 19, 26, 0.6);
        margin: 1rem 0;
        max-height: 600px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

def create_message_bubble(text, is_user=False):
    if is_user:
        return f"""
            <div style="
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 0.5rem;
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.2);
                margin-left: auto;
                max-width: 80%;
                display: flex;
                gap: 0.5rem;
            ">
                <div>👤</div>
                <div style="color: #93C5FD;">{text}</div>
            </div>
        """
    else:
        return f"""
            <div style="
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 0.5rem;
                background: rgba(17, 19, 26, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                margin-right: auto;
                max-width: 80%;
                display: flex;
                gap: 0.5rem;
            ">
                <div>🤖</div>
                <div style="color: #E2E8F0;">{text}</div>
            </div>
        """

# Initialize chatbot
chatbot = get_chatbot()

# Header
st.markdown('<h1 class="custom-title">🔮 RAGgle AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="custom-subtitle">Your intelligent companion for conversation and file analysis | Powered by LLaMA Vision</p>', unsafe_allow_html=True)

# Main content
st.markdown("---")

# Clear chat button
col1, col2 = st.columns([5,1])
with col2:
    if st.button("🗑️ Clear", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

# File upload section
with st.container():
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload PDF or Image",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Supported formats: PDF, PNG, JPG, JPEG",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        st.success(f"📎 File uploaded: {uploaded_file.name}")
        
        if file_ext in ['jpg', 'jpeg', 'png']:
            image = Image.open(uploaded_file)
            st.image(image, caption='Preview', use_column_width=True)
        else:
            st.info("📄 PDF document loaded")
    st.markdown('</div>', unsafe_allow_html=True)

# Chat interface
if 'messages' not in st.session_state:
    st.session_state.messages = []

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    st.markdown(
        create_message_bubble(
            message["content"],
            is_user=message["role"] == "user"
        ),
        unsafe_allow_html=True
    )
st.markdown('</div>', unsafe_allow_html=True)

# Query input
query = st.text_input(
    "Query",
    placeholder="Ask me anything...",
    label_visibility="collapsed"
)

if st.button("Send 🚀", use_container_width=True):
    if query:
        try:
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": query
            })
            
            with st.spinner('Processing...'):
                if uploaded_file:
                    # Handle file-based query
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    response = chatbot.generate_response(
                        file_path=tmp_path,
                        text_prompt=query,
                        file_type=file_ext
                    )
                    os.unlink(tmp_path)
                else:
                    # Handle text-only query
                    response = chatbot.generate_response(text_prompt=query)
                
                # Add assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                
                st.experimental_rerun()
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a question!")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Built by Gokul with ❤️ using Streamlit and LLaMA Vision</p>
    </div>
    """,
    unsafe_allow_html=True
) 
