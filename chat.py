import streamlit as st
import requests
import json
import pandas as pd
import os
from datetime import datetime

API_URL = "http://localhost:12434/api/generate"
MODEL_NAME = "ai/llama3.2:latest"
EXCEL_FILE = "chat_data.xlsx"

st.set_page_config(page_title="Nexus AI Studio", page_icon="✨", layout="wide")


st.markdown("""
<style>
    /* 1. Chat Message Fade-In Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stChatMessage {
        animation: fadeIn 0.4s ease-out;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        border: 1px solid rgba(255,255,255,0.1);
        background: linear-gradient(145deg, #1e1e24, #18181d);
        box-shadow: 4px 4px 10px rgba(0,0,0,0.2);
    }
    
    /* 2. Modern Cool Buttons with Hover Effects */
    .stButton > button {
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        border: none !important;
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(75, 108, 183, 0.4) !important;
        filter: brightness(1.2);
    }
    .stButton > button:active {
        transform: translateY(1px) scale(0.98) !important;
    }

    /* 3. Glowing Chat Input */
    .stChatFloatingInputContainer {
        padding-bottom: 20px;
    }
    .stChatFloatingInputContainer:focus-within {
        filter: drop-shadow(0 0 10px rgba(75, 108, 183, 0.5));
        transition: 0.3s ease-in-out;
    }
    
    /* Code block styling */
    code {
        background-color: #121212 !important;
        color: #00ffcc !important;
        border-radius: 6px;
        padding: 3px 6px;
        border: 1px solid #333;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def save_to_excel(role, message, tokens=0, error="None"):
    new_row = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Role": role,
        "Message": message,
        "Tokens_Used": tokens,
        "Errors": error
    }])
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(EXCEL_FILE, index=False)
        else:
            new_row.to_excel(EXCEL_FILE, index=False)
    except Exception:
        pass

def load_history():
    st.session_state.messages = []
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            for _, row in df.iterrows():
                if row["Role"] in ["user", "assistant"]:
                    st.session_state.messages.append({"role": row["Role"], "content": str(row["Message"])})
        except Exception:
            pass

def clear_history():
    if os.path.exists(EXCEL_FILE):
        try:
            os.remove(EXCEL_FILE)
        except Exception:
            pass
    st.session_state.messages = []


if "messages" not in st.session_state:
    load_history()
if "stop_generation" not in st.session_state:
    st.session_state.stop_generation = False


with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #4b6cb7;'>⚡ Nexus AI</h2>", unsafe_allow_html=True)
    st.caption("Processor: LLaMA 3.2 | Optimized for Speed")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear", use_container_width=True):
            clear_history()
            st.rerun()
    with col2:
        if st.button("⏹️ Stop", use_container_width=True):
            st.session_state.stop_generation = True
            st.rerun()
            
    st.divider()
    st.markdown("**🔄 Recent Prompts**")
    recent_user_msgs = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
    for msg in recent_user_msgs[-4:]: 
        st.code(msg, language="text") 
        
    st.divider()
    if os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, "rb") as f:
            st.download_button("💾 Export Data", data=f, file_name="chat_backup.xlsx", use_container_width=True)


st.title("Hi! How can I help you? 🚀")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message LLaMA... (Paste code/text here)"):
    
    st.session_state.stop_generation = False
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    save_to_excel("user", prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_reply = ""
       
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_ctx": 1024, 
                "temperature": 0.7 
            }
        }
        
        try:
            response = requests.post(API_URL, json=payload, stream=True, timeout=None)
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if st.session_state.stop_generation:
                        full_reply += "\n\n*[Stopped]*"
                        break
                        
                    if line:
                        chunk = json.loads(line)
                        word = chunk.get("response", "")
                        full_reply += word
                 
                        response_placeholder.markdown(full_reply + " █")
                
                response_placeholder.markdown(full_reply)
                
                token_count = int(len(full_reply.split()) * 1.3)
                st.session_state.messages.append({"role": "assistant", "content": full_reply})
                save_to_excel("assistant", full_reply, tokens=token_count)
                
            else:
                st.error(f"Error {response.status_code}: Model failed.")
                
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Connection Error: Is Docker Port 12434 active?")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")