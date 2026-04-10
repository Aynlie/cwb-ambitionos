# AmbitionOS Platform Architecture

This diagram illustrates the full data flow of AmbitionOS, from source extraction to human approval and final visualization.

```mermaid
graph TD
    %% Sources
    subgraph Sources [Input Sources]
        Email["📧 Email threads"]
        Syllabus["📄 Academic Syllabus"]
        Notes["📝 Meeting Notes"]
    end

    %% Onboarding Flow
    subgraph Onboarding [Amby Flow]
        Amby["🦄 Amby Onboarding<br/>(Persona Config)"]
        UP["🐘 user_profiles<br/>(tab_config JSONB)"]
    end

    %% Agents & Processing
    subgraph AgentLayer [AI Agent Layer]
        OA["🚀 Onboarding Agent"]
        Claude["🤖 Claude 3.5 Sonnet<br/>(Extraction & Confidence)"]
    end

    %% Storage
    subgraph Storage [Data Storage]
        ATS["☁️ Azure Table Storage<br/>(Source of Truth)"]
        AIS["🔍 Azure AI Search<br/>(Filterable Index)"]
        CDA["🕵️ Change Detection Agent"]
        GPT4["🤖 Azure OpenAI GPT-4o<br/>(Change Summaries)"]
        PG["🐘 PostgreSQL<br/>(Change Log + Tasks)"]
    end

    %% Human-in-the-Loop & Visualization
    subgraph Output [User Interface & Automation]
        FD["🌐 Flask Dashboard<br/>(Persona Tabs UI)"]
        PA["⚡ Power Automate<br/>(Approval Workflow)"]
        PBI["📊 Power BI<br/>(Analytics & Gantt)"]
    end

    %% Connections
    Amby --> UP
    UP --> FD
    Sources --> OA
    OA <--> Claude
    OA --> ATS
    OA --> AIS
    ATS --> CDA
    CDA --> GPT4
    GPT4 --> PG
    PG --> PBI
    AIS --> FD
    PG --> FD
    FD --> PA
    PA --> PG
```

### Component Flow Description:
1.  **Amby Onboarding**: A persona-based AI assistant that configures the user's dashboard tabs (Student, Professional, Career Shifter).
2.  **User Profiles**: Stores tab configurations as JSONB in PostgreSQL.
3.  **Sources**: Unstructured data from student life (emails, syllabi, notes).
4.  **Onboarding Agent**: Uses **Claude 3.5 Sonnet** to extract tasks and assign a confidence score.
5.  **Azure Table Storage**: Acts as the initial source of truth for extracted data.
6.  **Azure AI Search**: Provides fast, filterable search capabilities for the dashboard.
7.  **Change Detection Agent**: Compares new data with existing records, logging changes to **PostgreSQL**.
8.  **Azure OpenAI GPT-4o**: Generates smart summaries for detected task changes.
9.  **PostgreSQL**: Stores the processed tasks and a full audit trail of changes.
10. **Flask Dashboard**: The main UI where users review tasks, see confidence scores, and perform **Human-in-the-Loop** approvals.
11. **Power Automate**: Triggered for high-priority items to send approval emails and sync responses back to PostgreSQL.
12. **Power BI**: Connects directly to PostgreSQL to provide advanced analytics, Gantt charts, and progress tracking.
