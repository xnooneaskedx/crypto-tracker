import sys
import csv
from datetime import datetime
from crypto_api import (
    get_global_metrics,
    get_top_cryptocurrencies,
    get_cryptocurrency_info,
    parse_crypto_data,
    analyze_investment_opportunity  # 确保这个函数在 crypto_api.py 中定义
)

def display_global_metrics():
    """显示全球市场指标"""
    data = get_global_metrics()
    if not data:
        return

    metrics = data['data']
    print("\n=== 全球加密货币市场指标 ===")
    print(f"总市值: ${metrics['quote']['USD']['total_market_cap']:,.2f}")
    print(f"24小时交易量: ${metrics['quote']['USD']['total_volume_24h']:,.2f}")
    print(f"比特币主导率: {metrics['btc_dominance']:.2f}%")
    print(f"活跃加密货币数量: {metrics['active_cryptocurrencies']}")

def display_top_cryptocurrencies(limit=10):
    """显示排名前几位的加密货币"""
    data = get_top_cryptocurrencies(limit)
    if not data:
        return

    crypto_list = parse_crypto_data(data)
    if not crypto_list:
        print("无法解析加密货币数据")
        return

    print(f"\n=== 前{limit}名加密货币 ===")
    print(f"{'排名':<4} {'名称':<12} {'符号':<6} {'价格(USD)':<15} {'24h变化':<12} {'市值(USD)':<15}")
    print("-" * 80)

    for i, crypto in enumerate(crypto_list, 1):
        price = f"${crypto['price']:.2f}" if crypto['price'] > 1 else f"${crypto['price']:.6f}"
        change = f"{crypto['percent_change_24h']:+.2f}%"
        market_cap = f"${crypto['market_cap']:,.0f}"

        # 根据变化设置颜色
        change_color = change
        if crypto['percent_change_24h'] > 0:
            change_color = f"\033[32m{change}\033[0m"  # 绿色
        elif crypto['percent_change_24h'] < 0:
            change_color = f"\033[31m{change}\033[0m"  # 红色

        print(f"{i:<4} {crypto['name']:<12} {crypto['symbol']:<6} {price:<15} {change_color:<12} {market_cap:<15}")

def display_cryptocurrency_info(symbol):
    """显示特定加密货币信息"""
    data = get_cryptocurrency_info(symbol)
    if not data:
        return

    crypto_list = parse_crypto_data(data)
    if not crypto_list:
        print("无法找到该加密货币")
        return

    crypto = crypto_list[0]
    print(f"\n=== {crypto['name']} ({crypto['symbol']}) 详细信息 ===")
    print(f"当前价格: ${crypto['price']:.2f}" if crypto['price'] > 1 else f"当前价格: ${crypto['price']:.6f}")
    print(f"24小时变化: {crypto['percent_change_24h']:+.2f}%")
    print(f"7天变化: {crypto['percent_change_7d']:+.2f}%")
    print(f"市值: ${crypto['market_cap']:,.2f}")
    print(f"24小时交易量: ${crypto['volume_24h']:,.2f}")

