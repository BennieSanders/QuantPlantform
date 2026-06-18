from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import logging
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_analysis import AiAnalysis
from app.models.backtest_record import BacktestRecord
from app.schemas.ai import AiAnalysisMode, AiAnalysisResponse


logger = logging.getLogger(__name__)


def analyze_backtest(
    backtest_id: str,
    db: Session,
    user_id: str,
    mode: AiAnalysisMode = "openai",
) -> AiAnalysisResponse | None:
    record = db.get(BacktestRecord, backtest_id)
    if record is None or record.user_id != user_id:
        return None

    settings = get_settings()
    result = _build_analysis(record, settings, mode)
    analysis = AiAnalysis(
        id=f"ai-{uuid4().hex[:10]}",
        user_id=user_id,
        backtest_id=record.id,
        provider=result.provider,
        created_at=datetime.now(UTC),
        summary=result.summary,
        risk_level=result.risk_level,
        analysis_type=result.analysis_type,
        readiness=result.readiness,
        score=result.score,
        confidence=result.confidence,
        strengths=result.strengths,
        warnings=result.warnings,
        recommendations=result.recommendations,
        fit_profile=result.fit_profile,
        avoid_profile=result.avoid_profile,
        execution_plan=result.execution_plan,
        suggested_params=result.suggested_params,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _to_response(analysis)


def list_backtest_analyses(
    backtest_id: str,
    db: Session,
    user_id: str,
    limit: int = 10,
) -> list[AiAnalysisResponse] | None:
    record = db.get(BacktestRecord, backtest_id)
    if record is None or record.user_id != user_id:
        return None
    analyses = db.scalars(
        select(AiAnalysis)
        .where(AiAnalysis.backtest_id == backtest_id, AiAnalysis.user_id == user_id)
        .order_by(AiAnalysis.created_at.desc())
        .limit(min(max(limit, 1), 50))
    ).all()
    return [_to_response(item) for item in analyses]


@dataclass
class AnalysisDraft:
    provider: str
    summary: str
    risk_level: str
    analysis_type: str
    readiness: str
    score: int
    confidence: float
    strengths: list[str]
    warnings: list[str]
    recommendations: list[str]
    fit_profile: list[str]
    avoid_profile: list[str]
    execution_plan: list[str]
    suggested_params: dict[str, int | float]
    fallback_reason: str | None = None


def _build_analysis(record: BacktestRecord, settings, mode: AiAnalysisMode) -> AnalysisDraft:
    if mode == "gemini" and settings.gemini_api_key:
        try:
            draft = _build_gemini_analysis(record, settings)
            if draft is not None:
                return draft
        except Exception as error:
            logger.warning("Gemini analysis failed and will fall back to local engine: %s", error, exc_info=True)
            return _build_local_analysis(record, fallback_reason=_format_gemini_error(error))
    if mode == "gemini" and not settings.gemini_api_key:
        return _build_local_analysis(record, fallback_reason="未配置 Gemini API key，已回退本地引擎。")
    if mode == "openai" and settings.openai_api_key:
        try:
            draft = _build_openai_analysis(record, settings)
            if draft is not None:
                return draft
        except Exception as error:
            logger.warning("OpenAI analysis failed and will fall back to local engine: %s", error, exc_info=True)
            return _build_local_analysis(record, fallback_reason=_format_openai_error(error))
    if mode == "openai" and not settings.openai_api_key:
        return _build_local_analysis(record, fallback_reason="未配置 OpenAI API key，已回退本地引擎")
    return _build_local_analysis(record)


def _format_gemini_error(error: Exception) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        response = error.response
        error_status = ""
        try:
            payload = response.json()
            error_payload = payload.get("error", {}) if isinstance(payload, dict) else {}
            error_status = str(error_payload.get("status") or "")
        except Exception:
            pass

        if response.status_code == 400:
            return "Gemini API 请求参数无效，已回退本地引擎。"
        if response.status_code in {401, 403}:
            return "Gemini API 密钥无效、受限或无权访问模型，已回退本地引擎。"
        if response.status_code == 404:
            return "Gemini API 模型不存在或当前项目不可用，已回退本地引擎。"
        if response.status_code == 429 or error_status == "RESOURCE_EXHAUSTED":
            return "Gemini API 免费额度或请求限额已用尽，已回退本地引擎。"
        return f"Gemini API 返回 HTTP {response.status_code}，已回退本地引擎。"
    if isinstance(error, httpx.TimeoutException):
        return "Gemini API 请求超时，已回退本地引擎。"
    if isinstance(error, httpx.RequestError):
        return "无法连接 Gemini API，请检查代理和网络，已回退本地引擎。"
    return "Gemini API 返回内容无法解析，已回退本地引擎。"


def _format_openai_error(error: Exception) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        response = error.response
        error_code = ""
        try:
            payload = response.json()
            error_payload = payload.get("error", {}) if isinstance(payload, dict) else {}
            error_code = str(error_payload.get("code") or error_payload.get("type") or "")
        except Exception:
            pass

        if error_code == "insufficient_quota":
            return "OpenAI API 额度不足（insufficient_quota），已回退本地引擎。请在 API 平台开通计费或充值。"
        if response.status_code == 401:
            return "OpenAI API 密钥无效或已失效，已回退本地引擎。"
        if response.status_code == 403:
            return "当前 OpenAI API 项目无权访问所选模型，已回退本地引擎。"
        if response.status_code == 404:
            return "OpenAI API 模型或接口不存在，已回退本地引擎。"
        if response.status_code == 429:
            return "OpenAI API 请求达到限额，已回退本地引擎，请稍后重试。"
        return f"OpenAI API 返回 HTTP {response.status_code}，已回退本地引擎。"
    if isinstance(error, httpx.TimeoutException):
        return "OpenAI API 请求超时，已回退本地引擎。"
    if isinstance(error, httpx.RequestError):
        return "无法连接 OpenAI API，请检查代理和网络，已回退本地引擎。"
    return "OpenAI API 返回内容无法解析，已回退本地引擎。"


def _build_local_analysis(record: BacktestRecord, fallback_reason: str | None = None) -> AnalysisDraft:
    metrics = record.metrics
    total_return = float(metrics.get("total_return", 0))
    max_drawdown = float(metrics.get("max_drawdown", 0))
    sharpe = float(metrics.get("sharpe_ratio", 0))
    win_rate = float(metrics.get("win_rate", 0))
    trade_count = int(metrics.get("trade_count", 0))
    period_days = max(
        1,
        (datetime.fromisoformat(record.end_date) - datetime.fromisoformat(record.start_date)).days + 1,
    )

    risk_level = "low"
    if max_drawdown <= -0.35 or sharpe < 0:
        risk_level = "high"
    elif max_drawdown <= -0.2 or sharpe < 1:
        risk_level = "medium"

    score = _score_analysis(total_return, max_drawdown, sharpe, win_rate, trade_count)
    confidence = _estimate_confidence(trade_count, period_days)
    analysis_type = _infer_analysis_type(record.strategy_id, win_rate, trade_count, sharpe)
    readiness = _infer_readiness(score, confidence, risk_level)
    readiness_text = _readiness_label(readiness)

    strengths: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []
    fit_profile: list[str] = []
    avoid_profile: list[str] = []
    execution_plan: list[str] = []

    if total_return > 0:
        strengths.append(f"样本期实现 {total_return:.1%} 正收益。")
    else:
        warnings.append(f"样本期收益为 {total_return:.1%}，策略尚未形成正向优势。")
    if sharpe >= 1:
        strengths.append(f"夏普比率 {sharpe:.2f}，风险调整后收益具备可用性。")
    else:
        warnings.append(f"夏普比率仅 {sharpe:.2f}，收益稳定性不足。")
    if not strengths:
        strengths.extend(
            [
                f"{record.strategy_name} 已完成结构化回测并生成可复盘分析。",
                f"已输出 {trade_count} 笔交易的风险与参数建议，便于继续迭代。",
            ]
        )
    if max_drawdown <= -0.2:
        warnings.append(f"最大回撤达到 {max_drawdown:.1%}，资金曲线承压明显。")
        recommendations.append("增加趋势过滤或降低单次资金使用比例，优先压低最大回撤。")
    if trade_count < 8:
        warnings.append(f"只有 {trade_count} 笔交易，统计样本偏少。")
        recommendations.append("扩展数据区间并进行滚动窗口验证，避免依据少量交易下结论。")
    if win_rate < 0.45:
        recommendations.append("检查盈亏比而非单独追求胜率，并增加止损或退出条件对照实验。")
    recommendations.append("使用未参与调参的时间区间做样本外验证，并比较基准买入持有收益。")
    recommendations.append("先用纸面/仿真仓位跑 2 到 4 周，再决定是否扩大到实盘。")

    fit_profile.append(_analysis_style_label(analysis_type))
    fit_profile.append(_readiness_label(readiness))
    fit_profile.append(f"样本跨度 {period_days} 天")
    fit_profile.append(f"交易次数 {trade_count} 笔")

    if analysis_type == "trend_following":
        fit_profile.extend(["适合单边或趋势延续市场", "适合低频确认后跟随"])
        avoid_profile.extend(["高噪声横盘", "长时间来回震荡"])
    elif analysis_type == "mean_reversion":
        fit_profile.extend(["适合均值回归和震荡修复", "适合高频或中频进出"])
        avoid_profile.extend(["持续单边拉升", "单边暴跌时段"])
    else:
        fit_profile.extend(["适合继续研究和对照实验", "适合作为候选策略池"])
        avoid_profile.extend(["直接实盘重仓", "单一时段过拟合判断"])

    if readiness == "limited_live":
        execution_plan.extend([
            "保持小仓位，仅在已验证时段内运行。",
            "先验证手续费和滑点敏感性，再扩大规模。",
        ])
    elif readiness == "paper":
        execution_plan.extend([
            "在仿真环境连续观察 2 周以上。",
            "做跨周期和跨区间复测，确认稳定性。",
        ])
    else:
        execution_plan.extend([
            "当前更适合研究和归因，不建议直接部署实盘。",
            "补充样本外、不同资金量和不同周期对照测试。",
        ])

    suggested_params = _suggest_params(record.strategy_id, record.params, risk_level)
    if fallback_reason:
        recommendations.insert(0, fallback_reason)
    summary = (
        f"{record.strategy_name} 在 {record.symbol} {record.timeframe} 样本中取得 "
        f"{total_return:.1%} 收益、{max_drawdown:.1%} 最大回撤和 {sharpe:.2f} 夏普比率。"
        f"AI 推荐评分 {score}/100，置信度 {confidence:.0%}，"
        f"综合判断适配阶段为 {readiness_text}。"
    )
    return AnalysisDraft(
        provider="local-quant-recommender-v2",
        summary=summary,
        risk_level=risk_level,
        analysis_type=analysis_type,
        readiness=readiness,
        score=score,
        confidence=confidence,
        strengths=strengths,
        warnings=warnings,
        recommendations=recommendations,
        fit_profile=fit_profile,
        avoid_profile=avoid_profile,
        execution_plan=execution_plan,
        suggested_params=suggested_params,
        fallback_reason=fallback_reason,
    )


def _build_analysis_prompt(record: BacktestRecord) -> dict:
    metrics = record.metrics
    return {
        "task": "You are a quantitative trading analyst. Analyze the backtest and return JSON only.",
        "requirements": {
            "summary": "1-3 concise sentences in Chinese.",
            "risk_level": ["low", "medium", "high"],
            "analysis_type": ["trend_following", "mean_reversion", "hybrid_candidate"],
            "readiness": ["limited_live", "paper", "research"],
            "score": "integer 0-100",
            "confidence": "float 0-1",
            "strengths": ["short Chinese bullet strings"],
            "warnings": ["short Chinese bullet strings"],
            "recommendations": ["actionable Chinese bullet strings"],
            "fit_profile": ["target market / regime / usage notes"],
            "avoid_profile": ["scenarios to avoid"],
            "execution_plan": ["next-step checklist items"],
            "suggested_params": "object with numeric strategy parameters",
        },
        "backtest": {
            "strategy_name": record.strategy_name,
            "strategy_id": record.strategy_id,
            "symbol": record.symbol,
            "timeframe": record.timeframe,
            "start_date": record.start_date,
            "end_date": record.end_date,
            "initial_cash": record.initial_cash,
            "params": record.params,
            "metrics": metrics,
        },
    }


def _build_gemini_analysis(record: BacktestRecord, settings) -> AnalysisDraft | None:
    prompt = _build_analysis_prompt(record)
    payload = {
        "system_instruction": {
            "parts": [
                {"text": "Return strictly valid JSON without markdown fences. Write all analysis text in Chinese."}
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": json.dumps(prompt, ensure_ascii=False)}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 4096,
        },
    }
    headers = {
        "x-goog-api-key": settings.gemini_api_key,
        "Content-Type": "application/json",
    }
    with httpx.Client(
        timeout=settings.gemini_timeout_seconds,
        base_url=settings.gemini_base_url,
        headers=headers,
    ) as client:
        last_error: httpx.HTTPStatusError | None = None
        for model in _gemini_model_candidates(settings.gemini_model, settings.gemini_fallback_models):
            response = client.post(f"/models/{model}:generateContent", json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                last_error = error
                if response.status_code in {400, 401, 403}:
                    raise
                logger.warning("Gemini model %s failed, trying fallback model if available: %s", model, error)
                continue

            data = response.json()
            text = _extract_gemini_text(data)
            if not text:
                continue

            parsed = _safe_json_loads(text)
            if not isinstance(parsed, dict):
                continue
            return _normalize_analysis_draft(parsed, record, f"gemini:{model}")

    if last_error is not None:
        raise last_error
    return None


def _gemini_model_candidates(primary_model: str, fallback_models: tuple[str, ...]) -> list[str]:
    models: list[str] = []
    for model in (primary_model, *fallback_models):
        normalized = model.strip()
        if normalized and normalized not in models:
            models.append(normalized)
    return models


def _extract_gemini_text(payload: dict) -> str:
    chunks: list[str] = []
    for candidate in payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def _build_openai_analysis(record: BacktestRecord, settings) -> AnalysisDraft | None:
    prompt = _build_analysis_prompt(record)
    payload = {
        "model": settings.openai_model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Return strictly valid JSON without markdown fences.",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(prompt, ensure_ascii=False),
                    }
                ],
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=settings.openai_timeout_seconds, base_url=settings.openai_base_url, headers=headers) as client:
        response = client.post("/responses", json=payload)
        response.raise_for_status()
        data = response.json()

    text = _extract_openai_text(data)
    if not text:
        return None

    parsed = _safe_json_loads(text)
    if not isinstance(parsed, dict):
        return None

    draft = _normalize_analysis_draft(parsed, record, f"openai:{settings.openai_model}")
    return draft


def _extract_openai_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"].strip()

    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def _safe_json_loads(value: str) -> object:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
        if cleaned.lstrip().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def _normalize_analysis_draft(payload: dict, record: BacktestRecord, provider: str) -> AnalysisDraft:
    risk_level = _normalize_choice(payload.get("risk_level"), {"low", "medium", "high"}, "medium")
    analysis_type = _normalize_choice(
        payload.get("analysis_type"),
        {"trend_following", "mean_reversion", "hybrid_candidate"},
        "hybrid_candidate",
    )
    readiness = _normalize_choice(
        payload.get("readiness"),
        {"limited_live", "paper", "research"},
        "research",
    )
    score = _normalize_int(payload.get("score"), 0, 100, 50)
    confidence = _normalize_float(payload.get("confidence"), 0.0, 1.0, 0.5)
    strengths = _normalize_list(payload.get("strengths"))
    warnings = _normalize_list(payload.get("warnings"))
    recommendations = _normalize_list(payload.get("recommendations"))
    fit_profile = _normalize_list(payload.get("fit_profile"))
    avoid_profile = _normalize_list(payload.get("avoid_profile"))
    execution_plan = _normalize_list(payload.get("execution_plan"))
    suggested_params = _normalize_mapping(payload.get("suggested_params"))

    summary = str(payload.get("summary") or "").strip()
    if not summary:
        summary = (
            f"{record.strategy_name} 在 {record.symbol} {record.timeframe} 样本中呈现 "
            f"{risk_level} 风险特征，推荐评分 {score}/100。"
        )
    if not strengths:
        strengths = _default_strengths(record, suggested_params, score)
    if not warnings:
        warnings = _default_warnings(record, risk_level)
    if not recommendations:
        recommendations = _default_recommendations(record, readiness)
    if not fit_profile:
        fit_profile = _default_fit_profile(record, analysis_type, readiness)
    if not avoid_profile:
        avoid_profile = _default_avoid_profile(record, analysis_type)
    if not execution_plan:
        execution_plan = _default_execution_plan(readiness)

    return AnalysisDraft(
        provider=provider,
        summary=summary,
        risk_level=risk_level,
        analysis_type=analysis_type,
        readiness=readiness,
        score=score,
        confidence=confidence,
        strengths=strengths,
        warnings=warnings,
        recommendations=recommendations,
        fit_profile=fit_profile,
        avoid_profile=avoid_profile,
        execution_plan=execution_plan,
        suggested_params=suggested_params,
    )


def _default_strengths(record: BacktestRecord, suggested_params: dict[str, int | float], score: int) -> list[str]:
    items = [
        f"{record.strategy_name} 已完成结构化回测评分 {score}/100。",
        f"已生成可执行参数建议，共 {len(suggested_params)} 项。",
    ]
    return items


def _default_warnings(record: BacktestRecord, risk_level: str) -> list[str]:
    return [
        f"{record.symbol} {record.timeframe} 当前判定为 {risk_level} 风险。",
        "请结合样本外区间和不同资金量再验证。",
    ]


def _default_recommendations(record: BacktestRecord, readiness: str) -> list[str]:
    return [
        f"当前落地阶段为 { _readiness_label(readiness) }。",
        "先进行纸面验证，再考虑小仓位运行。",
    ]


def _default_fit_profile(record: BacktestRecord, analysis_type: str, readiness: str) -> list[str]:
    return [
        _analysis_style_label(analysis_type),
        _readiness_label(readiness),
        f"{record.symbol} / {record.timeframe}",
    ]


def _default_avoid_profile(record: BacktestRecord, analysis_type: str) -> list[str]:
    if analysis_type == "trend_following":
        return ["高噪声横盘", "频繁反转区间"]
    if analysis_type == "mean_reversion":
        return ["持续单边趋势", "极端波动时段"]
    return ["直接重仓实盘", "单一时段过拟合"]


def _default_execution_plan(readiness: str) -> list[str]:
    if readiness == "limited_live":
        return ["小仓位试运行", "监控滑点和手续费"]
    if readiness == "paper":
        return ["纸面验证 2 周以上", "做跨周期复测"]
    return ["继续研究", "补充样本外验证"]


def _normalize_choice(value: object, allowed: set[str], default: str) -> str:
    if isinstance(value, str) and value in allowed:
        return value
    return default


def _normalize_int(value: object, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(float(value))
    except Exception:
        return default
    return max(minimum, min(maximum, number))


def _normalize_float(value: object, minimum: float, maximum: float, default: float) -> float:
    try:
        number = float(value)
    except Exception:
        return default
    return round(max(minimum, min(maximum, number)), 2)


def _normalize_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable) and not isinstance(value, dict):
        return [str(item) for item in value if str(item).strip()]
    return []


def _normalize_mapping(value: object) -> dict[str, int | float]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, int | float] = {}
    for key, item in value.items():
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            normalized[str(key)] = item
        elif isinstance(item, float):
            normalized[str(key)] = round(item, 4)
        else:
            try:
                number = float(item)
            except Exception:
                continue
            normalized[str(key)] = int(number) if number.is_integer() else round(number, 4)
    return normalized


