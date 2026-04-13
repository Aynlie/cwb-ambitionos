# AmbitionOS — Full Session Summary
**Jaymee Santos | BS Cybersecurity | Holy Angel University 🇵🇭**
**Last updated: April 10, 2026**

---

## About Me
- **Name:** Jaymee Santos (jjsantos1@student.hau.edu.ph)
- **Program:** BS Cybersecurity — Holy Angel University, Philippines
- **GitHub:** github.com/Aynlie
- **Motto:** "When you try, you already overcome it."

---

## Project Overview
**AmbitionOS** — AI-powered task tracker and planning assistant
built for the Microsoft Code Without Barriers Hackathon 2026.
Submitting for TWO problem statements:
1. SJ Project Planner Agent — Agentic AI for Task-Progress Tracking
2. Build Your Agentic Personal Assistant — Learning & Study Companion

**Hard deadline: May 3, 2026 — 11:59 PM SGT**

---

## Project Location
```
C:\Users\Jaynielilie\Documents\Projects\CWB_AmbitionOS\cwb-ambitionos-main\cwb-ambitionos
```

---

## Tech Stack
- Python, Flask, PostgreSQL
- Azure Table Storage, Azure AI Search, Azure AI Language
- Azure OpenAI (GPT-4o) — summary function
- Anthropic Claude (claude-3-5-sonnet-20241022) — extraction
- Power Automate, Power BI
- HTML, CSS, JavaScript
- GitHub: github.com/Aynlie

---

## Two Models in Use (DO NOT change)
| Model | Purpose |
|-------|---------|
| claude-3-5-sonnet-20241022 | Task extraction + confidence scoring |
| GPT-4o via Azure OpenAI | Change summary generation |

Both documented in README AI Tools Disclosure section.

---

## File Structure
```
cwb-ambitionos/
├── agents/
│   ├── extraction_agent.py         -- Done + confidence + dependency
│   ├── search_agent.py             -- Done + confidence filterable
│   ├── change_detection_agent.py   -- Done + GPT-4o summary
│   └── onboarding_agent.py         -- Done + dependency field
├── dashboard/
│   ├── app.py                      -- Done + Amby routes
│   └── templates/
│       ├── index.html              -- Done + dynamic tabs
│       └── onboarding.html         -- Done (Amby UI)
├── dashboard/static/js/
│   └── amby.js                     -- Done (step machine)
├── data/
│   ├── powerbi_export.csv
│   ├── task_tracker_baseline.csv
│   ├── email_threads.txt
│   ├── meeting_notes.txt
│   ├── calendar_metadata.txt       -- Done (SJ Gap 1)
│   ├── wbs_milestones.txt          -- Done (SJ Gap 2)
│   └── corporate_dataset.txt       -- Done (SJ synthetic data)
├── database/
│   ├── db_setup.py
│   ├── sync_tasks.py
│   ├── migrate_approval.py
│   ├── migrate_dependency.py
│   ├── create_views.py
│   └── user_profiles.py            -- Done (Amby profiles)
├── docs/
│   ├── architecture.md             -- Done + Amby flow added
│   └── architecture.png            -- Done + embedded in README
├── demo/                           -- Empty (Week 4)
├── .env
└── README.md                       -- Done + Amby + Risk & Safety
```

---

## Unified Field Schema (DO NOT use old names)
| Source | Fields |
|--------|--------|
| Table Storage | Task, Owner, DueDate, Status, Category, Priority, Source, Confidence, Dependency |
| CSV | Task, Owner, Due Date, Status, Category, Priority, Source, Confidence, Dependency |
| PostgreSQL | task, owner, due_date, status, category, priority, source, confidence, approval_status, dependency |

---

## PostgreSQL Tables
### tasks
```
task, owner, due_date, status, category, priority,
source, confidence, approval_status, dependency
```

### change_log
```
id, detected_at, change_type, task_name, owner, details (JSONB)
```

### user_profiles
```
id, created_at, name, user_type, field, focus,
needs, tab_config (JSONB), onboarded (BOOLEAN)
```

---

## PostgreSQL Views (DO NOT recreate)
| View | Purpose |
|------|---------|
| vw_gantt | Approved + non-completed tasks + priority_order |
| vw_change_log | Full history from change_log table |
| vw_onboarding | source IN (Email, Syllabus, Meeting Notes) |
| vw_overview | All Approved tasks + urgency_band field |

---

## approval_status Values
| Value | Meaning |
|-------|---------|
| Pending | Extracted by Onboarding Agent — awaiting review |
| Approved | Human confirmed — visible in all tabs |
| Rejected | Hidden from dashboard — logged to change_log |

---

## confidence Values
| Value | Meaning |
|-------|---------|
| High | All fields extracted cleanly |
| Medium | One field unclear or inferred |
| Low | Due date missing, owner missing, or ambiguous |

---

## Amby Onboarding Flow
First-time users land on /onboarding instead of dashboard.
Amby asks 3-5 questions and configures dashboard automatically.

