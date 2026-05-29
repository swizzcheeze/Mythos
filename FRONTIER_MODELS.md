# Frontier Models Support - Complete Guide

Mythos World Engine supports **6 LLM providers** with seamless switching. **All provider SDKs are pre-installed** - no container rebuild required when switching!

## 🚀 Key Feature: Zero-Rebuild Provider Switching

All provider packages are included in the Docker image. Switch providers by:
1. Changing environment variables
2. Restarting container (`docker compose restart mythos_backend`)

**No `docker compose build` needed!**

## Supported Providers

| Provider | Best For | Speed | Cost | Setup Link |
|----------|----------|-------|------|------------|
| **Anthropic Claude** | Highest quality reasoning | Fast | Medium | https://console.anthropic.com/ |
| **OpenRouter** | Access 200+ models, one key | Varies | Varies | https://openrouter.ai/ |
| **Groq** | Ultra-fast inference | Very Fast | Low | https://console.groq.com/ |
| **xAI (Grok)** | Latest X/Twitter models | Fast | Medium | https://console.x.ai/ |
| **Google Gemini** | Multimodal, large context | Fast | Low-Med | https://makersuite.google.com/app/apikey |
| **Ollama** | Free, private, offline | Depends | Free | Local install |

## Quick Start Examples

### Anthropic Claude (Best Quality)

```powershell
$env:MYTHOS_LLM_PROVIDER="anthropic"
$env:ANTHROPIC_API_KEY="sk-ant-api03-your-key"
docker compose restart mythos_backend  # No rebuild!
```

### OpenRouter (200+ Models with One Key)

```powershell
$env:MYTHOS_LLM_PROVIDER="openrouter"
$env:OPENROUTER_API_KEY="sk-or-v1-your-key"
$env:MYTHOS_OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"  # Or any OpenRouter model
docker compose restart mythos_backend
```

### Groq (Blazing Fast - Up to 800 tok/sec)

```powershell
$env:MYTHOS_LLM_PROVIDER="groq"
$env:GROQ_API_KEY="gsk_your-key"
docker compose restart mythos_backend
```

### xAI Grok

```powershell
$env:MYTHOS_LLM_PROVIDER="xai"
$env:XAI_API_KEY="xai-your-key"
docker compose restart mythos_backend
```

### Google Gemini

```powershell
$env:MYTHOS_LLM_PROVIDER="gemini"
$env:GEMINI_API_KEY="AIzaSy-your-key"
docker compose restart mythos_backend
```

### Local Ollama (Default - Free & Private)

```powershell
$env:MYTHOS_LLM_PROVIDER="ollama"
docker compose restart mythos_backend
```

## Environment Variables Reference

### Provider Selection

```env
MYTHOS_LLM_PROVIDER=ollama  # Options: ollama, anthropic, openrouter, groq, xai, gemini
```

