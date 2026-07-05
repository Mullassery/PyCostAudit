# Mock Pricing Data (Development)

**Status**: For development/testing only. Production uses live API pricing.

---

## OpenAI (Mock)

Based on February 2025 knowledge + estimates for July 2026

| Model | Input ($/1M) | Output ($/1M) | Vision Premium |
|-------|---|---|---|
| GPT-4 | $30 | $60 | 25% |
| GPT-4 Turbo | $10 | $30 | 25% |
| GPT-5 (estimated) | $50 | $150 | 25% |

---

## AWS Bedrock (Mock)

Based on available documentation + estimates

| Model | Input ($/1M) | Output ($/1M) |
|-------|---|---|
| Claude 3 Opus | $15 | $75 |
| Claude 3 Sonnet | $3 | $15 |
| Claude 3 Haiku | $0.25 | $1.25 |
| Llama 2 70B | $0.80 | $1.00 |
| Mistral Large | $8 | $24 |

Provisioned Throughput: 10% discount

---

## Google Gemini (Mock)

Based on available documentation

| Model | Input ($/1M) | Output ($/1M) |
|-------|---|---|
| Gemini Pro | $0.125 | $0.375 |
| Gemini Pro Vision | $0.125 | $0.375 |

---

## Production Usage

In production, these values are replaced by:

```python
# Example: Fetch OpenAI pricing from API
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
pricing = fetch_openai_pricing(openai_client)

# Example: Fetch Bedrock pricing from AWS
bedrock = boto3.client('bedrock-pricing')
pricing = bedrock.get_pricing()

# Example: Fetch Gemini pricing from Google
gemini_pricing = fetch_gemini_pricing()
```

See: `pycostaudit/pricing/loaders.py` for implementation.
