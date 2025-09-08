from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import matplotlib
matplotlib.use("Agg")  # ✅ 确保在服务器无显示环境下也能正常绘图
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# from matplotlib.backends.backend_agg import FigureCanvasAgg  # ❌ 未使用，删除以避免混淆
import io
import base64
from datetime import datetime
from crypto_api import (
    get_global_metrics,
    get_top_cryptocurrencies,
    get_cryptocurrency_info,
    enhanced_investment_analysis,
    analyze_portfolio_opportunities
)
from database import (
    init_database,
    get_historical_prices,
    add_to_watchlist,
    get_watchlist,
    add_to_portfolio,
    get_portfolio
)

# 创建Flask应用
app = Flask(__name__)

# JSON 返回中文不转义
app.config['JSON_AS_ASCII'] = False

# 初始化数据库
init_database()

# ==================== 健康检查 ====================
@app.route('/healthz')
def healthz():
    """健康检查"""
    return jsonify({"status": "ok"}), 200

# ==================== 首页路由 ====================
@app.route('/')
def index():
    """首页 - 显示热门加密货币"""
    try:
        # 获取加密货币数据
        limit = request.args.get('limit', 10, type=int)
        if limit <= 0:
            limit = 10
        top_cryptos = get_top_cryptocurrencies(limit)

        # 确保数据格式正确
        if top_cryptos is None:
            top_cryptos = []

        return render_template('index.html', top_cryptos=top_cryptos)

    except Exception as e:
        print("首页错误:", str(e))
        import traceback
        traceback.print_exc()
        return render_template('index.html', error=str(e))

# ==================== 加密货币详情路由 ====================
@app.route('/crypto/<symbol>')
def crypto_detail(symbol):
    """加密货币详情页"""
    try:
        symbol = (symbol or "").upper().strip()

        # 获取加密货币详细信息
        crypto_info = get_cryptocurrency_info(symbol)

        # 获取历史价格数据
        days = request.args.get('days', 30, type=int)
        if days <= 0:
            days = 30
        history_data = get_historical_prices(symbol, days)

        # 生成价格图表
        chart_base64 = None
        if history_data and len(history_data) > 0:
            chart_base64 = generate_price_chart(symbol, history_data)

        if crypto_info:
            return render_template('crypto_detail.html',
                                   crypto=crypto_info,
                                   history=history_data,
                                   chart_base64=chart_base64)
        else:
            return render_template('crypto_detail.html',
                                   symbol=symbol,
                                   error="未找到该加密货币的信息",
                                   chart_base64=chart_base64)

    except Exception as e:
        print("详情页错误:", str(e))
        import traceback
        traceback.print_exc()
        return render_template('crypto_detail.html',
                               symbol=symbol,
                               error=str(e),
                               chart_base64=None)

