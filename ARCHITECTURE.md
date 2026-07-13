# Chariot — AI Campaign Content Generation Service

Python/FastAPI rebuild of an enterprise content-generation microservice.
Generates channel-specific marketing draft copy from campaign briefs using an
LLM, grounded by RAG over previously approved campaigns, with validation
guardrails before anything reaches a human reviewer.

## 1. Why this exists (business context)

Two bottlenecks in the original enterprise workflow:

1. **Human authoring is slow.** Marketers draft campaign content from a blank
   page. Content authoring is the slowest step in the delivery pipeline.
2. **Metadata is scattered across teams.** Alert configuration and reference
   data are owned by separate teams/services. Manually coordinating across
   them loses metadata and adds delay.

Chariot addresses both: a unified service that aggregates configuration and
reference data, generates draft content with an LLM, validates it, and hands
a review-ready draft to the marketer. Authoring shifts from *writing* to
*reviewing*.

**Design principle:** the system improves through retrieval, not training.
Model weights never change. Every approved campaign enriches the retrieval
corpus, which improves future prompts. Day-one quality is solved by seeding
the corpus with historical human-written campaigns.

## 2. Modules

```
chariot/
  api/            FastAPI routes (generate, approve, alert-configs, health)
  config_store/   Alert type codes + reference data access (Postgres)
  retrieval/      Embedding client + pgvector similarity search (RAG)
  prompting/      Prompt builder: instructions + references + examples + brief
  llm/            Provider abstraction (Ollama local / OpenAI cloud)
  guardrails/     Output validation against reference data
  persistence/    Campaign records, audit log (Postgres)
```

## 3. Core flow — POST /generate

```
POST /generate {alert_type_code, brief, channel}
 1. config_store : load config + references for the type code
 2. retrieval    : embed the brief (same embedding model as the corpus)
 3. retrieval    : pgvector top-3 similar approved campaigns
 4. prompting    : build prompt = instructions + references
                   + 3 few-shot examples + brief + channel rules
 5. llm          : call provider, request schema-shaped output
 6. guardrails   : validate — promo codes / rates / expiry vs reference
                   data; required disclosures present; schema conformance
 7a. valid       : persist draft (status=PENDING_APPROVAL), return it
 7b. invalid     : retry once with validation feedback in the prompt;
                   on second failure return a structured error (fallback
                   to the manual authoring path)
```

## 4. Learning flow — POST /campaigns/{id}/approve

```
 1. mark campaign APPROVED
 2. embed the approved content
 3. insert (content, vector, type_code, channel) into pgvector
```

Retrieval corpus grows with every approval → future generations improve.

## 5. Data model (v1)

- `alert_configs`   — type_code (3 letters + 3 digits, e.g. ABC123), channel
  defaults, tone/template selector
- `references`      — reference data keyed by type_code: promo codes, rates,
  expiry windows, required disclosures
- `campaigns`       — brief, generated content, status
  (PENDING_APPROVAL | APPROVED | REJECTED), audit fields
- `campaign_embeddings` — pgvector column + metadata for similarity search

## 6. Provider abstraction

```python
class LLMProvider(Protocol):
    def generate(self, prompt: str, schema: type[BaseModel]) -> BaseModel: ...
    def embed(self, text: str) -> list[float]: ...
```

Implementations: `OllamaProvider` (dev, free, localhost:11434/v1),
`OpenAIProvider` (validation runs, spend-capped). Same interface — provider
selected by config. Bedrock can be added later behind the same Protocol.

Embedding-space rule: brief and corpus MUST be embedded by the same model;
vectors from different models are not comparable. Switching embedding models
requires re-embedding the corpus.

## 7. Guardrails (v1)

- Schema-enforced structured output (Pydantic)
- Programmatic fact checks: promo codes, rates, expiry validated against
  `references` — never trusted from the model
- Required legal disclosures asserted present (template-owned, not
  model-generated)
- One retry with validation feedback; then structured failure
- Per-call audit log: prompt version, model, tokens, latency, validation
  outcome

## 8. Deliberately out of scope for v1

- Delivery flows beyond a channel enum (email | sms) — the real system has 31
- Downstream publishing, scheduling, customer/group targeting
- Images or rich HTML content (text only)
- Human approval UI (approval is an API call)
- AuthN/AuthZ
- The upstream alert-config and references *services* — modeled as local
  Postgres tables instead

## 9. Open questions

- [ ] What exactly does the type code select at generation time — reference
  set only, or also tone/template? (current assumption: both)
- [ ] Retry budget: is one guardrail-feedback retry enough, or two?
- [ ] Seed corpus: how many historical campaigns to embed for day-one quality?
