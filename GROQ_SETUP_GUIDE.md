# 🚀 Groq API Setup Guide

## What is Groq?

Groq provides **FREE** access to powerful open-source LLMs (like Llama 3.1) with the **fastest inference speed** in the world. Perfect for MVP development!

## ✨ Benefits

- ✅ **100% FREE** - No credit card required
- ✅ **Ultra-fast** - ~500 tokens/second (10x faster than Claude)
- ✅ **Generous limits** - 14,400 requests/day on free tier
- ✅ **High quality** - Llama 3.1 70B is excellent
- ✅ **Easy to switch** - Can move to Claude later with one config change

---

## 📝 Step-by-Step Setup

### Step 1: Get Your Free Groq API Key

1. **Go to Groq Console:**
   - Visit: https://console.groq.com

2. **Sign Up (FREE):**
   - Click "Sign Up" or "Get Started"
   - Sign up with Google, GitHub, or email
   - No credit card required!

3. **Create API Key:**
   - Once logged in, go to "API Keys" section
   - Click "Create API Key"
   - Give it a name (e.g., "EPI Brain MVP")
   - Copy the API key (starts with `gsk_...`)
   - **IMPORTANT:** Save it somewhere safe - you can't see it again!

### Step 2: Add API Key to Your Project

1. **Navigate to backend directory:**
   ```bash
   cd epi-brain-backend
   ```

2. **Create .env file from template:**
   ```bash
   cp .env.example .env
   ```

3. **Edit .env file:**
   ```bash
   # Open in your favorite editor
   nano .env
   # or
   vim .env
   # or
   code .env
   ```

4. **Add your Groq API key:**
   ```env
   # AI Provider Selection
   USE_GROQ=true
   
   # Groq API (FREE for MVP)
   GROQ_API_KEY=gsk_YOUR_ACTUAL_API_KEY_HERE
   GROQ_MODEL=llama-3.1-70b-versatile
   
   # You can leave Claude keys empty for now
   CLAUDE_API_KEY=
   ```

5. **Configure Database URLs:**
   ```env
   # For local development with Docker
   DATABASE_URL=postgresql://epi_user:epi_password@localhost:5432/epi_brain_dev
   REDIS_URL=redis://localhost:6379
   
   # JWT Secret (generate a random string)
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
   ```

### Step 3: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (includes Groq SDK)
pip install -r requirements.txt
```

### Step 4: Start the Backend

**Option A: Using Docker (Recommended)**
```bash
# Start PostgreSQL, Redis, and Backend
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

**Option B: Local Development**
```bash
# Start PostgreSQL and Redis with Docker
docker-compose up -d postgres redis

# Run backend locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Test the API

1. **Open your browser:**
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

2. **Test Registration:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword123",
       "voice_preference": "none"
     }'
   ```

3. **Test Login:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword123"
     }'
   ```

4. **Test Chat (with your access token):**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/chat/message" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -d '{
       "message": "Hello! How are you today?",
       "mode": "personal_friend"
     }'
   ```

---

## 🎯 Available Models

You can choose different Groq models in your `.env` file:

### Llama 3.3 70B Versatile (Recommended)
```env
GROQ_MODEL=llama-3.3-70b-versatile
```
- **Best for:** Production-quality responses
- **Speed:** Fast (~300 tokens/sec)
- **Quality:** Excellent (comparable to GPT-4)
- **Note:** Latest and most capable model

### Llama 3.1 8B Instant (Fastest)
```env
GROQ_MODEL=llama-3.1-8b-instant
```
- **Best for:** Ultra-fast responses
- **Speed:** Very fast (~500 tokens/sec)
- **Quality:** Good (great for simple modes)

### Mixtral 8x7B
```env
GROQ_MODEL=mixtral-8x7b-32768
```
- **Best for:** Long context (32K tokens)
- **Speed:** Fast
- **Quality:** Very good

---

## 🔄 Switching Between Groq and Claude

### Use Groq (FREE - for MVP):
```env
USE_GROQ=true
GROQ_API_KEY=gsk_your_key_here
```

### Switch to Claude (when ready for production):
```env
USE_GROQ=false
CLAUDE_API_KEY=sk-ant-your_key_here
```

**That's it!** No code changes needed - just flip the flag!

---

## 📊 Rate Limits (Free Tier)

| Limit Type | Free Tier |
|------------|-----------|
| Requests per minute | 30 |
| Requests per day | 14,400 |
| Tokens per minute | 6,000 |

**Perfect for MVP!** This allows:
- ~480 conversations per day
- ~20,000 messages per month
- More than enough for initial testing

---

## 🐛 Troubleshooting

### Error: "Invalid API Key"
- Make sure your API key starts with `gsk_`
- Check for extra spaces in `.env` file
- Regenerate key if needed at console.groq.com

### Error: "Rate limit exceeded"
- Free tier: 30 requests/minute
- Wait a minute and try again
- Consider upgrading if needed (still very cheap)

### Error: "Connection refused"
- Make sure Docker containers are running: `docker-compose ps`
- Check if ports are available: `lsof -i :8000`
- Restart services: `docker-compose restart`

### Error: "Database connection failed"
- Make sure PostgreSQL is running: `docker-compose up -d postgres`
- Check DATABASE_URL in `.env`
- Wait for database to be ready (check health)

---

## 💡 Tips for Best Results

### 1. Choose the Right Model
- **Development/Testing:** Use `llama-3.1-8b-instant` (fastest)
- **Production/Demo:** Use `llama-3.1-70b-versatile` (best quality)

### 2. Optimize Prompts
- Keep system prompts concise
- Limit conversation history to last 10 messages
- This reduces token usage and improves speed

### 3. Monitor Usage
- Check your usage at: https://console.groq.com
- Free tier is generous but has limits
- Plan to upgrade if you exceed limits

### 4. Test All Modes
- Test each personality mode
- Verify responses are appropriate
- Adjust system prompts if needed

---

## 🚀 Next Steps

1. ✅ Get Groq API key
2. ✅ Add to `.env` file
3. ✅ Start backend with Docker
4. ✅ Test API endpoints
5. ✅ Build frontend
6. ✅ Deploy MVP
7. 🔄 Switch to Claude when ready for production

---

## 📞 Need Help?

- **Groq Documentation:** https://console.groq.com/docs
- **Groq Discord:** https://discord.gg/groq
- **API Status:** https://status.groq.com

---

## 💰 Cost Comparison

| Provider | MVP Cost | Production Cost |
|----------|----------|-----------------|
| **Groq (Free)** | **$0** | **$0** (with limits) |
| Together AI | $20/month | $100/month |
| Claude Haiku | $50/month | $300/month |
| Claude Sonnet | $200/month | $1,000/month |

**Start with Groq, scale with Claude!** 🎉

---

*Last Updated: December 31, 2024*