# 🚀 AI-Powered Multi-Agent Workflow Automation Platform

A production-style AI workflow automation platform where multiple intelligent agents collaborate to solve complex user tasks through planning, research, analysis, execution, and synthesis.

The system uses an orchestrator-driven architecture that decomposes user goals into subtasks, delegates work to specialized agents, tracks execution in real time, and maintains complete audit logs for transparency and cost monitoring.

---

## 🌐 Live Demo

### Frontend Application

https://ai-powered-multi-agent-workflow-aut.vercel.app/

### Backend API

https://ai-powered-multi-agent-workflow-17hi.onrender.com

### API Documentation

https://ai-powered-multi-agent-workflow-17hi.onrender.com/docs

---

## 📂 GitHub Repository

https://github.com/Ashishiqbalcse/ai-powered-multi-agent-workflow-automation-platform

---

# ✨ Key Features

## Multi-Agent Architecture

The platform coordinates multiple specialized AI agents that work together to solve user requests.

### Included Agents

- Orchestrator Agent
- Web Search Agent
- Data Analysis Agent
- Code Execution Agent
- Result Synthesizer Agent

---

## Intelligent Task Planning

- Breaks complex goals into manageable subtasks
- Assigns work to appropriate agents
- Tracks execution status
- Maintains execution history

---

## Real-Time Workflow Monitoring

- Live execution trace
- Agent status tracking
- Event streaming via WebSockets
- Detailed workflow visibility

---

## Search & Knowledge Retrieval

- Tavily Search API Integration
- Context-aware information retrieval
- Multi-source research support
- Structured result aggregation

---

## Human-in-the-Loop Approval

For sensitive or risky actions:

- Execution pause
- Approval requests
- Decision logging
- Audit trail generation

---

## Cost Tracking & Audit Logs

Tracks:

- API usage
- Agent activity
- Workflow history
- Execution metadata
- Cost estimates

---

# 🏗️ System Architecture

```text
                    User
                      │
                      ▼
             React Frontend
                      │
                      ▼
                FastAPI API
                      │
                      ▼
             Orchestrator Agent
                      │
 ┌────────────┬────────────┬────────────┐
 ▼            ▼            ▼            ▼
Web Search  Data Analysis  Code Exec  Synthesizer
 Agent         Agent        Agent       Agent
 └────────────┴────────────┴────────────┘
                      │
                      ▼
               Agent Memory
                      │
                      ▼
              SQLite Database
```

---

# 🛠️ Technology Stack

## Frontend

- React.js
- TypeScript
- Vite
- Tailwind CSS
- WebSockets

## Backend

- FastAPI
- Python
- SQLAlchemy
- SQLite
- Pydantic

## AI & Agent Framework

- Multi-Agent Architecture
- Tavily Search API
- Ollama (Local Development)
- LangGraph Ready

## DevOps & Deployment

- GitHub
- GitHub Actions
- Docker
- Docker Compose
- Render
- Vercel

---

# 📸 Screenshots

## Dashboard

Add screenshot:

```text
screenshots/dashboard.png
```

## Live Agent Trace

Add screenshot:

```text
screenshots/live-trace.png
```

## Workflow Result

Add screenshot:

```text
screenshots/result.png
```

---

# ⚙️ Local Setup

## Clone Repository

```bash
git clone https://github.com/Ashishiqbalcse/ai-powered-multi-agent-workflow-automation-platform.git

cd ai-powered-multi-agent-workflow-automation-platform
```

---

## Configure Environment

Create a .env file:

```env
TAVILY_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key
```

---

## Start Backend

```bash
pip install -e .

cd backend

uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API Docs:

```text
http://localhost:8000/docs
```

---

## Start Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔌 API Endpoints

## Create Workflow

```http
POST /api/v1/runs
```

## Get Workflow Status

```http
GET /api/v1/runs/{run_id}
```

## List Runs

```http
GET /api/v1/runs
```

## Approval Workflow

```http
POST /api/v1/runs/{run_id}/approval
```

## Live Events

```http
WS /api/v1/ws/runs/{run_id}
```

---

# 🔒 Safety Controls

The platform includes multiple safeguards:

- Maximum iteration limits
- Agent timeout controls
- Budget restrictions
- Human approval gates
- Execution monitoring
- Error handling and recovery

---

# 🚀 Deployment

## Frontend Deployment

Hosted on:

- Vercel

## Backend Deployment

Hosted on:

- Render

---

# 📈 Future Enhancements

### Phase 2

- OpenAI Integration
- Gemini Integration
- PostgreSQL Migration
- Redis Message Queue
- Celery Workers

### Phase 3

- JWT Authentication
- Role-Based Access Control
- Multi-Tenant Support
- Team Collaboration

### Phase 4

- AWS ECS Deployment
- Kubernetes Support
- PDF Report Generation
- Advanced Cost Analytics
- Enterprise Audit Dashboard

---

# 👨‍💻 Author

**Ashish Iqbal**

Computer Science Engineer

GitHub:
https://github.com/Ashishiqbalcse

LinkedIn:
(Add LinkedIn Profile)

---

## ⭐ Support

If you found this project useful, consider giving it a star on GitHub.
