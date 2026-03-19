# REST-API AUTO CODING EXPERT

> **50년 경력의 전설적 시스템 트레이딩 아키텍트 & 퀀트 개발 전문가**  
> 자동매매의 코딩전문가로 수정, 보완할 점들을 스스로 판단하여 조언한다.

A FastAPI service that analyses submitted automated-trading code (Python, Pine Script, etc.) using a veteran trading-architect AI persona and returns structured, battle-tested advice.

---

## Features

| 검수 기준 | 설명 |
|---|---|
| 🔒 Robustness (안정성) | 예외 처리, 네트워크 단절 대응, API 에러 코드 처리 |
| 💰 Risk Management (리스크 관리) | 손절/익절, 변동성 조절, 포지션 사이징 |
| ⚡ Execution Efficiency (실행 효율) | 루프 최적화, 비동기 처리, 불필요한 연산 제거 |
| 🏦 Market Reality (시장 현실성) | 세금·수수료·슬리피지 반영 여부 |
| 🧠 Logic Integrity (논리적 무결성) | Look-ahead bias, 과적합 진단 |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 3. Run the server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## API Endpoints

### `GET /health`
Liveness probe — returns `{"status": "ok"}`.

### `POST /analyze`
Submit automated-trading code for expert review.

**Request body (JSON):**

| Field | Type | Required | Description |
|---|---|---|---|
| `code` | string | ✅ | Source code to analyse (min 10 chars) |
| `language` | string | ❌ | Language/platform (e.g. `"Python"`) |
| `additional_context` | string | ❌ | Strategy description, target market, etc. |

**Example request:**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "while True:\n    buy(\"005930\", 10)\n    time.sleep(1)",
    "language": "Python",
    "additional_context": "KOSPI momentum strategy using KIS API"
  }'
```

**Response body:**

```json
{
  "analysis": "### 1. 🔍 치명적 결함 진단 ...",
  "model": "gpt-4o",
  "input_tokens": 512,
  "output_tokens": 1024
}
```

The `analysis` field contains a full Markdown report with four sections:

1. **🔍 치명적 결함 진단 (Critical Audit)** — account-critical bugs
2. **🚀 코드 최적화 제안 (Code Improvement)** — refactored code snippets
3. **🛡️ 리스크 및 전략 보완 조언 (Strategic Advice)** — Korean-market-specific advice
4. **💡 Follow-up 질문 (Next Step)** — two key questions to improve completeness

---

## Running Tests

```bash
pip install pytest httpx
pytest tests.py -v
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | Model to use |
| `OPENAI_MAX_TOKENS` | `4096` | Max tokens for the response |
