# Language Feedback API

An LLM-powered API that analyzes sentences written by language learners and returns structured grammar feedback. Built with FastAPI and Claude Haiku.

---

## What I Built

The API takes a sentence, a target language, and the learner's native language, and returns a corrected sentence, a list of errors with explanations, and a CEFR difficulty rating. The whole thing runs in Docker and responds in well under 30 seconds.

---

## Design Decisions

### Why Claude Haiku
I went with Haiku instead of a larger model for a few reasons. It is cheap, which matters a lot for an endpoint that could get hit thousands of times a day in a real app. It is fast, consistently coming in well under the 30 second limit. And for a task this well defined, a smaller model with a good prompt outperforms a bigger model with a lazy one. Haiku handled every language in my test suite correctly, including Japanese and Korean.

### Prompt Strategy
The prompt was where I spent most of my time. My approach was to be specific rather than general because vague instructions produce inconsistent results.

A few things I was deliberate about:

The error detection rules explicitly tell the model NOT to flag things that are not actually wrong. Subject pronouns in Spanish are optional, not errors. Regional variations are not errors. This matters because over-correction is frustrating for learners and would erode trust in the app fast.

For non-Latin scripts I named specific grammar concepts like Japanese particles, Korean speech levels, Arabic case, and Russian aspect rather than just saying "support all languages." Naming them forces the model to think script-specifically rather than defaulting to Latin-script assumptions.

The CEFR section defines each level with concrete examples so ratings are consistent across requests rather than arbitrary.

The output format section is strict: raw JSON only, no markdown, no backticks, must be parseable by JSON.parse(). I also added a fallback parser that strips code fences in case the model ignores that instruction.

### Caching
The API caches responses in memory using an MD5 hash of the sentence plus both languages as the key. Same input twice? Return the cached result instantly, no API call. In a language learning app this actually matters because learners make the same common mistakes constantly, so cache hit rates in production would be meaningful. It cuts costs and latency at the same time.

### Error Handling
Every Anthropic failure mode is handled explicitly: bad API key, rate limits, connection failures, and unparseable responses. Each one returns a meaningful HTTP status code instead of a generic 500.

---

## How to Run

### Local
```bash
git clone https://github.com/YOUR_USERNAME/intern-task-2026.git
cd intern-task-2026

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

uvicorn app.main:app --reload
```

Test it:
```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"sentence": "Yo soy fue al mercado ayer.", "target_language": "Spanish", "native_language": "English"}'
```

### Docker
```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
docker compose up --build
```

---

## Tests

15 tests total: 5 unit tests and 10 integration tests.

Unit tests mock the Anthropic client so they run without an API key. They cover response parsing, field mapping, and schema validation.

Integration tests make real API calls and cover Spanish conjugation errors, French gender agreement, Japanese particles, Korean sentence structure, Portuguese spelling, correct sentences in multiple languages, and schema validation across all response types.
```bash
# Unit tests (no API key needed)
pytest tests/test_feedback_unit.py -v

# Integration tests
export ANTHROPIC_API_KEY=your-key-here
pytest tests/test_feedback_integration.py -v
```

---

## Assumptions

Subject pronouns in pro-drop languages like Spanish and Italian are optional by definition, so I told the model not to flag them as errors. A learner writing "Yo fui" instead of "Fui" is not making a mistake.

CEFR difficulty is rated on sentence complexity, not on whether it has errors. A sophisticated sentence with a typo is still C1.

For languages I cannot personally verify like Japanese, Korean, and Arabic, I rely on the model's linguistic knowledge guided by the structured prompt. In a real production system I would want native speaker review or a secondary verification pass for low-confidence outputs.