# PaperlyAI — Production-Grade Development Plan

Scratch se leke production launch tak ka complete roadmap. Current codebase (Django + LangGraph + OpenAI) ko base rakh ke banaya gaya hai — rewrite nahi, systematic upgrade.

---

## Phase 0 — Foundations & Architecture Decisions (Week 1)

Sabse pehle decisions lock karo, taaki baad mein rework na karna pade.

### 0.1 Tech stack finalize karo
| Layer | Current | Recommended |
|---|---|---|
| Web framework | Django (sync) | Django rakho, but async views ya DRF add karo API ke liye |
| Task queue | None | **Celery + Redis** (ya lightweight ho to Django-Q2) |
| DB | SQLite/Postgres via dj-database-url | Postgres (already supported) — lock this in, SQLite sirf local dev |
| Cache | None | Redis (dual purpose: Celery broker + cache) |
| LLM orchestration | LangGraph | Rakho, isko touch mat karo — architecture sahi hai |
| Frontend | Django templates + vanilla JS | Rakho for MVP; baad mein htmx add karke polling UX behtar karo |
| Hosting | Render/Railway | Render/Railway theek hai, but worker dyno alag se chahiye Celery ke liye |

### 0.2 Repo structure decide karo
```
paperly-ai/
├── paperlydjango/          # settings, urls
├── paperlyapp/             # views, models, serializers
├── paperlyagents/          # NEW: saara LangGraph/agent logic yahan move karo (graph.py se alag app)
│   ├── graph.py
│   ├── nodes/              # har generator/critic function alag file mein
│   ├── prompts/            # prompts ko code se alag rakho (jinja templates ya .txt files)
│   └── tasks.py            # Celery tasks
├── tests/
├── .github/workflows/      # CI
└── docker-compose.yml      # local dev: web + worker + redis + postgres
```
**Kyu zaruri hai**: abhi `graph.py` mein 400+ lines ek hi file mein hai — prompts, state, nodes, graph wiring sab mixed. Alag karne se testing aur maintenance dono easy honge.

### 0.3 Environment setup
- `.env.example` ko poora karo: `OPENAI_API_KEY`, `REDIS_URL`, `DATABASE_URL`, `SECRET_KEY`, `SENTRY_DSN`, `MAX_GENERATIONS_PER_DAY`
- Docker Compose local dev ke liye (web, worker, redis, postgres) — naya dev onboard karne mein 5 min lage, 2 ghante nahi

---

## Phase 1 — Data Model & Persistence (Week 1-2)

Abhi `models.py` khaali hai. Yeh sabse pehle fix karo kyunki baaki sab isi pe depend karega.

### 1.1 Core models
```python
class PaperRequest(models.Model):
    STATUS_CHOICES = [("queued","Queued"),("running","Running"),
                       ("done","Done"),("failed","Failed")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)  # anon allowed initially
    topic = models.CharField(max_length=500)
    field = models.CharField(max_length=100)
    level = models.CharField(max_length=50)
    objectives = models.CharField(max_length=500)
    keywords = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    current_section = models.CharField(max_length=50, blank=True)   # for progress UI
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_tokens_used = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0)

class PaperSection(models.Model):
    paper = models.ForeignKey(PaperRequest, related_name="sections", on_delete=models.CASCADE)
    section_type = models.CharField(max_length=30)  # intro/lit_review/methodology/conclusion/abstract
    content = models.TextField()
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class GeneratedPaper(models.Model):
    request = models.OneToOneField(PaperRequest, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    novelty = models.TextField()
    pdf_file = models.FileField(upload_to="papers/", null=True, blank=True)
```
**Kyu**: history dashboard, re-download, "resume from failure" (agar section 3 pe crash hua to 1-2 dobara generate nahi karna padega), analytics — sab isi se milta hai.

### 1.2 Migration
```bash
python manage.py makemigrations paperlyapp
python manage.py migrate
```

---

## Phase 2 — Background Job System (Week 2-3) — **Highest Priority**

Yeh sabse critical change hai. Iske bina production mein app timeout ho jayegi.

### 2.1 Celery setup
```python
# paperlydjango/celery.py
from celery import Celery
app = Celery("paperlydjango")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```
```python
# settings.py
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")
CELERY_TASK_TIME_LIMIT = 600  # 10 min hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 540
```

