### Step 1: Start the AI Model in Docker

1. Open **Docker Desktop**.

2. Go to the **Models** tab on the left sidebar.

3. Locate `ai/llama3.2:latest` and click the **Play (▶️)** button to start the local model server.


### Step 2: Open Terminal & Navigate to Project Folder
Open Command Prompt (CMD) or VS Code Terminal and navigate to your project directory:
```bash
cd path\to\OFFLINECHATAPP
---

```bash
1.      .venv\Scripts\activate

2.      pip install streamlit requests pandas openpyxl

3.      streamlit run app.py


```

```
OFFLINECHATAPP/
│
├── .venv/                   # Python Virtual Environment folder
├── chat_data.xlsx           # Auto-generated offline chat history database
├── app.py                   # Main Python application (Frontend + API Logic)
└── README.md                # Documentation & Setup Guide
```