def _score_analysis(
    total_return: float,
    max_drawdown: float,
    sharpe: float,
    win_rate: float,
    trade_count: int,
) -> int:
    score = 50.0
    score += min(max(total_return * 120, -18), 22)
    score += min(max(sharpe * 10, -20), 20)
    score += min(max(win_rate * 18 - 9, -10), 10)
    score += min(max(10 + max_drawdown * 35, -15), 10)
    if trade_count >= 20:
        score += 8
    elif trade_count >= 8:
        score += 4
    else:
        score -= 6
    return max(0, min(100, round(score)))


def _estimate_confidence(trade_count: int, period_days: int) -> float:
    trade_factor = min(trade_count / 20, 1.0)
    period_factor = min(period_days / 180, 1.0)
    return round(0.35 + trade_factor * 0.35 + period_factor * 0.3, 2)


def _infer_analysis_type(strategy_id: str, win_rate: float, trade_count: int, sharpe: float) -> str:
    if strategy_id == "rsi-reversal-default" or (trade_count >= 14 and win_rate >= 0.45 and sharpe < 1.4):
        return "mean_reversion"
    if strategy_id == "ma-cross-default" or sharpe >= 1.0 or trade_count <= 12:
        return "trend_following"
    return "hybrid_candidate"


def _infer_readiness(score: int, confidence: float, risk_level: str) -> str:
    if score >= 78 and confidence >= 0.75 and risk_level == "low":
        return "limited_live"
    if score >= 58 and confidence >= 0.55 and risk_level != "high":
        return "paper"
    return "research"


