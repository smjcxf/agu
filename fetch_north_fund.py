#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北向资金监控 — 采集汇总+个股+板块+连续加仓数据
用法: python fetch_north_fund.py
输出: data/north_fund.json

原则: 不构造数据，API无数据时保留旧数据
"""
import os, sys, json, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "north_fund.json")

def fetch_summary():
    """从akshare获取北向资金当日汇总"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_fund_flow_summary_em()
        north = df[df['资金方向'] == '北向']
        if len(north) == 0:
            return None
        sh = north[north['板块'] == '沪股通']
        sz = north[north['板块'] == '深股通']
        total = 0.0
        for subset in [sh, sz]:
            if len(subset) > 0:
                total += float(subset.iloc[-1].get('资金净流入', 0) or 0)
        if total == 0:
            return None
        direction = "流入" if total >= 0 else "流出"
        return {"total": round(abs(total), 2), "unit": "亿", "direction": direction}
    except Exception as e:
        print(f"  [summary API] {e}")
        return None

def fetch_weekly_summary():
    """获取本周北向资金累计净流入"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_hist_em(symbol="北向资金")
        if df is None or len(df) == 0:
            return None
        # 按日期降序，取最近5个交易日
        df_sorted = df.sort_values("日期", ascending=False)
        recent = df_sorted.head(5)
        weekly_total = recent["当日成交净买额"].sum()
        if weekly_total == 0:
            return None
        direction = "流入" if weekly_total >= 0 else "流出"
        avg_daily = weekly_total / len(recent)
        today_row = recent.iloc[0]
        return {
            "total": round(abs(weekly_total), 2),
            "unit": "亿",
            "direction": direction,
            "avg_daily": round(abs(avg_daily), 2),
            "days": len(recent),
            "date_range": f"{recent.iloc[-1]['日期']} — {recent.iloc[0]['日期']}"
        }
    except Exception as e:
        print(f"  [weekly API] {e}")
        return None

def fetch_sector_flow():
    """获取北向资金行业板块流向（增持/减持TOP5）"""
    try:
        import akshare as ak
        # 尝试获取北向资金行业板块排名
        df = ak.stock_hsgt_board_rank_em()
        if df is None or len(df) == 0:
            return None
        
        buy_sectors = []
        sell_sectors = []
        
        for _, row in df.iterrows():
            name = str(row.get("名称", "")).strip()
            net_flow_val = float(row.get("净买入", 0) or 0) / 1e8  # 转为亿
            if not name or abs(net_flow_val) < 0.1:
                continue
            if net_flow_val > 0:
                buy_sectors.append({"name": name, "net": round(net_flow_val, 2), "unit": "亿"})
            else:
                sell_sectors.append({"name": name, "net": round(net_flow_val, 2), "unit": "亿"})
        
        # 按绝对值排序
        buy_sectors.sort(key=lambda x: x["net"], reverse=True)
        sell_sectors.sort(key=lambda x: x["net"])
        
        return {
            "buy_top5": buy_sectors[:5],
            "sell_top5": sell_sectors[:5]
        }
    except Exception as e:
        print(f"  [sector API] {e}")
        return None

def fetch_top_stocks():
    """获取北向资金当日净买入个股TOP10"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_individual_em()
        if df is None or len(df) == 0:
            return None
        
        stocks = []
        for _, row in df.iterrows():
            name = str(row.get("股票名称", "")).strip()
            net_buy = float(row.get("净买入", 0) or 0) / 1e8
            if not name or net_buy <= 0.1:
                continue
            code = str(row.get("股票代码", "")).strip()
            stocks.append({
                "code": code,
                "name": name,
                "net_buy": round(net_buy, 2),
                "unit": "亿"
            })
        
        stocks.sort(key=lambda x: x["net_buy"], reverse=True)
        return stocks[:10]
    except Exception as e:
        print(f"  [top stocks API] {e}")
        return None

