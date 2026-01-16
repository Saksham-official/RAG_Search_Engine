# Using OpenAI and Groq APIs

This PDF RAG application now supports both **OpenAI** and **Groq** as LLM providers.

## Configuration

Edit the `.env` file to select your preferred LLM provider:

```env
# Set your API keys
GROQ_API_KEY=your-groq-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Choose LLM provider: "openai" or "groq"
LLM_PROVIDER=groq
```

## Switching Between Providers

### To use Groq (default):
```env
LLM_PROVIDER=groq
```
- Model: `llama-3.1-8b-instant`
- Faster and free tier available
- Great for testing and development

### To use OpenAI:
```env
LLM_PROVIDER=openai
```
- Model: `gpt-3.5-turbo` (you can change to `gpt-4` or `gpt-4-turbo` in `rag.py`)
- Higher quality responses
- Requires paid API access

## Installation

Make sure to install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

After configuring your `.env` file:

```bash
uvicorn main:app --reload
```

The application will automatically use the provider specified in `LLM_PROVIDER`.

## Notes

- You only need the API key for the provider you're using
- The application will print which provider is being used when processing queries
- Invalid provider names will raise a `ValueError`
