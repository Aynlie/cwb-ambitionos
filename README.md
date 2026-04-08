# 🚀 AmbitionOS — AI-Powered Personal Planner
> Microsoft Code Without Barriers Hackathon 2026

An agentic AI personal dashboard and project planner built with Microsoft Azure services.


📊 **Live Power BI Dashboard:** [View Dashboard](https://app.powerbi.com/groups/me/reports/d36551b2-29f7-42fb-9c8e-bead676b10a2/b91788b4030f6e70bb6b?experience=power-bi)

---

## 🏗️ Architecture
```
[Meeting Notes / Emails / CSV]
        ↓
[Azure Blob Storage]
        ↓
[Extraction Agent] ──── Azure AI Language
        ↓
[Azure Table Storage] ←→ [PostgreSQL Tasks Table]
        ↓
[Change Detection Agent]
        ↓
[Power Automate Approval Flow]
        ↓
[Flask Dashboard] ←── Azure AI Search
        ↓
[Power BI Dashboard]
```

---

## ☁️ Azure Resources
| Resource | Name | Type | Location |
|---|---|---|---|
| Resource Group | `cwbAmbitionosRg` | Resource Group | Southeast Asia |
| Storage Account | `cwbambitionosstorage` | Storage V2 | East Asia |
| Table Storage | `ambitionosdata` | Azure Table | East Asia |
| AI Search | `cwb-ambitionos-search` | Search Service | East Asia |
| PostgreSQL | `cwb-ambitionos-db` | PostgreSQL Flexible | East Asia |
| AI Language | `cwb-ambitionos-language` | Cognitive Services | East Asia |

---

## 🛠️ Tech Stack
- **Python Flask** — Web framework
- **Azure Blob Storage** — File storage for meeting notes, emails, CSV
- **Azure Table Storage** — NoSQL task storage
- **Azure AI Language** — Text extraction and entity recognition
- **Azure AI Search** — Full-text search on tasks
- **Azure Database for PostgreSQL** — Relational task and change log storage
- **Power Automate** — Human-in-the-loop approval workflow
- **Power BI** — Visual analytics dashboard
- **GitHub** — Version control

---

## 📁 Project Structure
```
cwb-ambitionos/
├── .env                          # Azure credentials (never commit!)
├── .gitignore                    # Excludes .env and venv
├── requirements.txt              # Python dependencies
├── test_connection.py            # Azure connection test
├── upload_to_blob.py             # Upload data files to Blob Storage
├── export_for_powerbi.py         # Export tasks to CSV for Power BI
├── test_power_automate.py        # Test Power Automate flow
│
├── data/
│   ├── meeting_notes.txt         # Sample meeting notes
│   ├── email_threads.txt         # Sample email threads
│   ├── task_tracker_baseline.csv # Master task list (9 tasks)
│   └── powerbi_export.csv        # Exported tasks for Power BI
│
├── agents/
│   └── extraction_agent.py       # Extracts tasks → Azure Table Storage
│
├── database/
│   ├── db_setup.py               # Creates PostgreSQL tables
│   └── sync_tasks.py             # Syncs Table Storage → PostgreSQL
│
├── dashboard/
│   ├── app.py                    # Flask web app
│   └── templates/
│       └── index.html            # 5-tab dashboard UI
│
└── architecture/
    └── architecture_diagram.png  # System architecture diagram
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.11+
- Git
- Azure for Students subscription
- VS Code

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/cwb-ambitionos.git
cd cwb-ambitionos
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

### 3. Install Dependencies
```bash
pip install flask azure-data-tables azure-storage-blob azure-ai-textanalytics psycopg2-binary sqlalchemy python-dotenv requests
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=cwbambitionosstorage;AccountKey=...
AZURE_TABLE_NAME=ambitionosdata

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://cwb-ambitionos-search.search.windows.net
AZURE_SEARCH_KEY=your_search_key
AZURE_SEARCH_INDEX=ambitionos-index

# Azure AI Language
AZURE_LANGUAGE_KEY=your_language_key
AZURE_LANGUAGE_ENDPOINT=https://cwb-ambitionos-language.cognitiveservices.azure.com/

# PostgreSQL
POSTGRES_HOST=cwb-ambitionos-db.postgres.database.azure.com
POSTGRES_DB=postgres
POSTGRES_USER=ambitionosadmin
POSTGRES_PASSWORD=your_password
POSTGRES_PORT=5432

# Power Automate
POWER_AUTOMATE_URL=your_power_automate_url
```

### 5. Test Azure Connection
```bash
python test_connection.py
```

### 6. Upload Data Files
```bash
python upload_to_blob.py
```

### 7. Set Up Database
```bash
python database/db_setup.py
python database/sync_tasks.py
```

### 8. Run Extraction Agent
```bash
python agents/extraction_agent.py
```

### 9. Run Dashboard
```bash
cd dashboard
python app.py
```
Open 👉 http://127.0.0.1:5000

---

## 🤖 Agents

### Extraction Agent (`agents/extraction_agent.py`)
- Loads 9 structured tasks from `task_tracker_baseline.csv`
- Extracts additional tasks from `meeting_notes.txt` using Azure AI Language
- Saves all tasks to Azure Table Storage and syncs to PostgreSQL

### Change Detection Agent
- Compares old vs new task data
- Detects: new tasks, updated deadlines, status changes, priority changes
- Logs every change to PostgreSQL `change_logs` table
- Triggers Power Automate approval flow on detected changes

---

## 🔄 Power Automate Flow
```
HTTP Trigger (task change detected)
        ↓
Start and wait for approval (assigned to Jaymee Santos)
        ↓
    Condition: Outcome == "Approve"
   ↙                              ↘
True (Approved)              False (Rejected)
Send approval email          Send rejection email
```

---

## 📊 Dashboard Features
- **Dashboard tab** — Today's priorities, stats, change log, search bar
- **Opportunities tab** — Internships, Scholarships, Ambassador programs
- **School tab** — Certifications, deadlines
- **Grow tab** — GitHub streak, skills, learning
- **Me tab** — Profile, goals, preferences

---

## 🗄️ PostgreSQL Schema
```sql
-- Tasks table
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    task VARCHAR(255),
    owner VARCHAR(100),
    due_date VARCHAR(100),
    status VARCHAR(50),
    category VARCHAR(100),
    priority VARCHAR(50),
    source VARCHAR(100),
    extracted_at TIMESTAMP DEFAULT NOW()
);