### 2.2 Graph ko task mein wrap karo
```python
@shared_task(bind=True, max_retries=2)
def generate_paper_task(self, paper_request_id):
    paper_req = PaperRequest.objects.get(id=paper_request_id)
    paper_req.status = "running"
    paper_req.save()
    try:
        result = rungraph(user_input, progress_callback=lambda section: update_progress(paper_req, section))
        save_result_to_db(paper_req, result)
        paper_req.status = "done"
    except Exception as e:
        paper_req.status = "failed"
        paper_req.error_message = str(e)
    paper_req.save()
```

### 2.3 View badlo — job submit karo, wait mat karo
```python
def generate_paper(request):
    # validate input (existing logic rakho)
    paper_req = PaperRequest.objects.create(**user_input, status="queued")
    generate_paper_task.delay(paper_req.id)
    return JsonResponse({"status": "queued", "request_id": str(paper_req.id)})

def check_status(request, request_id):
    paper_req = PaperRequest.objects.get(id=request_id)
    return JsonResponse({
        "status": paper_req.status,
        "current_section": paper_req.current_section,
        "error": paper_req.error_message,
    })

def get_result(request, request_id):
    paper = GeneratedPaper.objects.get(request_id=request_id)
    return JsonResponse({...})
```

### 2.4 Frontend polling (simple, no infra change chahiye)
```javascript
async function pollStatus(requestId) {
  const res = await fetch(`/status/${requestId}/`);
  const data = await res.json();
  updateProgressBar(data.current_section);  // "Writing methodology..."
  if (data.status === "done") window.location.href = `/result/${requestId}/`;
  else if (data.status === "failed") showError(data.error);
  else setTimeout(() => pollStatus(requestId), 3000);
}
```
Baad mein (nice-to-have): SSE ya WebSocket se real-time push, polling se better UX milega.

### 2.5 Deployment change
- Render/Railway pe **do services** chahiye: `web` (gunicorn) aur `worker` (celery worker), plus ek Redis addon.
- `Procfile` update karo:
```
web: gunicorn paperlydjango.wsgi:application
worker: celery -A paperlydjango worker --loglevel=info --concurrency=2
```

---

## Phase 3 — Cost Control & Abuse Prevention (Week 3)

### 3.1 Rate limiting
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key="ip", rate="3/h", method="POST", block=True)
def generate_paper(request):
    ...
```
Anonymous users: 3 papers/hour/IP. Logged-in users: higher quota, tracked in DB.

### 3.2 Cost tracking per request
- Har LLM call se `response.usage_metadata` (tokens) capture karo, `PaperRequest.total_tokens_used` mein add karo.
- Daily/monthly budget cap: agar total spend threshold cross kare to naye requests reject karo with clear message.

### 3.3 Reduce redundant LLM calls
- Abhi critic loop max 2 retries/section karta hai — theek hai, but **combine karo related calls**: e.g. novelty extraction ke 5 alag calls (per arxiv paper) ko ek hi batched call mein convert karo (sab 5 abstracts ek prompt mein bhejo, structured output se 5 novelties nikalo). Isse 5 calls → 1 call.
- Arxiv results cache karo (Redis, 24h TTL) — same topic dobara search kare to fresh fetch na ho.

### 3.4 Auth (minimum viable)
- Django's built-in auth ya simple magic-link email login — full account system nahi chahiye abhi, but kam se kam ek identifier chahiye rate-limiting aur history ke liye.

---

## Phase 4 — Reliability & Code Quality (Week 4)

### 4.1 LLM call wrapper — retries + timeout
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def safe_llm_invoke(llm, prompt, timeout=60):
    return llm.invoke(prompt, config={"timeout": timeout})
```
Har `llm.invoke(...)` call ko isse replace karo graph.py mein.

### 4.2 Structured output for critic (JSON parsing fix)
```python
from pydantic import BaseModel

class CriticOutput(BaseModel):
    needs_rewrite: bool
    improvements: list[str]

structured_llm = llm.with_structured_output(CriticOutput)
critique = structured_llm.invoke(prompt)  # no manual json.loads, no backtick stripping
```

### 4.3 Prompts ko code se alag karo
```
paperlyagents/prompts/
├── introduction.jinja
├── literature_review.jinja
├── critic.jinja
```
Version control ke liye alag, aur non-engineers (agar prompt tweak karna ho) bhi edit kar sake without touching Python.

### 4.4 Refactor graph.py
- `rungraph()` ke andar nested functions ko top-level module functions banao — testability ke liye. Abhi unit test likhna almost impossible hai kyunki sab kuch closures ke andar hai.
- `llm` instance ko dependency-injected banao (function param), taaki test mein mock LLM pass kar sako.

