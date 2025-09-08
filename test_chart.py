import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import io
import base64

def test_price_chart():
    """测试价格图表生成"""
    # 生成测试数据
    dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
    prices = [50000 + np.random.normal(0, 1000) + i*100 for i in range(30)]

    # 创建图表
    plt.style.use('default')  # 使用默认样式，seaborn-v0_8可能不存在
    fig, ax = plt.subplots(figsize=(10, 6))

    # 绘制价格线
    ax.plot(dates, prices, linewidth=2, color='#007bff', marker='o', markersize=4)

    # 设置标题和标签
    ax.set_title('BTC 价格趋势图', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('价格 (USD)', fontsize=12)

    # 格式化x轴日期
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # 添加网格
    ax.grid(True, alpha=0.3)

    # 调整布局
    plt.tight_layout()

    # 显示图表
    plt.show()

    # 或者保存为文件
    plt.savefig('test_chart.png', dpi=100, bbox_inches='tight')
    print("图表已保存为 test_chart.png")

    # 清理内存
    plt.close(fig)

def generate_price_chart(symbol, history_data):
    """
    生成价格图表
    :param symbol: 货币符号
    :param history_data: 历史数据
    :return: 图表的base64编码
    """
    try:
        if not history_data or len(history_data) == 0:
            return None

        # 准备数据
        dates = []
        prices = []

        # 从最新的数据开始（倒序处理）
        for record in reversed(history_data):
            try:
                # 解析时间戳
                timestamp = record['timestamp']
                if isinstance(timestamp, str):
                    # 处理不同的时间格式
                    if 'T' in timestamp:
                        # 移除Z并添加时区信息
                        if timestamp.endswith('Z'):
                            timestamp = timestamp[:-1] + '+00:00'
                        date_obj = datetime.fromisoformat(timestamp)
                    else:
                        date_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                else:
                    date_obj = timestamp

                dates.append(date_obj)
                prices.append(float(record['price']))
            except (ValueError, KeyError) as e:
                print(f"解析数据时出错: {e}")
                continue

        if len(dates) == 0 or len(prices) == 0:
            return None

        # 创建图表
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))

        # 绘制价格线
        ax.plot(dates, prices, linewidth=2, color='#007bff', marker='o', markersize=4)

        # 设置标题和标签
        ax.set_title(f'{symbol} 价格趋势图', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('价格 (USD)', fontsize=12)

        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # 添加网格
        ax.grid(True, alpha=0.3)

        # 调整布局
        plt.tight_layout()

        # 保存为内存中的PNG
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)

        # 转换为base64
        chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        # 清理内存
        plt.close(fig)

        return chart_base64

    except Exception as e:
        print(f"生成图表时出错: {e}")
        return None

