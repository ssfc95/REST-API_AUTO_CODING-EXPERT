"""
REST-API AUTO CODING EXPERT
============================
A FastAPI service that acts as a 50-year veteran systematic trading architect.
It analyses submitted automated-trading code and returns structured, battle-tested
advice on critical flaws, optimisation opportunities, risk management gaps, and
Korean-market-specific considerations.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field

from config import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — the 50-year trading expert persona
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
# Role: 50년 경력의 전설적 시스템 트레이딩 아키텍트 & 퀀트 개발 전문가

## Context
당신은 월스트리트와 여의도를 거치며 수많은 시장의 폭락과 급등을 경험한 50년 경력의 자동매매 시스템 거장입니다. \
사용자가 제출한 자동매매 코드나 전략 로직을 분석하여, 실전 매매에서 발생할 수 있는 '치명적인 결함'을 찾아내고, \
수익성보다 '생존'과 '효율' 중심의 코드 개선(Code Improvement)안을 제시해야 합니다.

## Objective
1. 사용자의 코드에서 논리적 오류(Logic Bug), 데이터 편향(Look-ahead bias), 리스크 관리 부재를 즉각 식별한다.
2. 실행 속도, 메모리 효율, API 호출 안정성 측면에서 코드를 최적화(Improve)한다.
3. 한국 시장(KOSPI/KOSDAQ)의 특수성(세금, 슬리피지, 틱 사이즈 등)을 반영한 실전적 조언을 제공한다.

## Analysis & Decision Criteria (검수 기준)
당신은 다음 5가지 핵심 지표를 기준으로 사용자의 입력을 분석합니다.
1. **Robustness (안정성):** 예외 처리(Exception Handling), 네트워크 단절 대응, API 에러 코드 처리 여부.
2. **Risk Management (리스크 관리):** 손절(Stop-loss), 익절(Take-profit), 변동성 조절, 포지션 사이징 로직의 적절성.
3. **Execution Efficiency (실행 효율):** 루프 최적화, 불필요한 연산 제거, 비동기 처리 적용 여부.
4. **Market Reality (시장 현실성):** 거래 세금, 수수료, 호가 잔량에 따른 슬리피지 반영 여부.
5. **Logic Integrity (논리적 무결성):** 미래 참조 편향(Look-ahead bias), 과적합(Overfitting) 가능성 진단.

## Output Format
모든 응답은 아래의 구조를 엄격히 따릅니다.

---
### 1. 🔍 치명적 결함 진단 (Critical Audit)
- 현재 코드에서 즉시 수정하지 않으면 '계좌가 파산할 수 있는' 문제점을 불렛포인트로 제시.

### 2. 🚀 코드 최적화 제안 (Code Improvement)
- 구체적인 리팩토링 코드 스니펫 제공.
- 알고리즘 효율성(시간 복잡도) 및 API 호출 안정성 개선 방안.

### 3. 🛡️ 리스크 및 전략 보완 조언 (Strategic Advice)
- 50년 경험에 비추어 볼 때, 해당 전략이 놓치고 있는 시장의 변수 조언.
- 한국 시장 특화 로직(예: 세금 0.18% 계산, 15:20분 종가 매매 특성 등) 반영 여부.

### 4. 💡 Follow-up 질문 (Next Step)
- 시스템 완성도를 높이기 위해 사용자가 추가로 확인하거나 답변해야 할 핵심 질문 2가지.
---

## Forbidden Behavior (금지 사항)
- "코드가 괜찮아 보입니다"와 같은 막연한 칭찬 금지.
- 단순히 문법적인 수정만 제안하는 행위 금지 (반드시 '트레이딩' 관점이 포함되어야 함).
- 실전 매매에서 불가능한 이론적인 수익률에 동조하는 행위 금지.

## Follow-up Action
사용자가 코드를 제공하면, 당신은 즉시 위 기준에 따라 분석을 시작하고, \
수정이 필요한 부분에 대해 "이 코드는 시장의 변동성을 견딜 수 있겠습니까?"라는 엄격한 질문과 함께 조언을 시작하십시오.
"""

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="REST-API AUTO CODING EXPERT",
    description=(
        "50년 경력의 전설적 시스템 트레이딩 아키텍트 & 퀀트 개발 전문가 REST API. "
        "Submit your automated-trading code and receive a structured expert review."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy singleton — created once on first request to avoid startup failures when
# the API key is not yet configured.
_openai_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    """Payload sent by the caller."""

    code: str = Field(
        ...,
        min_length=10,
        description="The automated-trading source code (Python / Pine Script / etc.) to be reviewed.",
        examples=[
            "import time\nwhile True:\n    buy('005930', 10)\n    time.sleep(1)"
        ],
    )
    language: Optional[str] = Field(
        default=None,
        description="Programming language / platform of the code (e.g. 'Python', 'Pine Script').",
        examples=["Python"],
    )
    additional_context: Optional[str] = Field(
        default=None,
        description="Optional context: strategy description, target market, exchange, etc.",
        examples=["KOSPI momentum strategy using KIS API"],
    )


class AnalyzeResponse(BaseModel):
    """Structured expert analysis returned to the caller."""

    analysis: str = Field(
        ...,
        description=(
            "Full Markdown-formatted expert analysis containing: "
            "1) Critical Audit, 2) Code Improvement, 3) Strategic Advice, 4) Follow-up questions."
        ),
    )
    model: str = Field(..., description="The LLM model that produced the analysis.")
    input_tokens: int = Field(..., description="Prompt tokens consumed.")
    output_tokens: int = Field(..., description="Completion tokens consumed.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Utility"])
async def health_check() -> dict:
    """Liveness probe — returns 200 OK when the service is running."""
    return {"status": "ok"}


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    tags=["Expert Analysis"],
    summary="Analyze automated-trading code",
    description=(
        "Submit automated-trading source code and receive a structured review "
        "from the 50-year veteran trading system architect persona."
    ),
)
async def analyze_code(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Core endpoint: sends the submitted code to the LLM together with the
    expert system prompt and returns the structured analysis.
    """
    # Build the user message
    user_message_parts = []

    if request.language:
        user_message_parts.append(f"**언어/플랫폼:** {request.language}")

    if request.additional_context:
        user_message_parts.append(f"**추가 컨텍스트:** {request.additional_context}")

    user_message_parts.append(f"**제출된 코드:**\n```\n{request.code}\n```")

    user_message = "\n\n".join(user_message_parts)

    logger.info(
        "Received analysis request | language=%s | code_length=%d",
        request.language or "unspecified",
        len(request.code),
    )

    try:
        client = get_openai_client()
        response = await client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=settings.openai_max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
    except OpenAIError as exc:
        logger.error("OpenAI API error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream LLM error: {exc}",
        ) from exc

    analysis_text = response.choices[0].message.content or ""
    usage = response.usage

    logger.info(
        "Analysis complete | model=%s | input_tokens=%d | output_tokens=%d",
        response.model,
        usage.prompt_tokens if usage else 0,
        usage.completion_tokens if usage else 0,
    )

    return AnalyzeResponse(
        analysis=analysis_text,
        model=response.model,
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
    )
