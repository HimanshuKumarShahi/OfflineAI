import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# ==========================================
# ⚙️ SETTINGS & CONFIGURATION
# ==========================================
API_URL = "http://localhost:12434/api/generate"
MODEL_NAME = "ai/llama3.2:latest"
EXCEL_FILE = "chat_data.xlsx"

# Modern Wide Layout
st.set_page_config(page_title="Offline AI Workspace", page_icon="⚡", layout="wide")

# Custom CSS for modern look
st.markdown("""
<style>
    .stChatFloatingInputContainer { padding-bottom: 20px; }
    .sidebar-text { font-size: 0.9rem; color: #6c757d; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 🗄️ DATABASE FUNCTIONS (CRUD Operations)
# ==========================================

# 1. CREATE & UPDATE (Save message to Excel)

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
            existing_data = pd.read_excel(EXCEL_FILE)
            updated_data = pd.concat([existing_data, new_row], ignore_index=True)
            updated_data.to_excel(EXCEL_FILE, index=False)
        else:
            new_row.to_excel(EXCEL_FILE, index=False)
    except PermissionError:
        # Agar Excel open hai toh app crash nahi hoga, bas ye warning dega
        st.toast("⚠️ Data save nahi hua: Kripya 'chat_data.xlsx' ko Excel me close karein.", icon="❌")
    except Exception as e:
        st.toast(f"⚠️ File error: {e}", icon="❌")

# ... (load_history function waisa hi rahega) ...

# 3. DELETE (Clear entire chat history)
def clear_history():
    if os.path.exists(EXCEL_FILE):
        try:
            os.remove(EXCEL_FILE)
        except PermissionError:
            st.error("⚠️ History Delete nahi hui: Pehle 'chat_data.xlsx' ko background me close karein.")
            return # Yahan se wapas bhej dega taaki screen par history bachi rahe
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
            return
            
    st.session_state.messages = []
    st.session_state.total_tokens = 0

# 2. READ (Load history into Session State)
def load_history():
    st.session_state.messages = []
    st.session_state.total_tokens = 0
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            for index, row in df.iterrows():
                if row["Role"] in ["user", "assistant"]:
                    st.session_state.messages.append({"role": row["Role"], "content": str(row["Message"])})
                # Calculate total tokens used
                if pd.notna(row.get("Tokens_Used")):
                    st.session_state.total_tokens += int(row["Tokens_Used"])
        except Exception as e:
            st.error(f"Failed to load history: {e}")
    else:
        st.session_state.total_tokens = 0

# 3. DELETE (Clear entire chat history)
def clear_history():
    if os.path.exists(EXCEL_FILE):
        os.remove(EXCEL_FILE)
    st.session_state.messages = []
    st.session_state.total_tokens = 0


# Initialize session state on first load
if "messages" not in st.session_state:
    load_history()


# ==========================================
# ⬅️ LEFT PANEL (SIDEBAR) - HISTORY & SETTINGS
# ==========================================
with st.sidebar:
    st.title("⚡ AI Workspace")
    st.caption("Powered by LLaMA 3.2 (Offline)")
    st.divider()
    
    # Show Stats
    st.subheader("📊 Session Stats")
    st.write(f"**Total Messages:** {len(st.session_state.messages)}")
    st.write(f"**Tokens Used:** ~{st.session_state.total_tokens}")
    
    st.divider()
    
    # CRUD: Delete Operation
    st.subheader("⚙️ Manage Data")
    if st.button("🗑️ Clear Chat History", use_container_width=True, type="primary"):
        clear_history()
        st.success("History Cleared!")
        st.rerun()
        
    # CRUD: Read/Download Operation
    if os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, "rb") as file:
            btn = st.download_button(
                label="💾 Download Excel Data",
                data=file,
                file_name=f"chat_backup_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
    st.divider()
    
    # Recent History Preview
    st.subheader("🕒 Recent Prompts")
    recent_prompts = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
    if recent_prompts:
        for prompt in recent_prompts[-5:]: # Show last 5 prompts
            st.markdown(f"<div class='sidebar-text'>💬 {prompt[:30]}...</div>", unsafe_allow_html=True)
    else:
        st.caption("No history yet.")


# ==========================================
# ➡️ RIGHT PANEL (MAIN CHAT AREA)
# ==========================================
st.header("💬 Chat with LLaMA")

# Container for chat messages
chat_container = st.container()

# Display Chat History
with chat_container:
    if not st.session_state.messages:
        st.info("👋 Welcome! Start a conversation by typing below. Everything is saved locally on your computer.")
        
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat Input at the bottom
if prompt := st.chat_input("Ask anything (Code, logic, writing)..."):
    
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)
            
    # 2. Save user message to DB
    save_to_excel(role="user", message=prompt)

    # 3. Process AI Response
    with chat_container:
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
            
            try:
                with st.spinner("🧠 Generating response..."):
                    response = requests.post(API_URL, json=payload, stream=True, timeout=None)
                    
                    if response.status_code != 200:
                        raise Exception(f"Error {response.status_code}: {response.text}")
                    
                    data = response.json()
                    ai_reply = data.get("response", str(data))
                    token_count = int(len(str(ai_reply).split()) * 1.3)
                    
                    # Typewriter effect can be added here, but direct markdown is faster
                    response_placeholder.markdown(ai_reply)
                    
                    # Update session & DB
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    st.session_state.total_tokens += token_count
                    save_to_excel(role="assistant", message=ai_reply, tokens=token_count)
                    
            except requests.exceptions.ConnectionError:
                error_msg = "⚠️ **Connection Error:** Please make sure Docker Model is running on port 12434."
                response_placeholder.error(error_msg)
                save_to_excel(role="system", message="", error=error_msg)
                
            except Exception as e:
                error_msg = f"⚠️ **Error:** {str(e)}"
                response_placeholder.error(error_msg)
                save_to_excel(role="system", message="", error=error_msg)