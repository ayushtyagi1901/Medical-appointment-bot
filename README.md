# Appointment Scheduling Agent

A conversational AI agent built with FastAPI and React that helps patients schedule appointments and answers frequently asked questions using RAG (Retrieval-Augmented Generation).

## 🎯 Features

- **Conversational Appointment Scheduling**: Natural language interface for booking appointments
- **FAQ Answering**: RAG-based system using ChromaDB for accurate clinic information retrieval
- **Mock Calendly API**: Simulated appointment booking system
- **Seamless Intent Switching**: Automatically detects whether user wants to schedule or ask questions
- **Modern UI**: Beautiful React interface with real-time chat

## 📋 Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React with Vite
- **AI**: Google Gemini 1.5 Flash (default) or Gemini 1.5 Pro
- **Vector Database**: ChromaDB
- **API Integration**: Mock Calendly API

## 📊 Architecture Diagram

See `ARCHITECTURE.md` for detailed architecture diagrams including:
- System architecture overview
- Conversation flow
- RAG pipeline flow
- Scheduling flow
- Component interactions
- Error handling flow

## 📂 Project Structure

```
appointment-scheduling-agent/
├── README.md
├── .env.example
├── requirements.txt
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── agent/
│   │   ├── scheduling_agent.py    # Main conversation agent
│   │   └── prompts.py             # System and user prompts
│   ├── rag/
│   │   ├── faq_rag.py             # RAG pipeline
│   │   ├── embeddings.py          # OpenAI embeddings
│   │   └── vector_store.py        # ChromaDB integration
│   ├── api/
│   │   ├── chat.py                # Chat endpoint
│   │   └── calendly_integration.py # Mock Calendly endpoints
│   ├── tools/
│   │   ├── availability_tool.py    # Slot availability checker
│   │   └── booking_tool.py        # Appointment booking
│   └── models/
│       └── schemas.py             # Pydantic models
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx
│   │   │   └── AppointmentConfirmation.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── clinic_info.json           # FAQ and clinic information
│   └── doctor_schedule.json       # Doctor availability data
└── tests/
    └── test_agent.py              # Test cases
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Node.js 16+ and npm
- OpenAI API key

### Backend Setup

1. **Navigate to project root**:
   ```bash
   cd appointment-scheduling-agent
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   LLM_MODEL=gemini-1.5-flash  # Use gemini-1.5-flash (default) or gemini-1.5-pro
   ```
   
   **Important**: 
   - Get your free Gemini API key from: https://aistudio.google.com/app/apikey
   - **Recommended**: Use `gemini-1.5-flash` (faster, free tier)
   - **For better performance**: Use `gemini-1.5-pro` (more capable, may have usage limits)

5. **Initialize ChromaDB** (automatic on first run):
   The vector store will be initialized automatically when you first run the application.

6. **Run the backend**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   
   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:5173`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
