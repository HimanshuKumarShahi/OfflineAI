import requests
import json
import pandas as pd
import os
from datetime import datetime
import sys

# ==========================================
# ⚙️ SETTINGS
# ==========================================
API_URL = "http://localhost:12434/api/generate"
MODEL_NAME = "ai/llama3.2:latest"
EXCEL_FILE = "chat_data.xlsx"

# ==========================================
# 🗄️ DATABASE FUNCTION
# ==========================================
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
    except Exception:
        pass # CLI me background errors ko ignore karenge taaki chat disturb na ho

# ==========================================
# 🚀 MAIN CLI APP
# ==========================================
def main():
    print("="*50)
    print("🤖 OFFLINE AI CLI (LLaMA 3.2: 3B)")
    print(" Type 'exit', 'quit' or 'clear' to manage chat.")
    print("="*50)

    while True:
        try:
            # User Input
            user_input = input("\n🧑 You: ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Bye! Chat saved to Excel.")
                break
                
            if user_input.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print("✨ Screen Cleared!")
                continue

            if not user_input.strip():
                continue

            save_to_excel("user", user_input)

            # AI Response
            print("🤖 AI: ", end="", flush=True)
            
            payload = {
                "model": MODEL_NAME,
                "prompt": user_input,
                "stream": True
            }
            
            # timeout=None lagaya hai taaki timeout error na aaye
            response = requests.post(API_URL, json=payload, stream=True, timeout=None)
            
            if response.status_code != 200:
                print(f"\n[Error: {response.status_code}] {response.text}")
                continue
                
            full_reply = ""
            
            # Streaming word by word
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    word = chunk.get("response", "")
                    full_reply += word
                    # Har word ko turant print karega bina naye line ke
                    print(word, end="", flush=True) 
            
            print() # Nayi line AI ka jawab khatam hone ke baad
            
            # Save AI response
            token_count = int(len(full_reply.split()) * 1.3)
            save_to_excel("assistant", full_reply, tokens=token_count)
            
        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Docker Model (Port 12434) is not running.")
        except KeyboardInterrupt:
            print("\n👋 App Closed.")
            sys.exit()
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()