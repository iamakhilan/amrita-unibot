import streamlit as st
import requests
import os
import time
import re
from datetime import datetime
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import uuid
from database import db
from chroma_manager_alt import chroma_manager
import html

from pathlib import Path
load_dotenv(dotenv_path=Path('.') / '.env')

# Page configuration
st.set_page_config(
    page_title="Amrita UniBot - Your Campus Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
FIXED_MODEL = "openai/gpt-4o-mini"
FIXED_TEMPERATURE = 0.7

# Pre-compile regex patterns for better performance
REGEX_BOLD_DOUBLE_STAR = re.compile(r'\*\*(.*?)\*\*')
REGEX_BOLD_DOUBLE_UNDERSCORE = re.compile(r'__(.*?)__')
REGEX_ITALIC_STAR = re.compile(r'(?<!\*)\*(?!\*)([^\*]+)(?<!\*)\*(?!\*)')
REGEX_ITALIC_UNDERSCORE = re.compile(r'(?<!_)_(?!_)([^_]+)(?<!_)_(?!_)')
REGEX_CODE_BLOCK = re.compile(r'```(.*?)```', re.DOTALL)
REGEX_INLINE_CODE = re.compile(r'`([^`]+)`')
REGEX_NUMBERED_LIST = re.compile(r'(\d+)\.\s+')

# Knowledge base
KNOWLEDGE_BASE = """
AMRITA VISHWA VIDYAPEETHAM - COIMBATORE CAMPUS

🏛️ UNIVERSITY OVERVIEW:
- Established: 2003, A++ NAAC accredited multidisciplinary university
- Campus Size: 800+ acres, main campus of Amrita Vishwa Vidyapeetham
- Location: Ettimadai, Coimbatore, Tamil Nadu, India
- University Type: Private, Deemed-to-be University status

🎓 ACADEMIC PROGRAMS:
Engineering: CSE, ECE, Mechanical, Civil, Aerospace, AI & Data Science, Cybersecurity
Sciences: Physics, Chemistry, Mathematics, Biotechnology, Microbiology
Business: MBA, BBA with various specializations
Arts & Humanities: English, Psychology, Social Work
Medicine: MBBS, Nursing, Physiotherapy, Allied Health Sciences

🏠 CAMPUS FACILITIES:
- Separate hostels for boys and girls with 24/7 security
- Central library with 2+ lakh books and digital resources
- State-of-the-art laboratories and research centers
- Sports complex: Cricket, Football, Basketball, Tennis, Swimming
- Medical center with qualified doctors and ambulance service
- Banking and ATM facilities on campus

🔬 RESEARCH & INNOVATION:
- Centers of Excellence in AI, Robotics, Cybersecurity
- Live-in-Labs® program for rural development
- International collaborations with top universities
- Patent filing and technology transfer support
- Student research opportunities from undergraduate level

🎭 STUDENT LIFE:
- Cultural festivals: Anokha (technical), Shristi (cultural)
- 100+ student clubs and organizations
- Sports teams competing at national level
- International exchange programs
- Placement assistance with 90%+ placement rate

📞 CONTACT INFORMATION:
- Phone: +91-422-2685000
- Email: coimbatore@amrita.edu
- Website: www.amrita.edu
- Address: Amrita Vishwa Vidyapeetham, Ettimadai, Coimbatore - 641112
"""

def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'authenticated': False,
        'user': None,
        'current_conversation_id': None,
        'chat_history': [],
        'conversations': [],
        'show_login': True,
        'show_signup': False,
        'feedback_submitted': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_api_key():
    """Get API key from environment"""
    return os.getenv("API_KEY", "")

def validate_api_key(api_key):
    """Validate API key format"""
    return bool(api_key and api_key.startswith('sk-or-v1-') and len(api_key) > 20)

def format_chat_message(role, content, timestamp=None):
    """Format chat message"""
    return {
        'role': role,
        'content': content,
        'timestamp': timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def format_message_content(content):
    """Format message content for better display with proper HTML escaping and markdown-like formatting"""
    # Escape HTML to prevent XSS
    content = html.escape(content)
    
    # Convert markdown-style formatting to HTML using pre-compiled patterns
    # Bold: **text** or __text__
    content = REGEX_BOLD_DOUBLE_STAR.sub(r'<strong>\1</strong>', content)
    content = REGEX_BOLD_DOUBLE_UNDERSCORE.sub(r'<strong>\1</strong>', content)
    
    # Italic: *text* or _text_
    content = REGEX_ITALIC_STAR.sub(r'<em>\1</em>', content)
    content = REGEX_ITALIC_UNDERSCORE.sub(r'<em>\1</em>', content)
    
    # Code blocks: ```code```
    content = REGEX_CODE_BLOCK.sub(r'<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace;">\1</code>', content)
    
    # Inline code: `code`
    content = REGEX_INLINE_CODE.sub(r'<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace;">\1</code>', content)
    
    # Line breaks: Convert \n to <br>
    content = content.replace('\n', '<br>')
    
    # Lists: Convert - item to bullet points
    lines = content.split('<br>')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('• '):
            if not in_list:
                formatted_lines.append('<ul style="margin: 8px 0; padding-left: 20px;">')
                in_list = True
            item_text = stripped[2:].strip()
            formatted_lines.append(f'<li style="margin: 4px 0;">{item_text}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            if stripped:
                formatted_lines.append(line)
    
    if in_list:
        formatted_lines.append('</ul>')
    
    content = '<br>'.join(formatted_lines)
    
    # Numbers lists: 1. item, 2. item
    content = REGEX_NUMBERED_LIST.sub(r'<strong>\1.</strong> ', content)
    
    return content

def make_api_request(messages, api_key):
    """Make API request to OpenRouter"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Amrita College Chatbot"
    }
    
    payload = {
        "model": FIXED_MODEL,
        "messages": messages,
        "temperature": FIXED_TEMPERATURE,
        "max_tokens": 1000,
        "stream": False
    }
    
    try:
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API request failed: {str(e)}")
        return None

def get_shared_styles():
    """Return shared CSS styles to avoid duplication"""
    return """
    <style>
    /* --- GLOBAL STYLES --- */
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    body {
        background-color: #f0f2f6;
    }

    /* --- LOGIN & SIGNUP PAGES --- */
    .login-container, .signup-container {
        max-width: 480px;
        margin: 40px auto;
        padding: 40px;
        border-radius: 20px;
        background: #ffffff;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border-top: 5px solid #667eea;
    }
    
    .login-header, .signup-header {
        text-align: center;
        margin-bottom: 35px;
    }
    
    .login-header h1, .signup-header h1 {
        font-size: 2.4em;
        font-weight: 700;
        color: #2c3e50;
        margin: 15px 0 5px 0;
    }
    
    .login-header h3, .signup-header h3 {
        font-size: 1.1em;
        font-weight: 400;
        color: #6c757d;
    }
    
    /* Input field styling */
    .stTextInput input {
        border-radius: 10px !important;
        border: 2px solid #e0e6ed !important;
        background: #f8f9fa !important;
        padding: 14px 18px !important;
        font-size: 16px !important;
        color: #333 !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        padding: 14px 24px !important;
        border: none !important;
        border-radius: 10px !important;
        cursor: pointer;
        font-size: 17px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .navigation-button button {
        background: transparent !important;
        color: #667eea !important;
        border: none !important;
        text-decoration: none;
        font-size: 15px !important;
        padding: 10px !important;
        font-weight: 600 !important;
    }
    
    .navigation-button button:hover {
        text-decoration: underline !important;
        background: transparent !important;
        transform: none !important;
        box-shadow: none !important;
    }
    </style>
    """

def get_chat_styles():
    """Return chat interface specific CSS styles"""
    return """
    <style>
    /* --- GLOBAL STYLES --- */
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    body {
        background-color: #f0f2f6;
    }

    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Chat messages container */
    .chat-messages-container {
        background: #ffffff;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        max-height: 600px;
        overflow-y: auto;
        box-shadow: 0 5px 25px rgba(0,0,0,0.07);
    }
    
    /* User message bubble */
    .user-message-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 14px 20px;
        border-radius: 18px 18px 4px 18px;
        margin: 10px 0 10px auto;
        max-width: 75%;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        animation: slideInRight 0.4s ease-out;
        word-wrap: break-word;
        line-height: 1.6;
    }
    
    /* Bot message bubble */
    .bot-message-bubble {
        background: #e9ecef;
        color: #2c3e50;
        padding: 14px 20px;
        border-radius: 18px 18px 18px 4px;
        margin: 10px auto 10px 0;
        max-width: 75%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        animation: slideInLeft 0.4s ease-out;
        word-wrap: break-word;
        line-height: 1.7;
    }
    
    .bot-message-bubble strong {
        color: #667eea;
        font-weight: 600;
    }
    
    .bot-message-bubble ul {
        margin: 10px 0;
        padding-left: 20px;
    }
    
    .bot-message-bubble li {
        margin: 6px 0;
    }
    
    /* Timestamp */
    .message-timestamp {
        font-size: 0.75em;
        opacity: 0.65;
        margin-top: 6px;
        font-style: italic;
    }
    
    /* Input styling */
    .stTextInput input {
        border-radius: 25px !important;
        border: 2px solid #e0e6ed !important;
        padding: 14px 22px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Form submit button */
    .stForm button[type="submit"] {
        border-radius: 50% !important;
        width: 55px !important;
        height: 55px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        font-size: 22px !important;
        cursor: pointer;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stForm button[type="submit"]:hover {
        transform: scale(1.08) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e0e6ed;
    }
    
    .sidebar-content {
        padding: 15px 10px;
    }
    
    .user-info-card {
        text-align: center;
        padding: 25px;
        background: linear-gradient(135deg, #f5f7fa 0%, #e8edf3 100%);
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #e0e6ed;
    }
    
    .user-info-card h3 {
        color: #667eea;
        font-size: 1.4em;
        margin: 10px 0;
        font-weight: 600;
    }
    
    .user-info-card p {
        color: #6c757d;
        font-size: 0.95em;
        line-height: 1.6;
        margin: 8px 0;
    }
    
    /* Sidebar buttons */
    .stSidebar .stButton button {
        background: #667eea !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100%;
        font-size: 15px !important;
    }
    
    .stSidebar .stButton button:hover {
        background: #764ba2 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Conversation history buttons */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        color: #495057 !important;
        text-align: left !important;
        padding: 12px 15px !important;
        margin: 6px 0 !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: #e9ecef !important;
        border-color: #667eea !important;
        transform: translateX(5px);
    }
    
    /* Divider styling */
    .stSidebar hr {
        margin: 20px 0;
        border: none;
        height: 1px;
        background: #e0e6ed;
    }
    
    /* Animations */
    @keyframes slideInRight {
        from { transform: translateX(50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); }
    </style>
    """


def login_page():
    """Display login page"""
    st.markdown(get_shared_styles(), unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown('<div class="login-header">', unsafe_allow_html=True)
        st.image("https://www.amrita.edu/sites/default/files/amrita-logo.png", width=100)
        st.markdown('<h1>Welcome Back</h1>', unsafe_allow_html=True)
        st.markdown('<h3>Login to access Amrita UniBot</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            roll_number = st.text_input("📝 Roll Number", placeholder="Enter your roll number")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            login_submit = st.form_submit_button("🚀 Login")
        
        if login_submit:
            if roll_number and password:
                roll_number = roll_number.strip()
                password = password.strip()
                
                success, user_data = db.authenticate_user(roll_number, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user = user_data
                    st.session_state.show_login = False
                    st.success(f"✅ Welcome back, {user_data['full_name']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid roll number or password")
            else:
                st.error("⚠️ Please fill in all fields")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Navigation to signup
        st.markdown('<div class="navigation-button" style="text-align: center;">', unsafe_allow_html=True)
        if st.button("✨ New to UniBot? Sign up here", use_container_width=True, key="goto_signup"):
            st.session_state.show_signup = True
            st.session_state.show_login = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def signup_page():
    """Display signup page"""
    st.markdown(get_shared_styles(), unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="signup-container">', unsafe_allow_html=True)
        
        st.markdown('<div class="signup-header">', unsafe_allow_html=True)
        st.image("https://www.amrita.edu/sites/default/files/amrita-logo.png", width=100)
        st.markdown('<h1>Create Your Account</h1>', unsafe_allow_html=True)
        st.markdown('<h3>Join UniBot to get started</h3>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.form("signup_form"):
            full_name = st.text_input("👤 Full Name", placeholder="Enter your full name")
            roll_number = st.text_input("📝 Roll Number", placeholder="Enter your roll number")
            email = st.text_input("📧 Email (Optional)", placeholder="Enter your email")
            department = st.text_input("🏛️ Department (Optional)", placeholder="Enter your department")
            password = st.text_input("🔒 Password", type="password", placeholder="Create a password (min 6 characters)")
            confirm_password = st.text_input("🔐 Confirm Password", type="password", placeholder="Confirm your password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            signup_submit = st.form_submit_button("🎉 Create Account")
        
        if signup_submit:
            if all([full_name, roll_number, password, confirm_password]):
                full_name = full_name.strip()
                roll_number = roll_number.strip()
                email = email.strip() if email else None
                department = department.strip() if department else None
                password = password.strip()
                confirm_password = confirm_password.strip()
                
                if password == confirm_password:
                    if len(password) >= 6:
                        success, message = db.create_user(roll_number, password, full_name, email, department)
                        if success:
                            st.success("✅ Account created successfully! Please login.")
                            time.sleep(2)
                            st.session_state.show_signup = False
                            st.session_state.show_login = True
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("⚠️ Password must be at least 6 characters long")
                else:
                    st.error("❌ Passwords do not match")
            else:
                st.error("⚠️ Please fill in all required fields")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Navigation to login
        st.markdown('<div class="navigation-button" style="text-align: center;">', unsafe_allow_html=True)
        if st.button("🔙 Already have an account? Login here", use_container_width=True, key="goto_login"):
            st.session_state.show_signup = False
            st.session_state.show_login = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def chat_interface():
    """Main chat interface"""
    st.markdown(get_chat_styles(), unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        # User info card
        st.markdown('<div class="user-info-card">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=80)
        st.markdown(f"<h3>{st.session_state.user['full_name']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p><b>Roll:</b> {st.session_state.user['roll_number']}</p>", unsafe_allow_html=True)
        if st.session_state.user.get('department'):
            st.markdown(f"<p><b>Dept:</b> {st.session_state.user['department']}</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # New Chat button
        if st.button("➕ New Chat", key="new_chat"):
            st.session_state.current_conversation_id = None
            st.session_state.chat_history = []
            st.rerun()
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Conversation history
        st.markdown("<h4>📜 Conversation History</h4>", unsafe_allow_html=True)
        conversations = db.get_user_conversations(st.session_state.user['id'])
        
        for conv in conversations:
            conv_id = conv['id']
            title = conv['title']
            
            if st.button(title, key=f"conv_{conv_id}", use_container_width=True):
                st.session_state.current_conversation_id = conv['conversation_id']
                st.session_state.chat_history = db.get_conversation_messages(conv['conversation_id'])
                st.rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Logout button
        if st.button("🚪 Logout", key="logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.current_conversation_id = None
            st.session_state.chat_history = []
            st.session_state.show_login = True
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Main chat area
    st.header("🎓 Amrita UniBot")
    
    # Chat messages display
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-messages-container">', unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            bubble_class = "user-message-bubble" if message['role'] == 'user' else "bot-message-bubble"
            formatted_content = format_message_content(message['content'])
            
            st.markdown(f"""
            <div class="{bubble_class}">
                {formatted_content}
                <div class="message-timestamp">{message['timestamp']}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([10, 1])
        with col1:
            user_input = st.text_input("Ask me anything about Amrita...", key="user_input", label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button("➤")

    if submit_button and user_input:
        api_key = get_api_key()
        if not validate_api_key(api_key):
            st.error("❌ Invalid or missing API key. Please set it correctly.")
            return

        user_message = format_chat_message("user", user_input)
        st.session_state.chat_history.append(user_message)
        
        # Create new conversation if it's a new chat
        if not st.session_state.current_conversation_id:
            conv_id = str(uuid.uuid4())
            db.create_conversation(st.session_state.user['id'], conv_id, user_input)
            st.session_state.current_conversation_id = conv_id
        
        db.save_message(st.session_state.current_conversation_id, "user", user_input)

        system_prompt = f"""
        You are Amrita UniBot, a helpful assistant for Amrita Vishwa Vidyapeetham, Coimbatore.
        Your goal is to provide accurate and helpful information based on the provided context.
        If the answer is not in the context, say so. Do not make up information.
        
        Context from Knowledge Base:
        {KNOWLEDGE_BASE}
        """
        
        messages_for_api = [
            {"role": "system", "content": system_prompt},
            *[{"role": m['role'], "content": m['content']} for m in st.session_state.chat_history]
        ]
        
        with st.spinner("🤖 Thinking..."):
            api_response = make_api_request(messages_for_api, api_key)
        
        if api_response and 'choices' in api_response and api_response['choices']:
            bot_response = api_response['choices'][0]['message']['content']
            bot_message = format_chat_message("assistant", bot_response)
            st.session_state.chat_history.append(bot_message)
            db.save_message(st.session_state.current_conversation_id, "assistant", bot_response)
        else:
            st.error("❌ Failed to get a response from the bot.")
            
        st.rerun()

def main():
    """Main function to run the Streamlit app"""
    initialize_session_state()
    
    if not st.session_state.authenticated:
        if st.session_state.show_signup:
            signup_page()
        else:
            login_page()
    else:
        chat_interface()

if __name__ == "__main__":
    main()