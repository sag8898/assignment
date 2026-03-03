# SupportIQ – Persona-Adaptive Customer Support Agent

SupportIQ is an intelligent, reactive customer support agent designed to detect user personas and frustration levels in real-time. It adapts its responses based on the identified persona (Technical Expert, Business Executive, Frustrated User, or General User) and retrieves relevant, tailored content from a built-in knowledge base.

## 🚀 Features

- **🧠 Real-time Persona Detection**: Analyzes technical terminology, business metrics, and sentiment to classify users instantly.
- **📚 Adaptive Knowledge Base**: Retrieval engine that serves persona-specific article content (e.g., code snippets for technical users, SLAs for executives).
- **🚨 Smart Escalation Logic**: Automatically triggers human agent handoffs (with full context) based on frustration thresholds (≥70%), complex issues, or explicit requests.
- **🤝 Dynamic Tone Generation**: Adapts greetings, body text, and call-to-action suggestions based on the detected persona and frustration level.
- **✨ Premium Streamlit Interface**: Beautiful, responsive dark-mode dashboard with real-time stats, frustration meters, and sidebar persona insights.

## 🛠️ Project Structure
```text
/assiggnment
├── models/           # Pydantic data models & enums
├── services/         # Core AI detection, KB search, and response logic
├── streamlit_app.py  # Unified Streamlit frontend
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation (this file)
```

## 🏎️ Running the App

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Launch the Agent
```powershell
streamlit run streamlit_app.py
```

## 🧪 Quick Test Demos
Use the sidebar buttons in the application to simulate:
- **Technical Expert**: Queries regarding OAuth, JWT, and clock skew.
- **Business Executive**: Strategic questions on ROI, SOC 2, and annual pricing.
- **Frustrated User**: Handles high-stress messages with empathetic de-escalation and priority escalation.

## 📄 License
MIT License