BACKEND_HOST=localhost
BACKEND_PORT=8000
FRONTEND_PORT=5173
CHROMA_DB_PATH=./chroma_db
FAQ_DATA_PATH=./data/clinic_info.json
SCHEDULE_DATA_PATH=./data/doctor_schedule.json
```

### Data Files

- **`data/clinic_info.json`**: Contains FAQ data and clinic information
- **`data/doctor_schedule.json`**: Contains doctor availability schedules

You can modify these files to update FAQs or doctor schedules.

## 📡 API Endpoints

### Chat Endpoint

**POST** `/api/chat`

Main conversational endpoint for interacting with the agent.

**Request Body**:
```json
{
  "message": "I need to book an appointment",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    }
  ]
}
```

**Response**:
```json
{
  "response": "I'd be happy to help you book an appointment...",
  "intent": "scheduling",
  "requires_confirmation": false
}
```

### Availability Endpoint

**GET** `/api/calendly/availability?date=2024-01-15&doctor_name=Dr. Sarah Johnson`

Get available appointment slots for a specific date.

**Response**:
```json
{
  "date": "2024-01-15",
  "slots": [
    {
      "start_time": "2024-01-15T09:00:00",
      "end_time": "2024-01-15T09:30:00",
      "doctor_name": "Dr. Sarah Johnson",
      "available": true
    }
  ]
}
```

### Booking Endpoint

**POST** `/api/calendly/book`

Book an appointment.

**Request Body**:
```json
{
  "patient_name": "John Doe",
  "patient_email": "john@example.com",
  "patient_phone": "+1-555-0100",
  "date": "2024-01-15",
  "start_time": "09:00",
  "doctor_name": "Dr. Sarah Johnson",
  "appointment_type": "general_consultation",
  "reason": "Annual checkup"
}
```

**Response**:
```json
{
  "success": true,
  "appointment_id": "uuid-here",
  "message": "Appointment successfully booked! Your appointment ID is uuid-here.",
  "appointment_details": {
    "appointment_id": "uuid-here",
    "patient_name": "John Doe",
    "patient_email": "john@example.com",
    "patient_phone": "+1-555-0100",
    "doctor_name": "Dr. Sarah Johnson",
    "date": "2024-01-15",
    "start_time": "09:00",
    "end_time": "09:30",
    "appointment_type": "general_consultation",
    "duration_minutes": 30,
    "status": "confirmed"
  }
}
```

### Reschedule Endpoint

**POST** `/api/calendly/reschedule`

Reschedule an existing appointment.

**Request Body**:
```json
{
  "appointment_id": "uuid-here",
  "new_date": "2024-01-16",
  "new_start_time": "14:00"
}
```

**Response**:
```json
{
  "success": true,
  "appointment_id": "uuid-here",
  "message": "Appointment successfully rescheduled to 2024-01-16 at 14:00.",
  "old_appointment": {
    "date": "2024-01-15",
    "start_time": "09:00",
    "end_time": "09:30"
  },
  "new_appointment": {
    "date": "2024-01-16",
    "start_time": "14:00",
    "end_time": "14:30"
  }
}
```

### Cancellation Endpoint

**POST** `/api/calendly/cancel`

Cancel an existing appointment.

**Request Body**:
```json
{
  "appointment_id": "uuid-here",
  "patient_email": "john@example.com"
}
```

**Response**:
```json
{
  "success": true,
  "appointment_id": "uuid-here",
  "message": "Appointment successfully cancelled. Your slot for 2024-01-15 at 09:00 has been released.",
  "cancelled_appointment": {
    ...
  }
}
```

### Waitlist Endpoint

**POST** `/api/calendly/waitlist`

Add a patient to the waitlist.

**Request Body**:
```json
{
  "patient_name": "Jane Doe",
  "patient_email": "jane@example.com",
  "patient_phone": "+1-555-0200",
  "preferred_date": "2024-01-15",
  "appointment_type": "general_consultation",
  "doctor_name": "Dr. Sarah Johnson"
}
```

**Response**:
```json
{
  "success": true,
  "waitlist_id": "uuid-here",
  "message": "You've been added to our waitlist for 2024-01-15. We'll notify you at jane@example.com if a slot becomes available."
}
```

## 🧪 Testing

Run the test suite:

```bash
# Install pytest if not already installed
pip install pytest

# Run tests
pytest tests/test_agent.py -v
```

## 🏗️ System Design

### Architecture Overview

The system follows a clean, modular architecture with clear separation of concerns:

```
┌─────────────────┐
│   React Frontend │  (UI Layer)
│  ChatInterface   │
└────────┬─────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   FastAPI Backend│  (API Layer)
│   /api/chat     │
│   /api/calendly │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Scheduling Agent │  (Orchestration Layer)
│  - Intent Detection
│  - Conversation Management
│  - Tool Coordination
└────────┬─────────┘
         │
    ┌────┴────┬──────────┬──────────────┐
    ▼         ▼          ▼              ▼
┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
│   RAG  │ │Tools │ │ Calendly │ │   LLM    │
│ Pipeline│ │      │ │   Mock   │ │ GPT-4-T  │
└────────┘ └──────┘ └──────────┘ └──────────┘
```

### Agent Conversation Flow

The agent follows a structured conversation flow:

**Phase 1: Understanding Needs**
1. Greet patient warmly
2. Understand reason for visit
3. Determine appointment type:
   - General Consultation (30 min) - routine checkups, symptoms
   - Follow-up (15 min) - follow-up visits, refills
   - Physical Exam (45 min) - comprehensive exams
   - Specialist Consultation (60 min) - complex issues
4. Ask about preferred date/time and doctor preferences

**Phase 2: Slot Recommendation**
1. Check availability using appointment type and duration matching
2. Filter slots based on:
   - Appointment duration requirements
   - Buffer time (15 minutes default)
   - Doctor availability
   - Timezone awareness
3. Present 3-5 best available slots with explanations
4. Handle "none work" gracefully with alternatives

**Phase 3: Booking Confirmation**
1. Collect patient information:
   - Full name
   - Phone number (required for reminders)
   - Email address
   - Reason for visit (optional)
2. Confirm all details before booking
3. Create appointment via mock Calendly API
4. Provide confirmation with appointment ID

**Context Switching**
- FAQ during booking → Answer → Return to booking context
- Scheduling after FAQ → Transition smoothly
- Multiple FAQs → Answer all while maintaining context

### Calendly Integration Approach

**Mock Implementation**
- Simulates real Calendly API behavior
- Stores appointments in-memory (production would use database)
- Endpoints:
  - `GET /api/calendly/availability` - Get available slots
  - `POST /api/calendly/book` - Book appointment
  - `POST /api/calendly/reschedule` - Reschedule appointment
  - `POST /api/calendly/cancel` - Cancel appointment
  - `POST /api/calendly/waitlist` - Add to waitlist

**Real Calendly Integration** (Future)
- Use Calendly API tokens
- Map appointment types to Calendly event types
- Handle webhooks for confirmations
- Sync calendar in real-time

### RAG Pipeline for FAQs

**1. Document Processing**
- Load FAQ data from `clinic_info.json`
- Combine question + answer for better retrieval
- Add clinic information as metadata

**2. Embedding Generation**
- Use OpenAI `text-embedding-3-small` model
- Generate embeddings for each FAQ document
- Store in ChromaDB with metadata

**3. Query Processing**
- User asks FAQ → Generate query embedding
- Semantic search in ChromaDB (cosine similarity)
- Retrieve top 3 most relevant FAQs

**4. Context-Augmented Generation**
- Format retrieved FAQs as context
- Include conversation history
- Generate answer using GPT-4-Turbo with context
- Return natural, conversational response

**5. Knowledge Base Categories**
- Clinic Details (location, hours, parking)
- Insurance & Billing (providers, payment methods)
- Visit Preparation (documents, first visit procedures)
- Policies (cancellation, late arrival, COVID-19)

### Tool Calling Strategy

**Availability Tool**
- Input: date, doctor_name (optional), appointment_type (optional)
- Process:
  1. Load schedule data
  2. Filter by doctor if specified
  3. Match slots to appointment duration + buffer
  4. Validate slots aren't in past
  5. Limit to 3-5 best slots
- Output: List of TimeSlot objects

**Booking Tool**
- Input: patient info, appointment details, appointment_type
- Process:
  1. Validate date/time formats
  2. Check slot availability
  3. Prevent double-booking
  4. Calculate end time based on appointment type duration
  5. Store appointment with all details
  6. Mark slot as booked
- Output: BookingResponse with appointment_id

**Rescheduling Tool**
- Input: appointment_id, new_date, new_start_time
- Process:
  1. Find existing appointment
  2. Validate new date/time
  3. Check new slot availability
  4. Free old slot
  5. Book new slot
  6. Update appointment record
- Output: RescheduleResponse with old/new details

**Cancellation Tool**
- Input: appointment_id, patient_email (verification)
- Process:
  1. Find appointment
  2. Verify email (if provided)
  3. Free up slot
  4. Remove appointment
- Output: CancelResponse with confirmation

**Waitlist Tool**
- Input: patient info, preferred_date, appointment_type
- Process:
  1. Create waitlist entry
  2. Store preferences
  3. Notify when slot becomes available (future: email notification)
- Output: WaitlistResponse with waitlist_id

### Scheduling Logic

**1. Appointment Type Matching**
- Match appointment type to required duration:
  - General Consultation: 30 minutes
  - Follow-up: 15 minutes
  - Physical Exam: 45 minutes
  - Specialist Consultation: 60 minutes
- Only show slots that accommodate duration + buffer

**2. Time Preferences**
- Understand "morning", "afternoon", "evening"
- Filter slots based on time preferences
- Suggest best matching slots

**3. Date Flexibility**
- Handle "ASAP", "next week", "tomorrow"
- Convert relative dates to absolute dates
- Check availability across date ranges

**4. Conflict Prevention**
- No double-booking
- Validate slot availability before booking
- Check conflicts during rescheduling

**5. Buffer Time**
- Default: 15 minutes buffer
- Accounts for travel and preparation
- Ensures adequate time between appointments

**6. Timezone Awareness**
- Configurable via TIMEZONE env variable
- Default: America/New_York
- Handles timezone conversions (future enhancement)

**7. Slot Limiting**
- Return maximum 3-5 slots
- Prioritize earlier times
- Present best available options
- Avoid overwhelming user with choices

### Data Flow

1. **User sends message** → Frontend
2. **Frontend** → POST `/api/chat` with message and history
3. **Agent** → Detects intent (scheduling/FAQ/reschedule/cancel)
4. **If FAQ**:
   - Retrieve relevant FAQs from ChromaDB
   - Generate context-augmented answer
   - Return response
5. **If Scheduling**:
   - Extract booking information
   - Determine appointment type
   - Check availability (3-5 slots)
   - Present options
   - Collect patient info (name, phone, email)
   - Book appointment
   - Confirm with appointment ID
6. **If Rescheduling**:
   - Find appointment
   - Check new slot availability
   - Reschedule and confirm
7. **If Cancellation**:
   - Verify appointment
   - Cancel and free slot
   - Confirm cancellation
8. **Response** → Frontend → Display to user

### Error Handling

**Validation Errors**:
- Invalid date/time formats → Clear error message
- Past dates → Suggest future dates
- Outside business hours → Suggest available times

**Availability Errors**:
- No slots available → Offer waitlist or alternatives
- Slot conflict → Suggest other times
- Double-booking → Prevent and suggest alternatives

**Missing Information**:
- Missing patient info → Ask specifically what's needed
- Missing appointment ID → Request ID
- Missing email for cancellation → Request verification

**API Errors**:
- OpenAI API errors → Graceful degradation with fallback message
- ChromaDB errors → Retry or use cached data
- Network timeouts → User-friendly error message

All errors are gracefully handled with user-friendly messages and recovery suggestions.

## 💡 Usage Examples

### Booking an Appointment

```
User: "I need to see a doctor next week"
Agent: "I'd be happy to help you book an appointment. What day works best for you?"
User: "How about January 15th?"
Agent: [Shows available slots]
User: "9:00 AM with Dr. Sarah Johnson works for me"
Agent: "Great! I'll need your name and email to complete the booking."
User: "John Doe, john@example.com"
Agent: "Perfect! Your appointment has been booked..."
```

### Asking Questions

```
User: "What are your operating hours?"
Agent: [Retrieves from FAQ] "We are open Monday through Friday from 9:00 AM to 5:00 PM..."