def test_with_mock_data():
    """使用模拟数据测试图表生成"""
    # 生成模拟历史数据
    mock_data = []
    base_date = datetime.now()
    base_price = 50000

    for i in range(30, 0, -1):
        date = base_date - timedelta(days=i)
        price = base_price + np.random.normal(0, 1000) + i*100
        change = np.random.normal(0, 2)

        mock_data.append({
            'timestamp': date.isoformat(),
            'price': price,
            'percent_change_24h': change
        })

    # 生成图表
    chart_base64 = generate_price_chart('BTC', mock_data)

    if chart_base64:
        # 保存图表到文件
        with open('mock_chart.png', 'wb') as f:
            f.write(base64.b64decode(chart_base64))
        print("模拟数据图表已保存为 mock_chart.png")

        # 生成HTML页面预览
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>测试图表</title>
        </head>
        <body>
            <h1>BTC 价格趋势图 (模拟数据)</h1>
            <img src="data:image/png;base64,{chart_base64}" alt="BTC价格图表">
        </body>
        </html>
        """

        with open('chart_preview.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("图表预览已保存为 chart_preview.html")
    else:
        print("图表生成失败")
def enhanced_investment_analysis(crypto_data, user_risk_level='medium', investment_budget=1000):
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
        name = crypto_data['name']
        symbol = crypto_data['symbol']
        price = float(crypto_data['price'])
        change_24h = float(crypto_data['percent_change_24h'])
        change_7d = float(crypto_data['percent_change_7d'])
        market_cap = float(crypto_data['market_cap'])
        volume_24h = float(crypto_data['volume_24h'])

        # 计算分析指标
        analysis = {
            'name': name,
            'symbol': symbol,
            'current_price': price,
            'action': 'HOLD',  # BUY, SELL, HOLD
            'confidence': 0,   # 信心指数 0-100
            'investment_range': {'min': 0, 'max': 0, 'recommended': 0},
            'target_prices': {'take_profit': 0, 'stop_loss': 0},
            'timeframe': '短期',  # 短期/中期/长期
            'risk_level': '中等',
            'factors': [],
            'technical_signals': [],
            'disclaimer': "⚠️ 重要提示: 此分析仅供参考，不构成投资建议。加密货币投资存在高风险，请根据自身风险承受能力谨慎决策。"
        }

        # 1. 技术分析信号
        # 趋势分析
        if change_24h > 5 and change_7d > 10:
            analysis['technical_signals'].append("买入信号: 强势上涨趋势")
        elif change_24h > 2 and change_7d > 5:
            analysis['technical_signals'].append("持有信号: 稳定上涨趋势")
        elif change_24h < -5 and change_7d < -10:
            analysis['technical_signals'].append("卖出信号: 强烈下跌趋势")
        elif change_24h < -2 and change_7d < -5:
            analysis['technical_signals'].append("观望信号: 温和下跌趋势")
        else:
            analysis['technical_signals'].append("持有信号: 震荡行情")

        # 成交量分析
        if market_cap > 0 and volume_24h > market_cap * 0.1:  # 成交量占市值比例
            analysis['technical_signals'].append("确认信号: 高成交量确认趋势")

        # 2. 风险评估
        volatility = abs(change_24h) + abs(change_7d)
        if volatility > 25:
            analysis['risk_level'] = "高风险"
            analysis['factors'].append("高波动性")
        elif volatility > 15:
            analysis['risk_level'] = "中等风险"
            analysis['factors'].append("中等波动性")
        else:
            analysis['risk_level'] = "低风险"
            analysis['factors'].append("低波动性")

        # 3. 市值分析
        if market_cap > 50000000000:  # 500亿美元
            analysis['factors'].append("大盘币，相对稳定")
        elif market_cap > 10000000000:  # 100亿美元
            analysis['factors'].append("中盘币，稳定性适中")
        else:
            analysis['factors'].append("小盘币，高风险高收益")

        # 4. 投资建议算法
        score = 0

        # 趋势得分
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

        # 市值得分
        if market_cap > 50000000000:
            score += 3
        elif market_cap > 10000000000:
            score += 1
        else:
            score -= 2

        # 成交量得分
        volume_ratio = volume_24h / market_cap if market_cap > 0 else 0
        if volume_ratio > 0.1:
            score += 2
        elif volume_ratio > 0.05:
            score += 1

        # 计算信心指数
        analysis['confidence'] = max(0, min(100, 50 + (score * 5)))

        # 5. 买卖决策
        if score >= 8:
            analysis['action'] = 'BUY'
            analysis['timeframe'] = '短期'
        elif score >= 4:
            analysis['action'] = 'BUY'
            analysis['timeframe'] = '中期'
        elif score >= -3:
            analysis['action'] = 'HOLD'
            analysis['timeframe'] = '短期'
        elif score >= -7:
            analysis['action'] = 'SELL'
            analysis['timeframe'] = '短期'
        else:
            analysis['action'] = 'SELL'
            analysis['timeframe'] = '立即'

        # 6. 投资金额建议
        risk_multiplier = {'low': 0.5, 'medium': 1.0, 'high': 1.5}
        base_investment = investment_budget * risk_multiplier.get(user_risk_level, 1.0) / 10  # 分散投资到10种资产

        if analysis['action'] == 'BUY':
            if score >= 8:  # 强烈买入
                analysis['investment_range'] = {
                    'min': round(base_investment * 0.3, 2),
                    'max': round(base_investment * 0.7, 2),
                    'recommended': round(base_investment * 0.5, 2)
                }
            elif score >= 4:  # 买入
                analysis['investment_range'] = {
                    'min': round(base_investment * 0.2, 2),
                    'max': round(base_investment * 0.5, 2),
                    'recommended': round(base_investment * 0.3, 2)
                }
            else:  # 持有
                analysis['investment_range'] = {
                    'min': 0,
                    'max': round(base_investment * 0.2, 2),
                    'recommended': round(base_investment * 0.1, 2)
                }
        elif analysis['action'] == 'SELL':
            analysis['investment_range'] = {
                'min': 0,
                'max': 0,
                'recommended': 0
            }
        else:  # HOLD
            analysis['investment_range'] = {
                'min': 0,
                'max': round(base_investment * 0.3, 2),
                'recommended': round(base_investment * 0.1, 2)
            }

        # 7. 目标价格计算
        if analysis['action'] == 'BUY':
            analysis['target_prices'] = {
                'take_profit': round(price * (1 + min(0.2, score * 0.03)), 2),  # 20%以内
                'stop_loss': round(price * (1 - min(0.1, abs(score) * 0.02)), 2)  # 10%以内
            }
        elif analysis['action'] == 'SELL':
            analysis['target_prices'] = {
                'take_profit': round(price * (1 - min(0.1, abs(score) * 0.02)), 2),
                'stop_loss': round(price * (1 + min(0.05, abs(score) * 0.01)), 2)
            }
        else:
            analysis['target_prices'] = {
                'take_profit': round(price * 1.1, 2),
                'stop_loss': round(price * 0.9, 2)
            }

        return analysis

    except (KeyError, TypeError, ValueError) as e:
        print(f"数据分析错误: {e}")
        return None


def analyze_portfolio_opportunities(investment_budget=1000, risk_level='medium'):
    """
    分析投资组合机会 - 为用户提供最佳投资建议
    :param investment_budget: 投资预算
    :param risk_level: 风险偏好
    :return: 投资机会列表
    """
    try:
        # 获取前20名加密货币
        top_cryptos = get_top_cryptocurrencies(20)
        if not top_cryptos:
            return []

        opportunities = []

        # 分析每个货币
        for crypto in top_cryptos:
            analysis = enhanced_investment_analysis(crypto, risk_level, investment_budget)
            if analysis and analysis['investment_range']['recommended'] > 0:
                opportunities.append(analysis)

        # 按推荐投资金额排序
        opportunities.sort(key=lambda x: x['investment_range']['recommended'], reverse=True)

        return opportunities[:10]  # 返回前10个机会

    except Exception as e:
        print(f"投资机会分析错误: {e}")
        return []

if __name__ == "__main__":
    # 测试基本图表功能
    test_price_chart()

    # 测试使用模拟数据生成图表
    test_with_mock_data()