def _analysis_style_label(analysis_type: str) -> str:
    labels = {
        "trend_following": "趋势跟随",
        "mean_reversion": "均值回归",
        "hybrid_candidate": "混合候选",
    }
    return labels.get(analysis_type, analysis_type)


def _readiness_label(readiness: str) -> str:
    labels = {
        "limited_live": "可小仓位试运行",
        "paper": "适合纸面验证",
        "research": "仍处研究阶段",
    }
    return labels.get(readiness, readiness)


def _suggest_params(strategy_id: str, params: dict, risk_level: str) -> dict[str, int | float]:
    if strategy_id == "ma-cross-default" or "short_window" in params:
        short_window = int(params.get("short_window", 7))
        long_window = int(params.get("long_window", 30))
        if risk_level in {"medium", "high"}:
            return {
                "short_window": max(3, short_window + 2),
                "long_window": max(long_window + 5, short_window + 3),
            }
        return {
            "short_window": max(3, short_window - 1),
            "long_window": max(long_window, short_window + 2),
        }
    if strategy_id == "rsi-reversal-default" or "period" in params:
        period = int(params.get("period", 14))
        return {
            "period": period + 2 if risk_level in {"medium", "high"} else period,
            "oversold": max(1, int(params.get("oversold", 30)) - 2),
            "overbought": min(99, int(params.get("overbought", 70)) + 2),
        }
    return {}


def _to_response(analysis: AiAnalysis) -> AiAnalysisResponse:
    return AiAnalysisResponse(
        id=analysis.id,
        backtest_id=analysis.backtest_id,
        provider=analysis.provider,
        summary=analysis.summary,
        risk_level=analysis.risk_level,
        analysis_type=analysis.analysis_type,
        readiness=analysis.readiness,
        score=analysis.score,
        confidence=analysis.confidence,
        strengths=analysis.strengths,
        warnings=analysis.warnings,
        recommendations=analysis.recommendations,
        fit_profile=analysis.fit_profile,
        avoid_profile=analysis.avoid_profile,
        execution_plan=analysis.execution_plan,
        suggested_params=analysis.suggested_params,
        created_at=analysis.created_at.isoformat(),
    )
