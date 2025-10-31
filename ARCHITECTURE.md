# Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                           │
│  ┌─────────────────┐  ┌──────────────────────────────────────┐  │
│  │ ChatInterface   │  │ AppointmentConfirmation              │  │
│  │ - Message input │  │ - Success modal                      │  │
│  │ - Chat history  │  │ - Appointment details                │  │
│  │ - Real-time UI  │  └──────────────────────────────────────┘  │
│  └────────┬────────┘                                             │
│           │ HTTP/REST API                                        │
└───────────┼─────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Routes                            │   │
│  │  POST /api/chat                                          │   │
│  │  GET  /api/calendly/availability                         │   │
│  │  POST /api/calendly/book                                  │   │
│  │  POST /api/calendly/reschedule                           │   │
│  │  POST /api/calendly/cancel                                │   │
│  │  POST /api/calendly/waitlist                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Scheduling Agent (Orchestrator)              │   │
│  │  - Intent Detection (Scheduling/FAQ/Reschedule/Cancel)  │   │
│  │  - Conversation Management                                │   │
│  │  - Tool Coordination                                      │   │
│  │  - Context Switching                                      │   │
│  └────────┬─────────────────────────────────────────────────┘   │
│           │                                                      │
│    ┌──────┴──────┬────────────┬─────────────┬────────────────┐  │
│    │             │            │             │                │  │
│    ▼             ▼            ▼             ▼                ▼  │
│ ┌──────┐   ┌──────────┐  ┌────────┐  ┌──────────┐  ┌────────┐ │
│ │  RAG │   │  Tools   │  │Calendly│  │   LLM    │  │ Vector │ │
│ │Pipeline│  │          │  │  Mock  │  │ GPT-4-T  │  │  Store │ │
│ └──────┘   └──────────┘  └────────┘  └──────────┘  └────────┘ │
│   │            │            │             │            │       │
│   │            │            │             │            │       │
│   ▼            ▼            ▼             ▼            ▼       │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │                   Data Layer                             │   │
│ │  - clinic_info.json (FAQs)                               │   │
│ │  - doctor_schedule.json (Availability)                   │   │
│ │  - ChromaDB (Vector embeddings)                          │   │
│ │  - In-memory storage (Appointments)                       │   │
│ └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Conversation Flow

```
User Input
    │
    ▼
┌─────────────────┐
│ Intent Detection│
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    │         │          │          │          │
    ▼         ▼          ▼          ▼          ▼
 Scheduling  FAQ   Reschedule  Cancel    Waitlist
    │         │          │          │          │
    │         │          │          │          │
    ▼         ▼          ▼          ▼          ▼
[Extract]  [RAG]    [Find]     [Verify]   [Create]
    │         │          │          │          │
    │         │          │          │          │
    ▼         ▼          ▼          ▼          ▼
[Check]   [Answer]  [Check]    [Cancel]   [Notify]
    │         │          │          │          │
    │         │          │          │          │
    ▼         ▼          ▼          ▼          ▼
[Book]    [Return]  [Resched]  [Confirm] [Waitlist]
    │         │          │          │          │
    └─────────┴──────────┴──────────┴──────────┘
                      │
                      ▼
              Response to User
```

## RAG Pipeline Flow

```
FAQ Query
    │
    ▼
┌─────────────────┐
│ Query Embedding │ (OpenAI text-embedding-3-small)
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Semantic Search │ (ChromaDB - Cosine Similarity)
│  Top 3 Results  │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Format Context  │
│ + History        │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ LLM Generation  │ (GPT-4-Turbo with context)
└────────┬─────────┘
         │
         ▼
    Final Answer
```

## Scheduling Flow

```
Booking Request
    │
    ▼
┌─────────────────┐
│ Extract Info    │ (Date, Time, Doctor, Type, Reason)
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Determine Type  │ (General/Follow-up/Physical/Specialist)
│ & Duration      │ (15/30/45/60 minutes)
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Check Available │ (Filter by duration + buffer)
│  3-5 Slots      │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Present Options │
└────────┬─────────┘
         │
    User Selects
         │
         ▼
┌─────────────────┐
│ Collect Info    │ (Name, Phone, Email, Reason)
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Validate Slot   │ (Check availability)
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Book Appointment│ (Create record, Mark slot)
└────────┬─────────┘
         │
         ▼
    Confirmation
```

## Component Interactions

### Agent → Tools

```
Scheduling Agent
    │
    ├──→ Availability Tool
    │       ├── Load schedule data
    │       ├── Filter by doctor
    │       ├── Match duration
    │       └── Return 3-5 slots
    │
    ├──→ Booking Tool
    │       ├── Validate input
    │       ├── Check availability
    │       ├── Calculate end time
    │       ├── Store appointment
    │       └── Mark slot booked
    │
    ├──→ Reschedule Tool
    │       ├── Find appointment
    │       ├── Validate new time
    │       ├── Free old slot
    │       └── Book new slot
    │
    ├──→ Cancel Tool
    │       ├── Find appointment
    │       ├── Verify email
    │       ├── Free slot
    │       └── Remove appointment
    │
    └──→ Waitlist Tool
            ├── Create entry
            ├── Store preferences
            └── Return waitlist ID
```

### Agent → RAG

```
Scheduling Agent
    │
    └──→ RAG Pipeline
            ├──→ Vector Store
            │       └──→ ChromaDB
            │               └──→ FAQ Embeddings
            │
            ├──→ Embeddings
            │       └──→ OpenAI API
            │
            └──→ FAQ RAG
                    └──→ LLM (GPT-4-Turbo)
                            └──→ Context-Augmented Answer
```

## Data Storage

```
┌─────────────────────────────────────┐
│         Data Storage                │
├─────────────────────────────────────┤
│                                     │
│  Static Files:                      │
│  - clinic_info.json                 │
│    └── FAQs, clinic details         │
│                                     │
│  - doctor_schedule.json              │
│    └── Doctor availability slots    │
│                                     │
│  Vector Database:                   │
│  - ChromaDB (./chroma_db)           │
│    └── FAQ embeddings & metadata   │
│                                     │
│  Runtime Storage (In-Memory):       │
│  - _booked_appointments             │
│    └── Active appointments          │
│                                     │
│  - _waitlist_entries                │
│    └── Waitlist requests            │
│                                     │
└─────────────────────────────────────┘
```

## Error Handling Flow

```
Operation
    │
    ▼
┌─────────────────┐
│   Try Execute   │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
Success    Error
    │         │
    │         ▼
    │   ┌─────────────────┐
    │   │ Categorize Error │
    │   └────────┬─────────┘
    │            │
    │     ┌──────┴──────┬──────────┬──────────┐
    │     │             │          │          │
    │     ▼             ▼          ▼          ▼
    │ Validation  Availability  API      Network
    │ Error       Error        Error    Error
    │     │             │          │          │
    │     └─────────────┴──────────┴──────────┘
    │                    │
    │                    ▼
    │            ┌─────────────────┐
    │            │ Generate Message│
    │            │ + Recovery      │
    │            └────────┬────────┘
    │                     │
    └─────────────────────┘
            │
            ▼
      User Response
```