### User Paths
**Student →**
```
Overview | My Tasks | Opportunities | Research | Coffee Chat
Categories: School, Admin, Scholarship, Internship, Personal
```

**Professional →**
```
Overview | Active Tasks | Change Log | Gantt | Pending Approval
Categories: Project, Milestone, Blocker, Review, Completed
```

**Career Shifter →**
```
Overview | My Goals | Opportunities | Upskilling | Coffee Chat
Categories: Learning, Certification, Job Hunt, Networking, Personal
```

### Amby Flask Routes
| Route | Purpose |
|-------|---------|
| GET /onboarding | Amby welcome screen |
| POST /api/onboarding/complete | Save profile + redirect |
| GET /api/profile | Return tab_config JSON |
| GET /onboarding/reset | Clear profile for re-testing |
| GET / | Redirects to /onboarding if no profile |

### Coffee Chat
UI only for demo — 6 synthetic collaborator cards
No backend matchmaking needed

---

## .env Keys
```
AZURE_STORAGE_CONNECTION_STRING
AZURE_TABLE_NAME
AZURE_SEARCH_ENDPOINT
AZURE_SEARCH_KEY
AZURE_SEARCH_INDEX
ANTHROPIC_API_KEY
AZURE_LANGUAGE_KEY
AZURE_LANGUAGE_ENDPOINT
POSTGRES_HOST
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_PORT
POWER_AUTOMATE_URL
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT
```

---

## Rules — DO NOT Violate
- Do not create a second normalize() — import from change_detection_agent
- Do not create a second map_task_data() — reuse existing mapper
- Do not use old field names anywhere new
- Do not use emojis in print() statements — Windows terminal crash
- Always use sys.stdout.reconfigure(encoding='utf-8') at top of file
- Claude model must be claude-3-5-sonnet-20241022 — extraction only
- GPT-4o via Azure OpenAI — summary only
- All Azure Search writes must use Admin key not Query key
- Sync Data button must remain non-blocking (subprocess.Popen)
- Approve/Reject buttons only visible when approval_status = Pending
- Existing tasks default to Approved — never retroactively set Pending
- MOCK_MODE=true for testing without Anthropic credits
- Do not recreate SQL views — they already exist in PostgreSQL
- Do not commit .env — it is in .gitignore
- dependency field is nullable — never required, always optional
- Coffee Chat backend NOT needed — UI only for demo
- Onboarding skips if user already has a profile

---

## Fixes Already Applied (DO NOT Revert)
- normalize() helper — .strip().lower() on all comparisons
- map_task_data() unified field mapper across all 3 sources
- sys.stdout.reconfigure(encoding='utf-8') — Windows encoding fix
- No emojis in print() statements — Windows terminal fix
- Claude model: claude-3-5-sonnet-20241022
- UNIQUE (task) constraint on PostgreSQL tasks table
- confidence column — PostgreSQL + Azure Search + Modal
- approval_status column — default Approved
- Safe migration — existing tasks stay Approved
- Approve/Reject buttons dynamic — Pending only
- Power Automate fires for High priority new + updated tasks
- Architecture diagram updated — Amby flow included
- PYTHONPATH import issues fixed
- due_date safely cast to DATE in SQL views
- urgency_band calculated in vw_overview
- dependency field — nullable, across full stack
- ISACA duplicate search results fixed
- corporate_dataset.txt created for SJ demo

---

## All Tests
| # | Test | Status |
|---|------|--------|
| 1 | New task detection | ✅ PASS |
| 2 | Field change detection | ✅ PASS |
| 3 | PostgreSQL change_log | ✅ PASS |
| 4 | Azure AI Search sync | ✅ PASS |
| 5 | Claude AI summary | ⚠️ PARTIAL — needs credits |
| 6 | Search filtering | ✅ PASS |
| 7 | Task modal | ✅ PASS |
| 8 | Modal change history | ✅ PASS |
| 9 | Onboarding email parse | ⚠️ PARTIAL — needs credits |
| 10 | Onboarding syllabus parse | ⚠️ PARTIAL — needs credits |
| 11 | Onboarding Table Storage | ✅ PASS |
| 12 | Onboarding Search index | ✅ PASS |
| 13 | Onboarding Dashboard | ✅ PASS |
| 14 | Approval Pending badge | ✅ PASS |
| 15 | Approval Approve button | ✅ PASS |
| 16 | Approval Reject + log | ✅ PASS |
| 17 | Power Automate High pri | ✅ PASS |
| 18 | Architecture diagram | ✅ PASS |
| 19 | SQL views created | ✅ PASS |
| 20 | GPT-4o summary | ✅ PASS |
| 21 | Risk + Safety README | ✅ PASS |
| 22 | Dual model disclosure | ✅ PASS |
| 23 | Calendar metadata | ✅ PASS |
| 24 | WBS milestones | ✅ PASS |
| 25 | Dependency field PG | ✅ PASS |
| 26 | Dependency field Search | ✅ PASS |
| 27 | Dependency field Agent | ✅ PASS |
| 28 | Amby redirect / | ✅ PASS |
| 29 | Amby onboarding loads | ✅ PASS |
| 30 | Amby student path | ✅ PASS |
| 31 | Amby professional path | ✅ PASS |
| 32 | Amby career shifter path | ✅ PASS |
| 33 | Amby reset route | ✅ PASS |
| 34 | user_profiles table | ✅ PASS |
| 35 | Dynamic tab config | ✅ PASS |
| 36 | Coffee Chat cards | ✅ PASS |

