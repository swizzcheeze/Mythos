# Frontier Models Quick Reference

## Setup Commands

### Windows PowerShell

**Using Anthropic Claude:**
```powershell
$env:MYTHOS_LLM_PROVIDER="anthropic"
$env:ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"
docker compose up --build -d
```

**Using Local Ollama:**
```powershell
$env:MYTHOS_LLM_PROVIDER="ollama"
docker compose up --build -d
```

### Linux/macOS Bash

**Using Anthropic Claude:**
```bash
export MYTHOS_LLM_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"
docker compose up --build -d
```

**Using Local Ollama:**
```bash
export MYTHOS_LLM_PROVIDER="ollama"
docker compose up --build -d
```

## Quick Tests

```powershell
# Check provider health
curl http://localhost:8001/ollama/health

# List available models
curl http://localhost:8001/ollama/models

# Test generation
curl -X POST http://localhost:8001/ollama/generate `
  -H "Content-Type: application/json" `
  -d '{"prompt": "Write a one-sentence story about dragons."}'

# Run full test suite
python test_frontier_models.py
```

## Model Selection Guide

| Model | Best For | Speed | Cost | Quality |
|-------|----------|-------|------|---------|
| **claude-3-5-sonnet-20241022** | General use | Fast | Medium | Excellent |
| **claude-3-7-sonnet-20250219** | Latest features | Fast | Medium | Excellent |
| **claude-3-opus-20240229** | Maximum quality | Slow | High | Outstanding |
| **claude-3-5-haiku-20241022** | High volume | Very Fast | Low | Good |
| **llama3** (Ollama) | Local/Private | Varies | Free | Good |

## Environment Variables Cheat Sheet

```env
# Provider Selection
MYTHOS_LLM_PROVIDER=anthropic          # or "ollama"

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-api03-...
MYTHOS_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Ollama Configuration
MYTHOS_OLLAMA_BASE_URL=http://host.docker.internal:11434
MYTHOS_OLLAMA_MODEL=llama3

# Advanced: Different models for different tasks
MYTHOS_GENERATOR_MODEL=claude-3-opus-20240229     # Creative writing
MYTHOS_CRITIC_MODEL=claude-3-5-haiku-20241022    # Quick critique
```

## Cost Optimization Tips

1. **Use Haiku for high-volume operations** (testing, iteration)
2. **Use Sonnet for production** (best balance)
3. **Use Opus for final polish** (highest quality)
4. **Mix providers**: Ollama for development, Anthropic for production

## Common Issues

### "anthropic package not installed"
```powershell
docker compose build --no-cache
docker compose up -d
```

### "invalid API key"
- Check key starts with `sk-ant-api03-`
- Verify no extra spaces or quotes
- Check key is active at https://console.anthropic.com/

### Provider shows "ollama" but expected "anthropic"
```powershell
# Check environment
docker compose exec mythos_backend printenv | Select-String "MYTHOS"

# Restart with correct env
docker compose down
$env:MYTHOS_LLM_PROVIDER="anthropic"
docker compose up -d
```

### Rate limiting
- Wait 5-10 seconds between requests
- Use Haiku for testing
- Consider implementing exponential backoff

## Monitoring Usage

Check logs for provider confirmation:
```powershell
docker compose logs mythos_backend | Select-String "Anthropic|provider"
```

Look for:
```
✓ Anthropic API configured with model: claude-3-5-sonnet-20241022
```

## Cost Tracking (Approximate)

**Claude 3.5 Sonnet:**
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Typical operation costs:**
- Character analysis: ~$0.005
- Lore generation: ~$0.012
- Session creation: ~$0.009
- Multi-archetype blend: ~$0.015

**Monthly estimates:**
- Light usage (100 ops/month): ~$1
- Medium usage (1000 ops/month): ~$10
- Heavy usage (10000 ops/month): ~$100

## Switching Providers

You can switch anytime without losing data:

```powershell
# Start with Anthropic
$env:MYTHOS_LLM_PROVIDER="anthropic"
docker compose up -d
# ... work ...

# Switch to Ollama
docker compose down
$env:MYTHOS_LLM_PROVIDER="ollama"
docker compose up -d
# ... work continues ...
```

Your worlds, lore, and sessions persist across provider changes!

## Best Practices

1. **Development**: Use Ollama (free, fast iteration)
2. **Testing**: Use Haiku (low cost, good quality)
3. **Production**: Use Sonnet (excellent balance)
4. **Final Polish**: Use Opus (maximum quality)
5. **Never commit**: Add `.env` to `.gitignore`
6. **Rotate keys**: Change API keys regularly
7. **Set alerts**: Monitor billing in Anthropic console

## Getting Help

- **Setup issues**: See [FRONTIER_MODELS.md](FRONTIER_MODELS.md)
- **API errors**: Check https://console.anthropic.com/
- **General help**: Open issue on GitHub
- **Test suite**: Run `python test_frontier_models.py`

## Links

- [Anthropic Console](https://console.anthropic.com/)
- [Anthropic Pricing](https://www.anthropic.com/api#pricing)
- [Full Documentation](FRONTIER_MODELS.md)
- [Installation Guide](INSTALLATION.md)
- [Main README](README.md)