# ==================== API接口路由 ====================
@app.route('/api/crypto/<symbol>')
def api_crypto_detail(symbol):
    """API接口 - 返回加密货币详细信息"""
    try:
        symbol = (symbol or "").upper().strip()
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        crypto_info = get_cryptocurrency_info(symbol)
        if crypto_info:
            return jsonify(crypto_info)
        else:
            return jsonify({'error': 'Crypto not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top')
def api_top_cryptos():
    """API接口 - 返回热门加密货币"""
    try:
        limit = request.args.get('limit', 10, type=int)
        if limit <= 0:
            limit = 10
        cryptos = get_top_cryptocurrencies(limit)
        return jsonify(cryptos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 关注列表路由 ====================
@app.route('/watchlist')
def watchlist():
    """关注列表页面"""
    try:
        watchlist_data = get_watchlist()
        return render_template('watchlist.html', watchlist=watchlist_data)
    except Exception as e:
        return render_template('watchlist.html', error=str(e))

@app.route('/api/watchlist/add', methods=['POST'])
def api_add_to_watchlist():
    """API接口 - 添加到关注列表"""
    try:
        data = request.get_json(silent=True) or {}
        symbol = (data.get('symbol') or '').upper().strip()
        notes = (data.get('notes') or '').strip()
        alert_price = data.get('alert_price', None)

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # alert_price 校验（允许 None 或 正数）
        if alert_price is not None:
            try:
                alert_price = float(alert_price)
                if alert_price <= 0:
                    return jsonify({'error': 'alert_price 必须为正数'}), 400
            except (TypeError, ValueError):
                return jsonify({'error': 'alert_price 参数格式错误，必须为数字'}), 400

        if add_to_watchlist(symbol, notes, alert_price):
            return jsonify({'success': True, 'message': 'Added to watchlist'})
        else:
            return jsonify({'success': False, 'message': 'Already in watchlist'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 投资组合路由 ====================
@app.route('/portfolio')
def portfolio():
    """投资组合页面"""
    try:
        portfolio_data = get_portfolio()
        return render_template('portfolio.html', portfolio=portfolio_data)
    except Exception as e:
        return render_template('portfolio.html', error=str(e))

@app.route('/api/portfolio/add', methods=['POST'])
def api_portfolio_add():
    """API接口 - 添加到投资组合"""
    try:
        data = request.get_json(silent=True) or {}
        symbol = (data.get('symbol') or '').upper().strip()
        amount = data.get('amount', None)
        cost = data.get('cost', None)

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # 数量与成本校验
        try:
            amount = float(amount)
            cost = float(cost)
        except (TypeError, ValueError):
            return jsonify({'error': 'amount 与 cost 必须为数字'}), 400

        if amount <= 0 or cost <= 0:
            return jsonify({'error': 'amount 与 cost 必须为正数'}), 400

        # 写入数据库（假设 add_to_portfolio 返回 True/False 或抛异常）
        added = add_to_portfolio(symbol, amount, cost)
        return jsonify({'success': bool(added)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 投资分析路由 ====================
@app.route('/investment-analysis')
def investment_analysis_page():
    """投资分析主页面"""
    return render_template('investment_analysis.html')

@app.route('/api/investment/analyze/<symbol>')
def api_investment_analyze(symbol):
    """API接口 - 分析特定货币的投资建议"""
    try:
        # 获取用户参数
        risk_level = request.args.get('risk_level', 'medium')
        budget = request.args.get('budget', 1000, type=float)

        # 参数验证
        if risk_level not in ['low', 'medium', 'high']:
            return jsonify({'error': '风险级别参数无效，必须是 low、medium 或 high'}), 400

        if budget is None or budget <= 0:
            return jsonify({'error': '预算必须大于0'}), 400

        # 获取货币信息
        symbol = (symbol or "").upper().strip()
        crypto_info = get_cryptocurrency_info(symbol)
        if not crypto_info:
            return jsonify({'error': f'未找到货币: {symbol}'}), 404

        # 进行投资分析
        analysis = enhanced_investment_analysis(crypto_info, risk_level, budget)
        if not analysis:
            return jsonify({'error': '分析失败，请稍后重试'}), 500

        return jsonify(analysis)

    except ValueError:
        return jsonify({'error': '预算参数格式错误，必须是数字'}), 400
    except Exception as e:
        # 打印具体错误到日志，但对外返回通用信息
        print("分析错误:", str(e))
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/investment/opportunities')
def api_investment_opportunities():
    """API接口 - 获取投资机会列表"""
    try:
        risk_level = request.args.get('risk_level', 'medium')
        budget = request.args.get('budget', 1000, type=float)

        # 参数验证
        if risk_level not in ['low', 'medium', 'high']:
            return jsonify({'error': '风险级别参数无效，必须是 low、medium 或 high'}), 400

        if budget is None or budget <= 0:
            return jsonify({'error': '预算必须大于0'}), 400

        opportunities = analyze_portfolio_opportunities(budget, risk_level) or []
        return jsonify(opportunities)

    except ValueError:
        return jsonify({'error': '预算参数格式错误，必须是数字'}), 400
    except Exception as e:
        print("机会列表错误:", str(e))
        return jsonify({'error': '服务器内部错误'}), 500

# ==================== 模板过滤器 ====================
@app.template_filter('currency')
def currency_filter(value):
    """货币格式化过滤器"""
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"${value:,.2f}"
    return value

@app.template_filter('price')
def price_filter(value):
    """价格格式化过滤器"""
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        if value > 1:
            return f"${value:,.2f}"
        else:
            return f"${value:.6f}"
    return value

@app.template_filter('percent')
def percent_filter(value):
    """百分比格式化过滤器"""
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:+.2f}%"
    return value

# ==================== 图表生成功能 ====================
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
                timestamp = record.get('timestamp')
                if isinstance(timestamp, str):
                    # 处理不同的时间格式
                    if 'T' in timestamp:
                        date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        date_obj = datetime.fromisoformat(timestamp)
                else:
                    date_obj = timestamp

                # 价格解析
                price_val = record.get('price')
                if price_val is None:
                    continue

                dates.append(date_obj)
                prices.append(float(price_val))
            except (ValueError, KeyError, TypeError) as e:
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
        # 至少每1天一个刻度，最多约10个主刻度
        interval = max(1, len(dates) // 10)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
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

# ==================== 测试路由 ====================
@app.route('/test-api')
def test_api():
    """测试API连接"""
    try:
        cryptos = get_top_cryptocurrencies(3)
        return f"<h1>API测试结果</h1><pre>{cryptos}</pre>"
    except Exception as e:
        return f"<h1>API错误</h1><p>{str(e)}</p>"

# ==================== 全局错误处理 ====================
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    # 生产环境请将 debug 设为 False
    app.run(debug=True, host='0.0.0.0', port=5000)