-- Change logs table
CREATE TABLE change_logs (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(255),
    field_changed VARCHAR(100),
    old_value VARCHAR(255),
    new_value VARCHAR(255),
    changed_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🛡️ Risk & Safety Evaluation
| Risk | Mitigation |
|---|---|
| PII exposure | Synthetic/masked data only used |
| API keys exposed | Stored in `.env`, excluded via `.gitignore` |
| Prompt injection | Input validation on all text fields |
| Hallucination | Structured CSV used as primary data source |
| Unauthorized flow trigger | Power Automate URL stored securely in `.env` |

---

## 🤝 AI Tools Disclosure
The following AI tools were used in development:
- **Claude (Anthropic)** — Development guidance and code assistance
- **GitHub Copilot** — Code completion

All AI-generated code has been reviewed and tested by the developer.

---

## 📅 Development Timeline
| Date | Milestone |
|---|---|
| Apr 6 | Repo setup + dataset files created |
| Apr 7 | Azure services configured |
| Apr 8 | Extraction agent + Flask dashboard live |
| Apr 8 | PostgreSQL connected + Power Automate flow working |
| Apr 8 | Power BI dashboard published live ✅ |
| Apr 9–11 | Azure AI Search setup |
| Apr 12–18 | Core agents + onboarding agent |
| Apr 19–25 | Dashboard polish + presentation |
| Apr 26–May 3 | Demo video + final submission |

---

## 👩‍💻 Developer
**Jaymee Santos**
Holy Angel University
jjsantos1@student.hau.edu.ph

---

## 📝 Prior Work Disclosure
The **SecondBrain** concept inspired the AmbitionOS personal dashboard idea. All code, agents, and Azure integrations were built fresh during the hackathon period (April 2–May 3, 2026).

---

*Built with 💜 for Microsoft Code Without Barriers Hackathon 2026*