def fetch_consecutive():
    """获取北向资金连续加仓个股"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_hold_stock_em()
        if df is None or len(df) == 0:
            return None
        
        consecutive = []
        for _, row in df.iterrows():
            name = str(row.get("股票名称", "")).strip()
            add_days = int(row.get("连续增持天数", 0) or 0)
            if add_days < 2:
                continue
            total_val = float(row.get("累计增持", 0) or 0) / 1e8
            if total_val < 1:
                continue
            consecutive.append({
                "code": str(row.get("股票代码", "")).strip(),
                "name": name,
                "days": add_days,
                "total": round(total_val, 2),
                "unit": "亿"
            })
        
        consecutive.sort(key=lambda x: x["days"] + x["total"] * 0.1, reverse=True)
        return consecutive[:5]
    except Exception as e:
        print(f"  [consecutive API] {e}")
        return None

def load_old_data():
    """加载旧数据，用于API空数据回退"""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            if old.get("top_buy") or (old.get("net_flow", {}).get("total", 0) > 0):
                return old
        except:
            pass
    return None


def main():
    print("=" * 50)
    print("  北向资金监控 (全面采集)")
    print("=" * 50)

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    old_data = load_old_data()

    result = {
        "update_time": now_str,
        "data_date": None,
        "net_flow": {"total": 0, "unit": "亿", "direction": "未获取"},
        "week_flow": None,
        "top_buy": [],
        "consecutive": [],
        "sector_flow": None,
        "data_available": False,
        "data_source": "API无数据",
    }

    has_any_data = False

    # 1. 当日汇总
    print("\n  [1/5] 当日净流入...")
    summary = fetch_summary()
    if summary and summary["total"] > 0:
        result["net_flow"] = summary
        result["data_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        result["data_source"] = "akshare API"
        result["data_available"] = True
        has_any_data = True
        print(f"    OK {summary['direction']} {summary['total']}{summary['unit']}")
    else:
        print("    WARN 无数据")

    # 2. 周累计
    print("  [2/5] 周累计净流入...")
    week = fetch_weekly_summary()
    if week:
        result["week_flow"] = week
        has_any_data = True
        print(f"    OK {week['direction']} {week['total']}{week['unit']} ({week['date_range']})")
    else:
        print("    WARN 无数据")

    # 3. 板块流向
    print("  [3/5] 板块流向...")
    sector = fetch_sector_flow()
    if sector:
        result["sector_flow"] = sector
        has_any_data = True
        print(f"    OK 增持{len(sector.get('buy_top5', []))} 减持{len(sector.get('sell_top5', []))}")
    else:
        print("    WARN 无数据")

    # 4. 个股净买TOP
    print("  [4/5] 个股净买TOP...")
    top_stocks = fetch_top_stocks()
    if top_stocks:
        result["top_buy"] = top_stocks
        has_any_data = True
        print(f"    OK {len(top_stocks)} 只")
    else:
        if old_data and old_data.get("top_buy"):
            result["top_buy"] = old_data["top_buy"]
            print("    WARN 保留旧个股数据")
        else:
            print("    WARN 无数据")

    # 5. 连续加仓
    print("  [5/5] 连续加仓...")
    consec = fetch_consecutive()
    if consec:
        result["consecutive"] = consec
        has_any_data = True
        print(f"    OK {len(consec)} 只")
    else:
        if old_data and old_data.get("consecutive"):
            result["consecutive"] = old_data["consecutive"]
            print("    WARN 保留旧连续加仓数据")
        else:
            print("    WARN 无数据")

    # 空数据保护：完全没获取到任何数据时保留旧数据
    if not has_any_data:
        if old_data:
            print("\n  ⚠️ 所有API均无数据，保留最近一次有效数据")
            result = old_data
        else:
            print("\n  ⚠️ 无数据且无旧数据可回退")

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已保存: {OUTPUT_FILE}")
    print(f"   available={result.get('data_available', False)}")
    print(f"   top_buy={len(result.get('top_buy', []))} consecutive={len(result.get('consecutive', []))}")

if __name__ == "__main__":
    main()