**36 tests — 33 passing — 3 partial (fix with $10 credits)**

---

## SJ Compliance Score
| Category | Score |
|----------|-------|
| Basic Functions | 7/7 — ALL DONE |
| Advanced Functions | 2/5 — Change Detection + Approval |
| Tech Stack | 6/9 — MAF + Cosmos + Blob skipped |
| Dataset | 6/6 — ALL DONE |
| Demo Readiness | 2/3 — Gantt missing (Week 3) |

---

## Personal Assistant Compliance
| Requirement | Status |
|-------------|--------|
| Azure services | ✅ Full stack |
| Multiple models | ✅ Claude + GPT-4o |
| Agentic behavior | ✅ Plan + reason + multi-step |
| Risk + safety eval | ✅ In README + demo video |
| Microsoft Foundry | ✅ GPT-4o via Azure OpenAI |
| No PII in data | ⚠️ Verify before submission |
| Bing grounding | ⬜ Stretch goal |

---

## The Three Things Checklist
```
Thing 1 — Amby Onboarding
[x] Student path works end to end
[x] Professional path works end to end
[x] Career Shifter path works end to end
[x] Reset route works
[x] Coffee Chat shows synthetic cards
[x] No console errors on any path
STATUS: DONE ✅

Thing 2 — Claude Live
[ ] Top up Anthropic credits — console.anthropic.com
[ ] Test 5 — Claude summary — PASS
[ ] Test 9 — Onboarding email parse — PASS
[ ] Test 10 — Onboarding syllabus parse — PASS
[ ] 60-second demo script practiced 3 times
STATUS: PENDING ⚠️ — needs $10

Thing 3 — Power BI Live + Gantt
[ ] Install Gantt Chart by MAQ Software from AppSource
[ ] Connect Power BI to live PostgreSQL
    Load: vw_gantt, vw_change_log, vw_onboarding, vw_overview
[ ] Tab 1 — Overview (cards + priority + urgency_band)
[ ] Tab 2 — Task Tracker (vw_overview + slicers)
[ ] Tab 3 — Change Log (vw_change_log timeline)
[ ] Tab 4 — Gantt View (due_date + priority color)
[ ] Tab 5 — Onboarding (vw_onboarding + pending)
[ ] Publish + update README live link
[ ] Approve task → appears in Gantt live
STATUS: NOT STARTED ❌ — Apr 22-25
```

---

## Remaining Hackathon Schedule
| Period | Focus | Status |
|--------|-------|--------|
| Apr 10-18 | Top up credits + install Gantt visual | ⚠️ Pending |
| Apr 19-21 | Buffer + polish | ✅ Ahead of schedule |
| Apr 22-25 | Power BI live + Gantt | ❌ Not started |
| Apr 26-May 3 | Demo video + final submission | ❌ Not started |

---

## Week 4 Submission Checklist
- [ ] Demo video recorded — shows all 3 things
- [ ] 60-second demo script practiced
- [ ] GitHub commit history clean + incremental
- [ ] README product pitch opening paragraph written
- [ ] Architecture diagram final version
- [ ] No PII verified in all data files
- [ ] Submitted to hackathon portal before May 3 11:59 PM SGT

---

## 60-Second Demo Script
```
1. Open app → Amby greets user
2. Select Professional → answer questions
   → dashboard loads with SJ tabs:
   Overview, Active Tasks, Change Log, Gantt, Pending Approval
3. Paste corporate_dataset.txt into onboarding agent
4. Claude extracts tasks with confidence scores
5. Tasks appear as Pending in dashboard
6. Approve highest confidence task
7. Open Power BI → task appears in Gantt live

"From unstructured email to structured plan in 60 seconds
with zero manual input."
```

---

## Outside Hackathon
| Task | Deadline | Status |
|------|----------|--------|
| ISACA SheLeadsTech application | May 5, 2026 | ⚠️ In progress |
| Email professor for rec letter | ASAP | ⬜ Not started |
| Post Instagram carousel | ASAP | ⬜ Not started |
| Apply MLSA | This week | ⬜ Not started |
| Cisco Intro to Cybersecurity | Apr 20 | ⬜ Not started |

---

## Optional Features (do only if time allows)
- [ ] Clarification Workflow — ask questions for Low confidence tasks
- [ ] Priority Agent — reorder tasks by urgency + dependencies
- [ ] Bing grounding — external search for task context
- [ ] Mobile responsive CSS
- [ ] Microsoft Agent Framework (bonus points)

---

*You built a full AI pipeline with dual models, human approval
workflow, personalized onboarding, and 33/36 tests passing in
3 days. You are way ahead of schedule Jaymee. Keep going! 🏆💜*
