# 🤖 NeuroQuery Natural Language Analytics

## 📑 **Table of Contents**
- [📖 Overview](#-overview)
- [🖼️ System Architecture](#-system-architecture)
- [🛠️ Tech Stack](#-tech-stack--libraries)
- [🚀 Key Features](#-key-features)
- [🖥️ UI Walkthrough](#-ui-walkthrough-application-tabs)
- [⚙️ Installation](#-installation--setup)
- [☁️ Deployment](#-deployment-guide)
- [📄 License](#-license)
- [📞 Contact](#-contact--support)

---

## 📖 **Overview**

**NeuroQuery** is a next-generation Business Intelligence platform that replaces static dashboards with **conversational analytics**. Instead of manually filtering charts, users ask questions in plain English (e.g., *"Show me the revenue trend for the East region in Feb 2026"*), and a swarm of **AI Agents** collaborates to generate real-time SQL queries, execute them securely, and visualize the results.

Built for **Enterprise Scalability**, this project features a **Service-Oriented Architecture (SOA)** with a decoupled React-like UI (Streamlit) and a robust API Backend (FastAPI + LangGraph).

---

## �️ **System Architecture**

This project leverages a **Multi-Agent Swarm Architecture** orchestrated by **LangGraph**. Each agent specializes in a distinct cognitive task, ensuring high accuracy and resilience.

### **Core Agent Swarm (The "Brain")**
1.  **� Metadata Agent:** Analysis user intent & schema mapping (Context-Aware).
2.  **🕸️ RAG Agent:** Retrieves certified business definitions from Vector DB.
3.  **📝 SQL Agent:** Generates dialect-specific SQL (SQLite/PostgreSQL) with 99% syntax accuracy.
4.  **🛡️ Impact Agent:** Governance layer; predicts query cost & blocks destructive operations (DROP/DELETE).
5.  **⚙️ Execute Agent:** Runs verified SQL in a sandboxed environment.
6.  **📊 BI Agent:** synthesizes results into JSON configs for Front-end rendering.

---

## 🛠️ **Tech Stack & Libraries**

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | **Streamlit** | Interactive UI with Tabs, Real-time Logs, and Plotly Charts. |
| **Backend** | **FastAPI** | High-performance Async REST API for Agent communication. |
| **Orchestration** | **LangGraph** | Stateful workflow management / Cyclic Graph for Agents. |
| **LLM Framework** | **LangChain** | Prompt engineering & Tool abstractions. |
| **AI Models** | **Groq (Llama 3)** | Ultra-fast inference for real-time SQL generation. |
| **Memory** | **Mem0 (mem0ai)** | Long-term user preference & session storage. |
| **Database** | **SQLite / SQLAlchemy and FAISS , VectorDB** | Relational data storage with ORM. |
| **Task Scheduling** | **APScheduler** | Background jobs and reporting. |
| **Visualization** | **Plotly Express** | Dynamic, interactive data visualizations. |

---

# 🚀 **NeuroQuery: The Conversational Analytics**

How businesses interact with data.Instead of navigating complex dashboards, users simply ask questions in natural language and AI swarm does the rest.

## **🎯 The Problem**
Traditional BI tools require SQL expertise,static dashboard configurations, and constant IT dependency.Business users waste hours waiting for reports that could be answered instantly.

## **💡The Solution: Multi-Agent AI Architecture**

I built an **Enterprise-Grade NeuroQuery Platform** using cutting-edge AI orchestration. Here's how it works:

**🧠 6-Agent Cognitive Swarm (LangGraph Orchestrated):**

1. **Metadata Agent** → Analyzes user intent & schema mapping
2. **RAG Agent** → Retrieves certified business definitions from Vector DB
3. **SQL Agent** → Generates production-ready SQL queries (99% accuracy)
4. **Impact Agent** → Governance layer; blocks unsafe queries & PII exposure
5. **Execute Agent** → Sandboxed SQL execution
6. **BI Agent** → Synthesizes results into intelligent visualizations
   
## **🛠️ Tech Stack (Production-Grade)**

**AI/ML & NLP Layer:**
- **LangGraph** (Multi-Agent Orchestration)
- **LangChain** (Prompt Engineering Framework)
- **Groq** (Llama 3.3 - 70B) for ultra-fast inference
- **HuggingFace** (Text embeddings & transformer models)
- **FuzzyWuzzy** (NLP fuzzy string matching for typo-tolerant queries)
- **Mem0** (Long-term AI memory for user preferences)
  
**Vector & Retrieval:**
- **FAISS** (Facebook AI Similarity Search - Vector DB)
- **RAG Pipeline** (Retrieval Augmented Generation)
- **MCP** (Model Context Protocol for agent-tool communication)
  
**Backend:**
- **FastAPI** (Async REST API)
- **SQLAlchemy** + SQLite/PostgreSQL
- **APScheduler** (Background task management)
  
**Frontend:**
- **Streamlit/Next.js** (Interactive UI with Real-time Agent Logs)
- **Plotly** (Dynamic, responsive visualizations)
  
**DevOps:**
- **Docker-ready** containers
- **CI/CD** pipeline (GitHub Actions)
  
## **🔐Enterprise-Ready Features**
- **Self-Healing Pipeline**:Auto-corrects SQL errors using reflexion loops
- **Typo-Resilient**:FuzzyWuzzy NLP handles misspelled queries intelligently
- **Semantic Search**:FAISS-powered vector similarity for context retrieval
- **Governance**:Built-in RBAC & PII detection
- **Memory**:Learns user preferences across sessions
- **Scalability**:SaaS & On-Prem deployment ready
  
---

## 🚀 **Key Features**

### 1. **Natural Language to SQL**
Type complex business questions like *"Compare marketing ROI vs Sales for Top 5 products"* and get instant charts. No SQL knowledge required.

### 2. **Self-Healing AI Pipeline**
The system uses `LangGraph` to implement **Reflexion**. If an agent generates invalid SQL, the **Execute Agent** feeds the error back to the **SQL Agent** for auto-correction.

### 3. **Enterprise Governance (RBAC)**
Built-in **Impact Agent** ensures security. It calculates "Query Cost" and blocks unauthorized access to sensitive PII columns or tables.

### 4. **Long-Term Memory**
Powered by `mem0`, the system "remembers" your preferred region, currency, and chart types across sessions.

### 5. **Real-Time System Logs**
A dedicated **"System Logs"** tab provides transparency. Watch the "Thought Process" of every agent in real-time (e.g., *Metadata Agent identified 'Sales' table*, *Impact Agent approved query*).

---

## 🖥️ **Walkthrough (Tabs)**

### **Tab 1: 🤖 NeuroQuery**
The main workspace.
- **Chat Interface:** Ask questions.
- **Dynamic Dashboard:** Charts (Bar, Line, Pie) render automatically based on data type.
- **Reasoning Engine:** View the "Why" behind the answer (Show SQL & Thinking).

### **Tab 2:ℹ️ About Project**
-  Project Vision & Mission : NeuroQuery is an enterprise-grade Business Intelligence platform powered by Agentic AI. Users can ask business questions in plain English, and the system intelligently converts them into trusted, governed, explainable insights.
- To democratize data access within enterprises, reducing the dependency on data analyst teams for routine reporting.
- 🚀 AI Analyst , 🧠 Long-Term Memory ,🔐 Enterprise Gov
- In simple words: This system replaces manual BI dashboards with an AI analyst that remembers, learns, and scales securely.

### **Tab 3: 🛠️ Tech Stack & Specs**
Detailed documentation of the libraries used.
- Interactive **badges** for every tool.
- Explanation of **RAG (Retrieval Augmented Generation)** implementation.
  
### **Tab 4: 📐 HLD & LLD**
- 📐 Design & Architecture Specification : Comprehensive documentation covering Software Requirements (SRS), High-Level Design (HLD), and Low-Level Design (LLD).
- 📝 1. Software Requirements Specification (SRS)
-m🏗️ 2. High Level Design (HLD)
- ⚙️ 3. Low Level Design (LLD)
  
### **Tab 5: 📊 Architecture & Design**
- High-Level Design (HLD) & Low-Level Design (LLD).
- Interactive **Graphviz** flowcharts showing data movement between Frontend -> API -> Database.

### **Tab 6: 📋 System Logs**
- **Live Event Feed:** See backend logs in the frontend.
- **Filters:** Filter by `Error`, `Success`, or specific `Agent`.
- **Export:** Download logs as `CSV` or `TXT` for auditing.

---

## ⚙️ **Installation & Setup**

### **Prerequisites**
- Python 3.10+
- Git

### **1. Clone the Repository**
```bash
git clone https://github.com/sohanpatil4600/NeuroQuery.git
cd NeuroQuery
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Configure Environment**
Create a `.env` file in the root directory:
```env
GROQ_API_KEY="your_groq_api_key"
OPENAI_API_KEY="optional_if_using_openai"
SIMULATION_MODE=False
```

### **4. Seed the Database**
Populate the SQLite database with synthetic enterprise data (Sales, CRM, Inventory):
```bash
python seed_db.py
```

### **5. Run the Application**
The app requires both the Backend (FastAPI) and Frontend (Streamlit) to run.

**Terminal 1 (Backend):**
```bash
uvicorn app.main:app --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
python -m streamlit run ui/presentation_app.py
```
> Access the app at `http://localhost:8501`

---


# 📞 **CONTACT & NETWORKING** 📞

[![LinkedIn](https://img.shields.io/badge/💼_LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sohanrpatil/)
[![GitHub](https://img.shields.io/badge/🐙_GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sohanpatil4600)
[![Email](https://img.shields.io/badge/✉️_Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:sohanpatil.usa@gmail.com)

---