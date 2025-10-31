# Model Configuration Guide

## Google Gemini Model Selection

The application uses Google's Gemini API, which offers free tier access with generous limits.

### Gemini 1.5 Flash (Default)

If you want fast responses and good quality:

```env
LLM_MODEL=gemini-1.5-flash
```

**Benefits**:
- ✅ Free tier available
- ✅ Very fast responses
- ✅ Good quality for this use case
- ✅ Lower latency
- ✅ Efficient token usage

**Limitations**:
- Slightly less sophisticated reasoning than Pro
- Still excellent for conversational tasks

### Gemini 1.5 Pro

If you need more advanced reasoning capabilities:

```env
LLM_MODEL=gemini-1.5-pro
```

**Benefits**:
- ✅ More sophisticated reasoning
- ✅ Better context understanding
- ✅ More natural conversations
- ✅ Better handling of complex scenarios

**Considerations**:
- May have stricter rate limits on free tier
- Slightly slower than Flash
- Still free to use

## How to Configure

1. **Get a Gemini API Key**:
   - Visit: https://aistudio.google.com/app/apikey
   - Sign in with your Google account
   - Create a new API key (it's free!)

2. **Open your `.env` file** (create from `.env.example` if needed)

3. **Set the API key and model**:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   LLM_MODEL=gemini-1.5-flash
   ```

4. **Restart the backend**:
   ```bash
   # Stop the server (Ctrl+C) and restart
   cd backend
   uvicorn main:app --reload
   ```

## Model Comparison

| Feature | Gemini 1.5 Flash | Gemini 1.5 Pro |
|---------|------------------|----------------|
| Cost | Free | Free |
| Speed | Fast | Slower |
| Response Quality | Excellent | Excellent+ |
| Context Understanding | Very Good | Excellent |
| Complex Reasoning | Good | Excellent |
| Token Efficiency | High | Medium |

## Recommendation

**For this assignment**: `gemini-1.5-flash` is perfect! It's fast, free, and provides excellent quality.

**For production**: Start with `gemini-1.5-flash`, upgrade to Pro only if you need advanced reasoning.

## Embeddings

The application uses Gemini's `text-embedding-004` model for embeddings, which is included in the free tier.

## Troubleshooting

### Error: "GEMINI_API_KEY environment variable is not set"

- Make sure your `.env` file exists and contains `GEMINI_API_KEY=your_key`
- Verify the key is correct and active

### Error: "API key not valid" or "Quota exceeded"

- Verify your API key at https://aistudio.google.com/app/apikey
- Check your quota/usage limits
- Ensure you're using a valid API key format

### Error: "Model not found"

- Make sure you're using a valid model name:
  - `gemini-1.5-flash` ✅
  - `gemini-1.5-pro` ✅
  - `gemini-pro` ✅ (older version)

## Getting Your API Key

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file
5. No credit card required! Free tier is generous.

## Migration from OpenAI

If you were previously using OpenAI, the switch to Gemini is automatic once you:
1. Install `google-generativeai` package
2. Set `GEMINI_API_KEY` in your `.env`
3. Restart the server

All functionality remains the same, but now using Google's free Gemini API!
