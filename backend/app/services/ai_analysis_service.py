from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AiAnalysis
from app.models.backtest_record import BacktestRecord
from app.schemas.ai import AiAnalysisResponse


def analyze_backtest(backtest_id: str, db: Session, user_id: str) -> AiAnalysisResponse | None:
    record = db.get(BacktestRecord, backtest_id)
    if record is None or record.user_id != user_id:
        return None

    result = _build_local_analysis(record)
    analysis = AiAnalysis(
        id=f"ai-{uuid4().hex[:10]}",
        user_id=user_id,
        backtest_id=record.id,
        provider="local-quant-analyst-v1",
        created_at=datetime.now(UTC),
        **result,
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


def _build_local_analysis(record: BacktestRecord) -> dict:
    metrics = record.metrics
    total_return = float(metrics.get("total_return", 0))
    max_drawdown = float(metrics.get("max_drawdown", 0))
    sharpe = float(metrics.get("sharpe_ratio", 0))
    win_rate = float(metrics.get("win_rate", 0))
    trade_count = int(metrics.get("trade_count", 0))

    risk_level = "low"
    if max_drawdown <= -0.35 or sharpe < 0:
        risk_level = "high"
    elif max_drawdown <= -0.2 or sharpe < 1:
        risk_level = "medium"

    strengths: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if total_return > 0:
        strengths.append(f"样本期实现 {total_return:.1%} 正收益。")
    else:
        warnings.append(f"样本期收益为 {total_return:.1%}，策略尚未形成正向优势。")
    if sharpe >= 1:
        strengths.append(f"夏普比率 {sharpe:.2f}，风险调整后收益具备可用性。")
    else:
        warnings.append(f"夏普比率仅 {sharpe:.2f}，收益稳定性不足。")
    if max_drawdown <= -0.2:
        warnings.append(f"最大回撤达到 {max_drawdown:.1%}，资金曲线承压明显。")
        recommendations.append("增加趋势过滤或降低单次资金使用比例，优先压低最大回撤。")
    if trade_count < 8:
        warnings.append(f"只有 {trade_count} 笔交易，统计样本偏少。")
        recommendations.append("扩展数据区间并进行滚动窗口验证，避免依据少量交易下结论。")
    if win_rate < 0.45:
        recommendations.append("检查盈亏比而非单独追求胜率，并增加止损或退出条件对照实验。")
    recommendations.append("使用未参与调参的时间区间做样本外验证，并比较基准买入持有收益。")

    suggested_params = _suggest_params(record.strategy_id, record.params, risk_level)
    summary = (
        f"{record.strategy_name} 在 {record.symbol} {record.timeframe} 样本中取得 "
        f"{total_return:.1%} 收益、{max_drawdown:.1%} 最大回撤和 {sharpe:.2f} 夏普比率。"
        f"综合判断风险等级为 {risk_level}，建议先验证稳健性，再决定是否扩大资金。"
    )
    return {
        "summary": summary,
        "risk_level": risk_level,
        "strengths": strengths,
        "warnings": warnings,
        "recommendations": recommendations,
        "suggested_params": suggested_params,
    }


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
        strengths=analysis.strengths,
        warnings=analysis.warnings,
        recommendations=analysis.recommendations,
        suggested_params=analysis.suggested_params,
        created_at=analysis.created_at.isoformat(),
    )