User: "Do you accept insurance?"
Agent: [Retrieves from FAQ] "Yes, we accept most major insurance plans..."
```

## 🔒 Security Considerations

- API keys stored in environment variables (never commit to git)
- Input validation using Pydantic schemas
- CORS configuration for frontend
- Error messages don't expose internal details

## 🚧 Limitations & Future Improvements

- Current implementation uses in-memory storage for bookings (should use a database)
- Schedule data is static JSON (should integrate with real calendar API)
- No authentication/authorization (add user accounts)
- No email notifications (integrate email service)
- Limited error recovery (add retry logic)
- No multi-language support (add internationalization)

## 📝 License

This project is built for assessment purposes.

## 👥 Contributing

This is an assessment project. For production use, consider:
- Adding proper database integration
- Implementing authentication
- Adding comprehensive error logging
- Setting up CI/CD pipelines
- Adding more comprehensive tests

## 🆘 Troubleshooting

### Backend won't start
- Check that Python 3.10+ is installed
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Ensure OpenAI API key is set in `.env`

### Frontend won't connect to backend
- Verify backend is running on port 8000
- Check CORS configuration in `backend/main.py`
- Verify API_BASE_URL in frontend (defaults to `http://localhost:8000`)

### ChromaDB errors
- Delete `./chroma_db` directory and restart (will reinitialize)
- Check file permissions in project directory

### OpenAI API errors
- Verify API key is correct and has credits
- Check API rate limits
- Verify internet connection

## 📞 Support

For issues or questions, please refer to the API documentation at `http://localhost:8000/docs` when the backend is running.