def export_to_csv(crypto_list, filename=None):
    """导出加密货币数据到CSV文件"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crypto_data_{timestamp}.csv"

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # 写入表头
            writer.writerow(['排名', '名称', '符号', '价格(USD)', '24h变化(%)', '市值(USD)', '24h交易量(USD)'])

            # 写入数据
            for i, crypto in enumerate(crypto_list, 1):
                writer.writerow([
                    i,
                    crypto['name'],
                    crypto['symbol'],
                    crypto['price'],
                    crypto['percent_change_24h'],
                    crypto['market_cap'],
                    crypto['volume_24h']
                ])

        print(f"数据已导出到: {filename}")
        return True

    except Exception as e:
        print(f"导出失败: {e}")
        return False

def display_investment_advice(symbol, investment_amount=1000):
    """显示投资建议"""
    print(f"\n=== {symbol.upper()} 投资分析报告 ===")
    print("⚠️  重要声明: 本分析仅供教育参考，不构成投资建议")
    print("⚠️  加密货币投资存在高风险，请谨慎决策\n")

    # 获取加密货币数据
    data = get_cryptocurrency_info(symbol)
    if not data:
        print("无法获取加密货币数据")
        return

    crypto_list = parse_crypto_data(data)
    if not crypto_list:
        print("无法解析加密货币数据")
        return

    crypto_data = crypto_list[0]

    # 分析投资机会
    analysis = analyze_investment_opportunity(crypto_data, investment_amount)
    if not analysis:
        print("无法生成投资分析")
        return

    # 显示分析结果
    print(f"加密货币: {analysis['name']} ({analysis['symbol']})")
    print(f"当前价格: ${analysis['current_price']:.2f}" if analysis['current_price'] > 1
          else f"当前价格: ${analysis['current_price']:.6f}")
    print(f"投资建议: {analysis['recommendation']}")
    print(f"风险等级: {analysis['risk_level']}")

    if analysis['recommended_amount'] > 0:
        coins_amount = analysis['recommended_amount'] / analysis['current_price']
        print(f"建议投资金额: ${analysis['recommended_amount']:.2f}")
        print(f"可购买数量: {coins_amount:.6f} {analysis['symbol']}")
    else:
        print("建议投资金额: $0.00 (不建议投资)")

    print(f"\n分析因素:")
    for i, factor in enumerate(analysis['factors'], 1):
        print(f"  {i}. {factor}")

    print(f"\n{analysis['disclaimer']}")

def display_top_investment_opportunities(limit=5, investment_amount=1000):
    """显示最佳投资机会"""
    print(f"\n=== 前{limit}名加密货币投资分析 ===")
    print("⚠️  重要声明: 本分析仅供教育参考，不构成投资建议")

    # 获取前几名加密货币
    data = get_top_cryptocurrencies(limit)
    if not data:
        print("无法获取加密货币数据")
        return

    crypto_list = parse_crypto_data(data)
    if not crypto_list:
        print("无法解析加密货币数据")
        return

    opportunities = []
    for crypto in crypto_list:
        analysis = analyze_investment_opportunity(crypto, investment_amount)
        if analysis:
            opportunities.append(analysis)

    # 按推荐程度排序
    opportunities.sort(key=lambda x: x['recommended_amount'], reverse=True)

    print(f"\n{'排名':<4} {'货币':<10} {'建议':<10} {'风险':<8} {'建议金额':<12} {'可购数量':<15}")
    print("-" * 70)

    for i, opp in enumerate(opportunities, 1):
        if opp['recommended_amount'] > 0:
            coins = opp['recommended_amount'] / opp['current_price']
            print(f"{i:<4} {opp['symbol']:<10} {opp['recommendation']:<10} {opp['risk_level']:<8} "
                  f"${opp['recommended_amount']:<11.2f} {coins:<15.6f}")
        else:
            print(f"{i:<4} {opp['symbol']:<10} {opp['recommendation']:<10} {opp['risk_level']:<8} "
                  f"$0.00          不建议投资")

def main():
    """主程序入口"""
    print("欢迎使用加密货币价格查询系统!")

    while True:
        print("\n请选择功能:")
        print("1. 查看全球市场指标")
        print("2. 查看前10名加密货币")
        print("3. 查看前5名加密货币")
        print("4. 查询特定加密货币")
        print("5. 导出前20名加密货币数据")
        print("6. 单个货币投资分析")
        print("7. 最佳投资机会排名")
        print("8. 退出")

        choice = input("\n请输入选项 (1-8): ").strip()

        if choice == '1':
            display_global_metrics()
        elif choice == '2':
            display_top_cryptocurrencies(10)
        elif choice == '3':
            display_top_cryptocurrencies(5)
        elif choice == '4':
            symbol = input("请输入加密货币符号 (如 BTC, ETH): ").strip()
            if symbol:
                display_cryptocurrency_info(symbol)
        elif choice == '5':
            print("正在获取数据...")
            data = get_top_cryptocurrencies(20)
            if data:
                crypto_list = parse_crypto_data(data)
                if crypto_list:
                    export_to_csv(crypto_list)
                else:
                    print("解析数据失败")
            else:
                print("获取数据失败")
        elif choice == '6':
            symbol = input("请输入加密货币符号 (如 BTC, ETH): ").strip()
            if symbol:
                amount_str = input("请输入投资金额(USD，默认1000): ").strip()
                try:
                    amount = float(amount_str) if amount_str else 1000
                    display_investment_advice(symbol, amount)
                except ValueError:
                    print("输入金额无效，使用默认值1000美元")
                    display_investment_advice(symbol, 1000)
        elif choice == '7':
            amount_str = input("请输入投资金额(USD，默认1000): ").strip()
            try:
                amount = float(amount_str) if amount_str else 1000
                display_top_investment_opportunities(5, amount)
            except ValueError:
                print("输入金额无效，使用默认值1000美元")
                display_top_investment_opportunities(5, 1000)
        elif choice == '8':
            print("感谢使用，再见!")
            break
        else:
            print("无效选项，请重新输入")

if __name__ == "__main__":
    main()
