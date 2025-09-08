import requests
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from config import API_KEY, BASE_URL

# 尝试导入数据库函数
try:
    from database import save_crypto_data
except ImportError:
    save_crypto_data = None
    print("警告: 无法导入save_crypto_data函数")

# -------------------- 基础配置与工具 -------------------- #
DEFAULT_TIMEOUT = 10  # 秒
USER_AGENT = "crypto-dashboard/1.0 (+https://example.local)"

def _get_api_key() -> str:
    """优先使用环境变量，其次使用 config.py"""
    return os.getenv("CMC_API_KEY") or API_KEY

def _get_base_url() -> str:
    """允许通过环境变量覆盖 BASE_URL"""
    return (os.getenv("CMC_BASE_URL") or BASE_URL or "").rstrip("/")

def validate_config() -> bool:
    """验证配置是否正确"""
    api_key = _get_api_key()
    base_url = _get_base_url()
    if not api_key or api_key == "your_coinmarketcap_api_key_here":
        print("错误: 请在config.py或环境变量 CMC_API_KEY 中设置有效的API密钥")
        return False
    if not base_url.startswith("http"):
        print("错误: 请在config.py或环境变量 CMC_BASE_URL 中设置有效的 BASE_URL，例如 https://pro-api.coinmarketcap.com")
        return False
    return True

def _headers() -> Dict[str, str]:
    return {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": _get_api_key(),
        "User-Agent": USER_AGENT,
    }

def _cmc_request(path: str, params: Optional[Dict[str, Any]] = None, timeout: int = DEFAULT_TIMEOUT) -> Optional[Dict[str, Any]]:
    """
    统一的请求封装：超时、错误码、JSON解析与错误信息回传
    """
    if not validate_config():
        return None

    base = _get_base_url()
    url = f"{base}{path if path.startswith('/') else '/' + path}"

    try:
        resp = requests.get(url, headers=_headers(), params=params or {}, timeout=timeout)
        # 常见状态码友好提示
        if resp.status_code == 400:
            print("请求参数错误(400)。")
            return None
        if resp.status_code == 401:
            print("API 密钥无效(401)。")
            return None
        if resp.status_code == 403:
            print("权限不足或IP受限(403)。")
            return None
        if resp.status_code == 429:
            print("频率限制(429)：API调用次数超限，请稍后再试。")
            return None
        if 500 <= resp.status_code < 600:
            print(f"服务端错误({resp.status_code})：{resp.text[:200]}")
            return None

        resp.raise_for_status()

        try:
            data = resp.json()
        except ValueError:
            print("JSON解析失败：响应非JSON。")
            return None

        # CMC 的业务层 status 检查
        status = data.get("status", {})
        if status.get("error_code", 0) != 0:
            code = status.get("error_code")
            msg = status.get("error_message", "Unknown error")
            print(f"CMC业务错误：code={code}, message={msg}")
            return None

        return data

    except requests.exceptions.Timeout:
        print("请求超时，请稍后再试。")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"网络连接错误，请检查网络设置: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

# -------------------- 对外函数 -------------------- #
def get_global_metrics() -> Optional[Dict[str, Any]]:
    """
    获取全球加密货币市场指标
    """
    data = _cmc_request("/v1/global-metrics/quotes/latest")
    return data

