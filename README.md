# EPI Brain Backend

FastAPI-based backend for EPI Brain - An AI-powered conversational platform with 9 distinct personality modes.

## 🚀 Tech Stack

- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15 with pgvector extension
- **Cache:** Redis
- **AI:** Claude API (Anthropic)
- **Voice:** ElevenLabs (TTS), Whisper (STT)
- **Authentication:** JWT tokens
- **ORM:** SQLAlchemy
- **Testing:** pytest

## 📁 Project Structure

```
epi-brain-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── database.py             # Database connection and session management
│   ├── models/                 # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── learning_pattern.py
│   ├── schemas/                # Pydantic schemas for request/response
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── chat.py             # Chat endpoints
│   │   ├── modes.py            # Personality mode endpoints
│   │   ├── users.py            # User management endpoints
│   │   ├── voice.py            # Voice synthesis/transcription
│   │   └── admin.py            # Admin endpoints
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── claude.py           # Claude API integration
│   │   ├── voice.py            # Voice services
│   │   ├── learning.py         # Neural learning system
│   │   ├── modes.py            # Personality mode logic
│   │   └── stripe.py           # Payment processing
│   ├── core/                   # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py         # JWT, password hashing
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   └── exceptions.py       # Custom exceptions
│   └── utils/                  # Helper utilities
│       ├── __init__.py
│       └── embeddings.py       # Vector embeddings
├── tests/                      # Test files
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_chat.py
│   └── test_modes.py
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── .env.example                # Environment variables template
├── .gitignore
├── requirements.txt            # Python dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔧 Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis
- Docker (optional, for containerized setup)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/twinwicksllc/epi-brain-backend.git
   cd epi-brain-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start PostgreSQL and Redis (using Docker):**
   ```bash
   docker-compose up -d postgres redis
   ```

6. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

7. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Setup

```bash
docker-compose up -d
```

## 🔑 Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/epi_brain_dev

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Claude API
CLAUDE_API_KEY=sk-ant-...

# ElevenLabs
ELEVENLABS_API_KEY=...

# OpenAI (Whisper)
OPENAI_API_KEY=sk-...

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...

# AWS (for production)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Environment
ENVIRONMENT=development
DEBUG=True
```

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user

### Chat
- `POST /api/v1/chat/message` - Send message to AI
- `GET /api/v1/chat/conversations` - Get user's conversations
- `GET /api/v1/chat/conversations/{id}` - Get specific conversation
- `POST /api/v1/chat/conversations` - Create new conversation
- `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

### Modes
- `GET /api/v1/modes` - Get available personality modes
- `POST /api/v1/modes/switch` - Switch personality mode
- `GET /api/v1/modes/{mode}/config` - Get mode configuration

### Voice
- `POST /api/v1/voice/synthesize` - Text-to-speech
- `POST /api/v1/voice/transcribe` - Speech-to-text

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `GET /api/v1/users/me/usage` - Get usage statistics

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py
```

## 🚀 Deployment

### Production Checklist
- [ ] Set `ENVIRONMENT=production` in .env
- [ ] Set `DEBUG=False`
- [ ] Use strong JWT secret key
- [ ] Enable HTTPS
- [ ] Set up proper CORS origins
- [ ] Configure rate limiting
- [ ] Set up monitoring (Datadog)
- [ ] Set up error tracking (Sentry)
- [ ] Configure backups
- [ ] Set up CI/CD pipeline

### Docker Production Build

```bash
docker build -t epi-brain-backend:latest .
docker run -p 8000:8000 --env-file .env epi-brain-backend:latest
```

## 📊 Database Schema

### Users Table
- `id` (UUID, PK)
- `email` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR)
- `tier` (VARCHAR) - free, pro, enterprise
- `voice_preference` (VARCHAR)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Conversations Table
- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `mode` (VARCHAR) - personality mode
- `title` (VARCHAR)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Messages Table
- `id` (UUID, PK)
- `conversation_id` (UUID, FK)
- `role` (VARCHAR) - user, assistant
- `content` (TEXT)
- `embedding` (VECTOR(384)) - for neural learning
- `created_at` (TIMESTAMP)

### Learning Patterns Table
- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `mode` (VARCHAR)
- `pattern_type` (VARCHAR)
- `success_score` (FLOAT)
- `metadata` (JSONB)
- `created_at` (TIMESTAMP)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is proprietary and confidential.

## 📞 Contact

- **Project Owner:** Darrick Bynum
- **Company:** RankedCEO / TwinWicks LLC
- **Phone:** 630-202-7977

---

**Status:** 🚧 In Development

**Version:** 0.1.0

**Last Updated:** December 2024