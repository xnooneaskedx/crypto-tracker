import requests
import json
from config import API_KEY, BASE_URL

def get_global_metrics():
    """
    获取全球加密货币市场指标
    """
    url = f"{BASE_URL}/v1/global-metrics/quotes/latest"

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"获取全球市场数据失败: {e}")
        return None

def get_top_cryptocurrencies(limit=10, sort='market_cap', convert='USD'):
    """
    获取排名前几位的加密货币
    :param limit: 获取数量(默认10)
    :param sort: 排序方式(market_cap, percent_change_24h等)
    :param convert: 转换货币(USD, EUR, CNY等)
    :return: 加密货币列表
    """
    url = f"{BASE_URL}/v1/cryptocurrency/listings/latest"

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }

    parameters = {
        'start': '1',
        'limit': str(limit),
        'sort': sort,
        'sort_dir': 'desc',
        'convert': convert
    }

    try:
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"获取加密货币列表失败: {e}")
        return None

def get_cryptocurrency_info(symbol, convert='USD'):
    """
    获取特定加密货币的详细信息
    :param symbol: 加密货币符号(BTC, ETH等)
    :param convert: 转换货币
    :return: 加密货币信息
    """
    url = f"{BASE_URL}/v1/cryptocurrency/quotes/latest"

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }

    parameters = {
        'symbol': symbol.upper(),
        'convert': convert
    }

    try:
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"获取{symbol}信息失败: {e}")
        return None

def parse_crypto_data(data):
    """
    解析加密货币数据
    :param data: API返回的原始数据
    :return: 格式化后的数据列表
    """
    if not data or 'data' not in data:
        return None

    crypto_list = []

    # 处理列表数据
    if isinstance(data['data'], list):
        for item in data['data']:
            crypto_info = {
                'name': item['name'],
                'symbol': item['symbol'],
                'price': item['quote']['USD']['price'],
                'market_cap': item['quote']['USD']['market_cap'],
                'volume_24h': item['quote']['USD']['volume_24h'],
                'percent_change_24h': item['quote']['USD']['percent_change_24h'],
                'percent_change_7d': item['quote']['USD'].get('percent_change_7d', 0)
            }
            crypto_list.append(crypto_info)
    # 处理单个货币数据
    else:
        for symbol, item in data['data'].items():
            crypto_info = {
                'name': item['name'],
                'symbol': item['symbol'],
                'price': item['quote']['USD']['price'],
                'market_cap': item['quote']['USD']['market_cap'],
                'volume_24h': item['quote']['USD']['volume_24h'],
                'percent_change_24h': item['quote']['USD']['percent_change_24h'],
                'percent_change_7d': item['quote']['USD'].get('percent_change_7d', 0)
            }
            crypto_list.append(crypto_info)

    return crypto_list
def analyze_investment_opportunity(crypto_data, investment_amount=1000):
    """
    分析加密货币投资机会
    注意: 这只是教育性分析，不构成投资建议
    :param crypto_data: 加密货币数据
    :param investment_amount: 投资金额(USD)
    :return: 投资分析结果
    """
    if not crypto_data:
        return None

    try:
        name = crypto_data['name']
        symbol = crypto_data['symbol']
        price = crypto_data['price']
        change_24h = crypto_data['percent_change_24h']
        change_7d = crypto_data['percent_change_7d']
        volume_24h = crypto_data['volume_24h']
        market_cap = crypto_data['market_cap']

        # 计算分析指标
        analysis = {
            'name': name,
            'symbol': symbol,
            'current_price': price,
            'recommendation': '',
            'recommended_amount': 0,
            'risk_level': '',
            'factors': []
        }

        # 1. 趋势分析
        if change_24h > 5 and change_7d > 10:
            trend = "强势上涨"
            analysis['factors'].append("短期和中期趋势强劲")
        elif change_24h > 0 and change_7d > 0:
            trend = "温和上涨"
            analysis['factors'].append("趋势稳定向好")
        elif change_24h < 0 and change_7d < 0:
            trend = "下跌趋势"
            analysis['factors'].append("短期和中期趋势疲软")
        else:
            trend = "震荡"
            analysis['factors'].append("价格波动较大")

        # 2. 风险评估
        volatility = abs(change_24h) + abs(change_7d)
        if volatility > 20:
            risk_level = "高风险"
            analysis['risk_level'] = "高风险"
            analysis['factors'].append("价格波动性较大")
        elif volatility > 10:
            risk_level = "中等风险"
            analysis['risk_level'] = "中等风险"
            analysis['factors'].append("价格波动性适中")
        else:
            risk_level = "低风险"
            analysis['risk_level'] = "低风险"
            analysis['factors'].append("价格相对稳定")

        # 3. 投资建议算法
        score = 0

        # 趋势得分
        if change_24h > 5:
            score += 3
        elif change_24h > 0:
            score += 1
        elif change_24h < -5:
            score -= 3
        elif change_24h < 0:
            score -= 1

        if change_7d > 10:
            score += 3
        elif change_7d > 0:
            score += 1
        elif change_7d < -10:
            score -= 3
        elif change_7d < 0:
            score -= 1

        # 根据得分给出建议
        if score >= 5:
            analysis['recommendation'] = "积极关注"
            analysis['recommended_amount'] = min(investment_amount * 0.3, 500)  # 最多30%或500美元
        elif score >= 2:
            analysis['recommendation'] = "适度关注"
            analysis['recommended_amount'] = min(investment_amount * 0.1, 200)  # 最多10%或200美元
        elif score >= -1:
            analysis['recommendation'] = "观察等待"
            analysis['recommended_amount'] = min(investment_amount * 0.05, 100)  # 最多5%或100美元
        else:
            analysis['recommendation'] = "谨慎观望"
            analysis['recommended_amount'] = 0

        # 4. 添加风险提示
        analysis['disclaimer'] = "⚠️ 重要提示: 这只是基于技术指标的教育性分析，不构成投资建议。加密货币投资存在高风险，请谨慎决策。"

        return analysis

    except (KeyError, TypeError) as e:
        print(f"数据分析错误: {e}")
        return None