def get_top_cryptocurrencies(limit: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    获取排名前几位的加密货币
    :param limit: 获取数量(默认10)
    :return: 解析后的加密货币列表
    """
    limit = int(limit) if isinstance(limit, (int, float, str)) else 10
    if limit <= 0:
        limit = 10

    params = {
        "start": "1",
        "limit": str(limit),
        "sort": "market_cap",
        "sort_dir": "desc",
        "convert": "USD",
    }

    raw = _cmc_request("/v1/cryptocurrency/listings/latest", params)
    if not raw:
        return None

    try:
        return parse_crypto_data(raw)
    except Exception as e:
        print(f"解析加密货币列表失败: {e}")
        return None

def get_cryptocurrency_info(symbol: str) -> Optional[Dict[str, Any]]:
    """
    获取特定加密货币的详细信息
    :param symbol: 加密货币符号(BTC, ETH等)
    :return: 加密货币信息或None
    """
    if not symbol or not isinstance(symbol, str):
        print("错误: 请输入有效的加密货币符号")
        return None

    params = {
        "symbol": symbol.upper().strip(),
        "convert": "USD",
    }

    data = _cmc_request("/v1/cryptocurrency/quotes/latest", params, timeout=DEFAULT_TIMEOUT)
    if not data:
        return None

    # 解析数据
    crypto_info = parse_single_crypto_data(data)

    # 保存到数据库（如果获取到数据且函数可用）
    if crypto_info and save_crypto_data:
        try:
            save_crypto_data(crypto_info)
        except Exception as e:
            # 保存失败不应影响接口使用
            print(f"保存到数据库失败: {e}")

    return crypto_info

def get_historical_prices(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
    """
    获取加密货币历史价格数据（尽力而为）
    注意: CoinMarketCap 免费计划通常不提供 OHLCV 历史数据。
    本函数会尝试调用 /v2/cryptocurrency/ohlcv/historical（需要相应权限），
    若权限不足/失败，则返回空列表。
    :param symbol: 加密货币符号
    :param days: 天数
    :return: [{'timestamp': datetime, 'price': float}, ...]
    """
    symbol = (symbol or "").upper().strip()
    days = int(days) if isinstance(days, (int, float, str)) else 30
    if days <= 0:
        days = 30

    # 计算时间范围（UTC）
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    params = {
        "symbol": symbol,
        "convert": "USD",
        "time_start": int(start.timestamp()),
        "time_end": int(end.timestamp()),
        "count": days,
        "interval": "daily",  # 可用: daily, hourly 等（取决于权限）
    }

    data = _cmc_request("/v2/cryptocurrency/ohlcv/historical", params, timeout=DEFAULT_TIMEOUT)
    if not data:
        # 回退：免费不可用时返回空
        print("注意: 免费API/权限不足，无法获取历史价格数据，返回空列表。")
        return []

    try:
        points = []
        quotes = (data.get("data", {}) or {}).get("quotes", []) or []
        for q in quotes:
            t = q.get("time_open") or q.get("time_close") or q.get("timestamp")
            price = ((q.get("quote") or {}).get("USD") or {}).get("close")
            if not (t and price is not None):
                continue
            # ISO 或 时间戳都处理
            try:
                if isinstance(t, (int, float)):
                    ts = datetime.fromtimestamp(t, tz=timezone.utc)
                else:
                    ts = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
            except Exception:
                continue
            try:
                price_f = float(price)
            except (TypeError, ValueError):
                continue
            points.append({"timestamp": ts, "price": price_f})
        return points
    except Exception as e:
        print(f"解析历史价格数据失败: {e}")
        return []

# -------------------- 解析函数 -------------------- #
def parse_single_crypto_data(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    解析单个加密货币数据
    :param data: API返回的原始数据
    :return: 格式化后的数据
    """
    if not data or "data" not in data:
        return None

    try:
        # CoinMarketCap对单个货币查询返回的是字典而不是列表
        keys = list((data.get("data") or {}).keys())
        if not keys:
            return None
        symbol_key = keys[0]
        item = data["data"][symbol_key] or {}

        quote_usd = (item.get("quote") or {}).get("USD") or {}

        crypto_info = {
            "name": item.get("name", "Unknown"),
            "symbol": item.get("symbol", "Unknown"),
            "price": quote_usd.get("price", 0) or 0,
            "market_cap": quote_usd.get("market_cap", 0) or 0,
            "volume_24h": quote_usd.get("volume_24h", 0) or 0,
            "percent_change_1h": quote_usd.get("percent_change_1h", 0) or 0,
            "percent_change_24h": quote_usd.get("percent_change_24h", 0) or 0,
            "percent_change_7d": quote_usd.get("percent_change_7d", 0) or 0,
            "circulating_supply": item.get("circulating_supply", 0) or 0,
            "max_supply": item.get("max_supply", 0) or 0,
        }
        return crypto_info
    except (KeyError, IndexError, TypeError) as e:
        print(f"数据解析错误: {e}")
        return None

def parse_crypto_data(data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    解析加密货币数据
    :param data: API返回的原始数据
    :return: 格式化后的数据列表
    """
    if not data or "data" not in data:
        print("返回数据格式错误：缺少'data'字段")
        return None

    arr = data["data"]
    if not isinstance(arr, list):
        print("数据格式不符合预期（应为列表）。")
        return None

    crypto_list: List[Dict[str, Any]] = []
    for i, item in enumerate(arr):
        try:
            quote_usd = (item.get("quote") or {}).get("USD") or {}
            crypto_info = {
                "name": item.get("name", "Unknown"),
                "symbol": item.get("symbol", "Unknown"),
                "price": quote_usd.get("price", 0) or 0,
                "market_cap": quote_usd.get("market_cap", 0) or 0,
                "volume_24h": quote_usd.get("volume_24h", 0) or 0,
                "percent_change_24h": quote_usd.get("percent_change_24h", 0) or 0,
                "percent_change_7d": quote_usd.get("percent_change_7d", 0) or 0,
            }
            crypto_list.append(crypto_info)
        except (KeyError, TypeError) as e:
            print(f"解析第{i+1}项数据时出错: {e}")
            continue

    return crypto_list

# -------------------- 分析函数 -------------------- #
def enhanced_investment_analysis(
    crypto_data: Dict[str, Any],
    user_risk_level: str = "medium",
    investment_budget: Union[int, float] = 1000,
) -> Optional[Dict[str, Any]]:
    """
    增强版投资分析 - 提供具体的买入/卖出建议和投资金额
    :param crypto_data: 加密货币数据
    :param user_risk_level: 用户风险偏好 ('low', 'medium', 'high')
    :param investment_budget: 投资预算
    :return: 详细的投资分析报告
    """
    if not crypto_data:
        return None

    try:
        # 提取关键数据
        name = crypto_data.get("name")
        symbol = crypto_data.get("symbol")
        price = float(crypto_data.get("price", 0) or 0)
        change_24h = float(crypto_data.get("percent_change_24h", 0) or 0)
        change_7d = float(crypto_data.get("percent_change_7d", 0) or 0)
        market_cap = float(crypto_data.get("market_cap", 0) or 0)
        volume_24h = float(crypto_data.get("volume_24h", 0) or 0)

        # 计算分析指标
        analysis = {
            "name": name,
            "symbol": symbol,
            "current_price": price,
            "action": "HOLD",  # BUY, SELL, HOLD
            "confidence": 0,   # 信心指数 0-100
            "investment_range": {"min": 0, "max": 0, "recommended": 0},
            "target_prices": {"take_profit": 0, "stop_loss": 0},
            "timeframe": "短期",  # 短期/中期/长期
            "risk_level": "中等",
            "factors": [],
            "technical_signals": [],
        }

        # 1. 技术分析信号
        if change_24h > 5 and change_7d > 10:
            analysis["technical_signals"].append("买入信号: 强势上涨")
            trend_score = 5
        elif change_24h > 2 and change_7d > 5:
            analysis["technical_signals"].append("持有信号: 稳定上涨")
            trend_score = 3
        elif change_24h < -5 and change_7d < -10:
            analysis["technical_signals"].append("卖出信号: 强烈下跌")
            trend_score = -5
        elif change_24h < -2 and change_7d < -5:
            analysis["technical_signals"].append("观望信号: 温和下跌")
            trend_score = -3
        else:
            analysis["technical_signals"].append("持有信号: 震荡行情")
            trend_score = 0

        # 成交量分析
        volume_ratio = (volume_24h / market_cap) if market_cap > 0 else 0
        if volume_ratio > 0.1:
            analysis["technical_signals"].append("确认信号: 高成交量确认趋势")

        # 2. 风险评估
        volatility = abs(change_24h) + abs(change_7d)
        if volatility > 25:
            analysis["risk_level"] = "高风险"
            analysis["factors"].append("高波动性")
        elif volatility > 15:
            analysis["risk_level"] = "中等风险"
            analysis["factors"].append("中等波动性")
        else:
            analysis["risk_level"] = "低风险"
            analysis["factors"].append("低波动性")

        # 3. 市值分析
        if market_cap > 50_000_000_000:
            analysis["factors"].append("大盘，相对稳定")
            mc_score = 3
        elif market_cap > 10_000_000_000:
            analysis["factors"].append("中盘，稳定性适中")
            mc_score = 1
        else:
            analysis["factors"].append("小盘，高风险高收益")
            mc_score = -2

        # 4. 评分
        score = 0

        # 短期变化评分
        if change_24h > 10:
            score += 5
        elif change_24h > 5:
            score += 3
        elif change_24h > 0:
            score += 1
        elif change_24h < -10:
            score -= 5
        elif change_24h < -5:
            score -= 3
        elif change_24h < 0:
            score -= 1

        # 7日变化评分
        if change_7d > 15:
            score += 5
        elif change_7d > 10:
            score += 3
        elif change_7d > 0:
            score += 1
        elif change_7d < -15:
            score -= 5
        elif change_7d < -10:
            score -= 3
        elif change_7d < 0:
            score -= 1

        # 市值、成交量评分
        score += mc_score
        if volume_ratio > 0.1:
            score += 2
        elif volume_ratio > 0.05:
            score += 1

        # 趋势微调
        score += trend_score

        analysis["confidence"] = max(0, min(100, int(abs(score) * 10)))

        # 5. 买卖决策
        if score >= 8:
            analysis["action"] = "BUY"
            analysis["timeframe"] = "短期"
        elif score >= 4:
            analysis["action"] = "BUY"
            analysis["timeframe"] = "中期"
        elif score >= -3:
            analysis["action"] = "HOLD"
            analysis["timeframe"] = "短期"
        elif score >= -7:
            analysis["action"] = "SELL"
            analysis["timeframe"] = "短期"
        else:
            analysis["action"] = "SELL"
            analysis["timeframe"] = "立即"

        # 6. 投资金额建议
        try:
            budget = float(investment_budget)
        except (TypeError, ValueError):
            budget = 1000.0

        risk_multiplier = {"low": 0.5, "medium": 1.0, "high": 1.5}
        base_investment = max(0.0, budget) * risk_multiplier.get(user_risk_level, 1.0)

        if analysis["action"] == "BUY":
            if score >= 8:  # 强烈买入
                analysis["investment_range"] = {
                    "min": base_investment * 0.3,
                    "max": base_investment * 0.7,
                    "recommended": base_investment * 0.5,
                }
            elif score >= 4:  # 买入
                analysis["investment_range"] = {
                    "min": base_investment * 0.2,
                    "max": base_investment * 0.5,
                    "recommended": base_investment * 0.3,
                }
            else:  # 持有
                analysis["investment_range"] = {
                    "min": 0,
                    "max": base_investment * 0.2,
                    "recommended": base_investment * 0.1,
                }
        elif analysis["action"] == "SELL":
            analysis["investment_range"] = {"min": 0, "max": 0, "recommended": 0}
        else:  # HOLD
            analysis["investment_range"] = {
                "min": 0,
                "max": base_investment * 0.3,
                "recommended": base_investment * 0.1,
            }

        # 7. 目标价格计算（保护上下限）
        def clamp(v: float, lo: float, hi: float) -> float:
            return max(lo, min(hi, v))

        if analysis["action"] == "BUY":
            tp = price * (1 + clamp(score * 0.03, 0.0, 0.2))   # take profit ≤ +20%
            sl = price * (1 - clamp(abs(score) * 0.02, 0.0, 0.1))  # stop loss ≤ -10%
        elif analysis["action"] == "SELL":
            tp = price * (1 - clamp(abs(score) * 0.02, 0.0, 0.1))
            sl = price * (1 + clamp(abs(score) * 0.01, 0.0, 0.05))
        else:
            tp = price * 1.10
            sl = price * 0.90

        analysis["target_prices"] = {"take_profit": tp, "stop_loss": sl}

        # 8. 风险提示
        analysis["disclaimer"] = "⚠️ 重要提示: 此分析仅供参考，不构成投资建议。加密货币投资存在高风险，请根据自身风险承受能力谨慎决策。"

        return analysis

    except (KeyError, TypeError, ValueError) as e:
        print(f"数据分析错误: {e}")
        return None

def analyze_portfolio_opportunities(investment_budget: Union[int, float] = 1000, risk_level: str = "medium") -> List[Dict[str, Any]]:
    """
    分析投资组合机会 - 为用户提供最佳投资建议
    :param investment_budget: 投资预算
    :param risk_level: 风险偏好
    :return: 投资机会列表
    """
    try:
        top_cryptos = get_top_cryptocurrencies(20)
        if not top_cryptos:
            return []

        opportunities: List[Dict[str, Any]] = []
        for crypto in top_cryptos:
            analysis = enhanced_investment_analysis(crypto, risk_level, investment_budget)
            if analysis and (analysis.get("investment_range", {}).get("recommended", 0) or 0) > 0:
                opportunities.append(analysis)

        # 按推荐投资金额排序
        opportunities.sort(key=lambda x: x["investment_range"]["recommended"], reverse=True)

        return opportunities[:10]  # 返回前10个机会

    except Exception as e:
        print(f"投资机会分析错误: {e}")
        return []