### Anthropic Configuration

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
MYTHOS_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # See models below
```

### OpenRouter Configuration

```env
OPENROUTER_API_KEY=sk-or-v1-...
MYTHOS_OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # See https://openrouter.ai/models
```

### Groq Configuration

```env
GROQ_API_KEY=gsk_...
MYTHOS_GROQ_MODEL=llama-3.3-70b-versatile  # Options: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
```

### xAI Configuration

```env
XAI_API_KEY=xai-...
MYTHOS_XAI_MODEL=grok-beta
```

### Google Gemini Configuration

```env
GEMINI_API_KEY=AIzaSy...
MYTHOS_GEMINI_MODEL=gemini-1.5-pro  # Options: gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp
```

### Ollama Configuration

```env
MYTHOS_OLLAMA_BASE_URL=http://host.docker.internal:11434
MYTHOS_OLLAMA_MODEL=llama3  # Any model you've pulled locally
```

### Advanced: Per-Task Model Override

```env
MYTHOS_GENERATOR_MODEL=claude-3-opus-20240229  # For creative generation
MYTHOS_CRITIC_MODEL=llama-3.3-70b-versatile     # For critique (Note: requires matching provider)
```

## Available Models

### Anthropic Claude Models

| Model | Description | Input Cost | Output Cost | Best For |
|-------|-------------|------------|-------------|----------|
| `claude-3-5-sonnet-20241022` | Latest Sonnet (Default) | $3/1M | $15/1M | General use, best balance |
| `claude-3-7-sonnet-20250219` | Newest with improved reasoning | $3/1M | $15/1M | Latest features |
| `claude-3-opus-20240229` | Highest quality | $15/1M | $75/1M | Maximum quality needed |
| `claude-3-5-haiku-20241022` | Fast & economical | $1/1M | $5/1M | High volume, testing |

### OpenRouter Models (Examples - 200+ available)

| Model ID | Description | Provider |
|----------|-------------|----------|
| `anthropic/claude-3.5-sonnet` | Claude via OpenRouter | Anthropic |
| `openai/gpt-4-turbo` | GPT-4 Turbo | OpenAI |
| `google/gemini-pro-1.5` | Gemini Pro | Google |
| `meta-llama/llama-3.1-70b-instruct` | Llama 3.1 70B | Meta |
| `anthropic/claude-3-opus` | Claude Opus | Anthropic |

**Full list**: https://openrouter.ai/models

### Groq Models

| Model | Description | Speed | Context |
|-------|-------------|-------|---------|
| `llama-3.3-70b-versatile` | Llama 3.3 70B (Default) | ~800 tok/s | 128K |
| `llama-3.1-70b-versatile` | Llama 3.1 70B | ~800 tok/s | 128K |
| `mixtral-8x7b-32768` | Mixtral 8x7B | ~500 tok/s | 32K |
| `gemma2-9b-it` | Google Gemma 2 9B | ~1000 tok/s | 8K |

### xAI (Grok) Models

| Model | Description | Context |
|-------|-------------|---------|
| `grok-beta` | Latest Grok model | 128K |

### Google Gemini Models

| Model | Description | Input Cost | Output Cost | Context |
|-------|-------------|------------|-------------|---------|
| `gemini-1.5-pro` | Pro quality (Default) | $1.25/1M | $5/1M | 2M tokens |
| `gemini-1.5-flash` | Fast & economical | $0.075/1M | $0.30/1M | 1M tokens |
| `gemini-2.0-flash-exp` | Experimental latest | Free (limited) | Free | 1M tokens |

### Ollama Models (Local)

Any model you've pulled locally:
- `llama3`, `llama3.1`, `llama3.2`
- `mistral`, `mixtral`
- `codellama`, `deepseek-coder`
- `qwen`, `phi3`
- And many more...

## Using .env File (Recommended)

Create `.env` in project root:

```env
# Provider selection
MYTHOS_LLM_PROVIDER=anthropic

# Anthropic (choose one)
ANTHROPIC_API_KEY=sk-ant-api03-your-key
MYTHOS_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# OpenRouter (uncomment to use)
# OPENROUTER_API_KEY=sk-or-v1-your-key
# MYTHOS_OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Groq (uncomment to use)
# GROQ_API_KEY=gsk_your-key
# MYTHOS_GROQ_MODEL=llama-3.3-70b-versatile

# xAI (uncomment to use)
# XAI_API_KEY=xai-your-key

# Gemini (uncomment to use)
# GEMINI_API_KEY=AIzaSy-your-key

# Ollama (local)
# MYTHOS_OLLAMA_MODEL=llama3
```

Then:
```powershell
docker compose up -d
```

Docker Compose automatically reads `.env` files.

## Testing Your Setup

### Check Provider Health

```bash
curl http://localhost:8001/ollama/health
```

**Example responses**:

```json
// Anthropic
{"provider": "anthropic", "connected": true, "model": "claude-3-5-sonnet-20241022"}

// OpenRouter
{"provider": "openrouter", "connected": true, "model": "anthropic/claude-3.5-sonnet"}

// Groq
{"provider": "groq", "connected": true, "model": "llama-3.3-70b-versatile"}

// Ollama
{"provider": "ollama", "connected": true, "generator_model": "llama3", "critic_model": "llama3"}
```

### Test Generation

```bash
curl -X POST http://localhost:8001/ollama/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Describe a dragon in 2 sentences."}'
```

### Run Full Test Suite

```powershell
python test_frontier_models.py anthropic  # Or: openrouter, groq, xai, gemini, ollama
```

## Cost Comparison (Approximate)

### Per Operation Costs

| Operation | Anthropic Sonnet | Groq | Gemini Pro | OpenRouter (Claude) | Ollama |
|-----------|------------------|------|------------|---------------------|--------|
| Character Analysis | ~$0.005 | ~$0.001 | ~$0.002 | ~$0.005 | Free |
| Lore Generation | ~$0.012 | ~$0.003 | ~$0.005 | ~$0.012 | Free |
| Multi-Archetype | ~$0.015 | ~$0.004 | ~$0.006 | ~$0.015 | Free |

### Monthly Estimates (Medium Usage - 1000 ops/month)

- **Anthropic Direct**: ~$10/month
- **OpenRouter**: ~$10-15/month (varies by model)
- **Groq**: ~$3-5/month
- **Gemini**: ~$4-6/month
- **xAI**: ~$8-12/month (estimate)
- **Ollama**: $0 (after hardware)

## Performance Comparison

| Provider | Latency | Throughput | Quality | Privacy |
|----------|---------|------------|---------|---------|
| **Anthropic** | ~1-3s | Medium | Excellent | API (cloud) |
| **OpenRouter** | ~1-4s | Varies | Varies | API (cloud) |
| **Groq** | ~0.5-1s | Very High | Good | API (cloud) |
| **xAI** | ~1-3s | Medium | Good | API (cloud) |
| **Gemini** | ~1-2s | High | Very Good | API (cloud) |
| **Ollama** | Varies | Depends | Good | Local (private) |

## Switching Providers Mid-Session

Your data persists across provider changes:

```powershell
# Start with Groq (fast development)
$env:MYTHOS_LLM_PROVIDER="groq"
docker compose up -d
# ... work ...