### 4.5 Resume-from-failure
- Section-by-section DB mein save karo (Phase 1 model se). Agar generation section 3 pe fail ho, retry endpoint banao jo already-generated sections skip kare.

---

## Phase 5 — Testing & CI/CD (Week 5)

### 5.1 Unit tests
- `test_graph.py`: har generator node ko mock LLM ke saath test karo (input state → expected keys in output state).
- `test_views.py`: validation logic, rate limiting, error responses.
- `test_critic.py`: JSON parsing edge cases (malformed output, missing keys).

### 5.2 Integration test
- Ek end-to-end test jo real LangGraph flow chalaye with a **mocked** `ChatOpenAI` (LangChain ka `FakeListLLM` use kar sakte ho) — poora pipeline bina real API cost ke test ho jaye.

### 5.3 CI pipeline
```yaml
# .github/workflows/ci.yml
- run: pip install -r requirements.txt
- run: python manage.py test
- run: python manage.py check --deploy   # Django deployment checklist
- run: flake8 / ruff for linting
```

### 5.4 Pin dependencies
```
langchain==0.3.x
langchain-openai==0.2.x
openai==1.x
```
`pip freeze > requirements.lock.txt` ya better, `uv`/`poetry` migrate karo for reproducible builds.

---

## Phase 6 — Observability & Monitoring (Week 5-6)

### 6.1 Error tracking
- Sentry integrate karo (`sentry-sdk`) — Django + Celery dono ke liye. Har failed generation, LLM timeout, ya JSON parse error automatically capture ho.

### 6.2 Structured logging
```python
logger.info("section_generated", extra={
    "request_id": str(paper_req.id), "section": "introduction",
    "tokens": response.usage_metadata, "duration_ms": elapsed
})
```
Isse pata chalega kaunsa section sabse zyada time leta hai / fail hota hai.

### 6.3 Health check
```python
def health(request):
    checks = {"db": check_db(), "redis": check_redis(), "openai": bool(settings.OPENAI_API_KEY)}
    status = 200 if all(checks.values()) else 503
    return JsonResponse(checks, status=status)
```

### 6.4 Basic dashboard
- Django admin se `PaperRequest` model expose karo (filter by status/date) — free monitoring milega bina extra tool ke.

---

## Phase 7 — Security Hardening (Week 6)

- [ ] `SECRET_KEY` — ensure production env mein hi set ho, default kabhi use na ho (already env-based hai, bas verify)
- [ ] Input sanitization: arxiv abstracts se prompt injection possible hai — LLM prompts mein clear delimiters use karo (e.g. `<untrusted_content>...</untrusted_content>`) taaki model instruction aur data mein confuse na ho
- [ ] CSRF: JS fetch calls mein CSRF token bhejna verify karo
- [ ] `python manage.py check --deploy` run karke Django ke security warnings fix karo
- [ ] Dependency scanning: `pip-audit` ya GitHub Dependabot on karo

---

## Phase 8 — Deployment & Scaling (Week 7)

### 8.1 Infra checklist
- Render/Railway: web service + worker service + Redis + Postgres (managed)
- Auto-scaling worker count based on queue length (agar traffic grow kare)
- CDN/static via Whitenoise (already hai) — theek hai for now

### 8.2 Cost estimation before launch
- Ek generation ≈ kitne tokens? Calculate karo (5 arxiv summaries + novelty + 5 sections × avg 2 attempts + 5 critics ≈ 20 calls, ~1500-2500 tokens avg per call) → per-generation cost estimate karo, phir daily budget decide karo.

### 8.3 Soft launch
- Beta users ka small group, feedback loop, monitor Sentry/costs for a week before public launch.

---

## Timeline Summary

| Week | Focus |
|---|---|
| 1 | Architecture decisions, repo restructure, env setup |
| 1-2 | DB models & persistence |
| 2-3 | Celery background jobs (**critical path**) |
| 3 | Rate limiting, cost tracking, auth |
| 4 | Reliability (retries, structured output, refactor) |
| 5 | Tests + CI/CD |
| 5-6 | Monitoring (Sentry, logging, health check) |
| 6 | Security hardening |
| 7 | Deployment, scaling, soft launch |

**Sabse pehle Phase 2 (background jobs) karo** — baaki sab iske bina bhi chal sakta hai, but yeh na ho to production mein app timeout hi ho jayegi.

---

## Quick Win vs Nice-to-Have

**Must-have before any real users (MVP-production)**: Phase 1, 2, 3
**Should-have soon after**: Phase 4, 5, 6
**Can wait**: Phase 7 (security hardening beyond basics), Phase 8 auto-scaling