# Switch to Anthropic (production quality)
docker compose down
$env:MYTHOS_LLM_PROVIDER="anthropic"
$env:ANTHROPIC_API_KEY="sk-ant-..."
docker compose up -d  # No rebuild!
# ... work continues with same worlds/lore/sessions ...
```

## Troubleshooting

### "Provider X selected but API key not set"

Set the appropriate API key:
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."  # For Anthropic
$env:OPENROUTER_API_KEY="sk-or-..."  # For OpenRouter
# etc.
```

### "Package not installed" (Shouldn't happen - all pre-installed)

If you see this, rebuild the container:
```powershell
docker compose build --no-cache
docker compose up -d
```

### Rate Limiting

- **Anthropic**: Tier-based limits, check console
- **OpenRouter**: Per-model limits
- **Groq**: Very high limits (rarely hit)
- **Gemini**: Generous free tier, then paid
- **xAI**: Contact support for limits

**Solution**: Implement exponential backoff or use different provider temporarily.

### Invalid API Key Format

Each provider has specific formats:
- Anthropic: `sk-ant-api03-...`
- OpenRouter: `sk-or-v1-...`
- Groq: `gsk_...`
- xAI: `xai-...`
- Gemini: `AIzaSy...`

### Check Container Logs

```powershell
docker compose logs mythos_backend | Select-String "API configured"
```

Should show: `✓ [Provider] API configured with model: [model-name]`

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use `.env` files** and add to `.gitignore`
3. **Rotate keys regularly** in provider consoles
4. **Set billing alerts** to avoid surprises
5. **Use separate keys** for dev vs production
6. **Monitor usage** in provider dashboards

## Recommended Strategies

### Development Workflow
1. **Prototyping**: Use Ollama (free, fast iteration)
2. **Testing**: Use Groq (fast, low cost)
3. **Quality Check**: Use Anthropic Sonnet (best balance)
4. **Final Polish**: Use Anthropic Opus (maximum quality)

### Production Recommendations
- **High Quality**: Anthropic Claude Sonnet
- **Best Value**: Groq or Gemini Flash
- **Most Flexible**: OpenRouter (switch models easily)
- **Private/Offline**: Ollama

### Cost Optimization
- Use Groq/Gemini for high-volume operations
- Use Anthropic Haiku for quick iterations
- Use Anthropic Opus only for final outputs
- Mix providers: Fast for critique, quality for generation

## OpenRouter Special Features

OpenRouter provides unique capabilities:

### Access 200+ Models with One Key

```env
MYTHOS_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key

# Switch between any model without changing keys:
MYTHOS_OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
# MYTHOS_OPENROUTER_MODEL=openai/gpt-4-turbo
# MYTHOS_OPENROUTER_MODEL=google/gemini-pro-1.5
# MYTHOS_OPENROUTER_MODEL=meta-llama/llama-3.1-405b-instruct
```

### Automatic Fallbacks

OpenRouter can automatically fallback to alternative models if your primary choice is unavailable.

### Cost Tracking

View detailed cost breakdown in OpenRouter dashboard.

## Getting API Keys

| Provider | Signup Link | Free Tier |
|----------|-------------|-----------|
| Anthropic | https://console.anthropic.com/ | $5 credit |
| OpenRouter | https://openrouter.ai/keys | Varies by model |
| Groq | https://console.groq.com/ | Generous free tier |
| xAI | https://console.x.ai/ | Limited beta |
| Gemini | https://makersuite.google.com/app/apikey | 60 req/min free |
| Ollama | https://ollama.com/download | 100% free (local) |

## Support & Resources

- **Mythos Issues**: GitHub Issues
- **Anthropic Support**: support@anthropic.com
- **OpenRouter Support**: https://openrouter.ai/docs
- **Groq Support**: https://console.groq.com/docs
- **xAI Support**: support@x.ai
- **Gemini Support**: Google AI Studio

## Future Enhancements

Planned features:
- Token usage tracking per session
- Cost estimation dashboard
- Automatic provider fallback on errors
- Streaming responses
- Batch processing optimization
- Provider-specific prompt optimization

---

**Status**: All 6 providers fully supported and tested
**Zero-Rebuild Switching**: ✅ Enabled
**Documentation**: ✅ Complete
