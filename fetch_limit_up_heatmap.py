#!/usr/bin/env python3
"""
fetch_limit_up_heatmap.py — 涨停热力矩阵数据采集
- 每日获取涨停股票 → 按概念板块归类统计 → 构建10日热力矩阵
- 输出 data/limit_up_heatmap.json
- 数据源：akshare stock_zt_pool_strong_em（强势涨停池）
- 支持全量重建（检测到脏数据时自动拉取近10日重建）
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import akshare as ak
except ImportError:
    print("✗ akshare 未安装")
    sys.exit(1)

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKSPACE, "data")
OUTPUT = os.path.join(DATA_DIR, "limit_up_heatmap.json")

# 概念板块关键词映射（从涨停股票所属概念中匹配）
SECTOR_KEYWORDS = [
    "新能源车", "人工智能", "半导体", "机器人", "光伏",
    "低空经济", "医药", "消费电子", "军工", "信创",
    "算力", "人形机器人", "无人驾驶", "固态电池", "储能",
    "数据要素", "6G", "商业航天", "氢能源", "芯片",
    "通信设备", "物联网", "智能驾驶", "光模块", "液冷",
]


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def get_trade_dates(n=15):
    """获取最近n个交易日"""
    dates = []
    try:
        df = ak.tool_trade_date_hist_sse()
        if df is not None and len(df) > 0:
            all_dates = [str(d).replace("-", "") for d in df["trade_date"]]
            today = datetime.now().strftime("%Y%m%d")
            # 过滤未来日期和今天之后的
            past_dates = [d for d in all_dates if d <= today]
            dates = past_dates[-n:]
    except Exception as e:
        print(f"  ⚠ 获取交易日历失败: {e}，回退到自然日推算")
        # 回退方案：倒推n*2个自然日，跳过周末
        d = datetime.now()
        while len(dates) < n:
            if d.weekday() < 5:  # 工作日
                dates.append(d.strftime("%Y%m%d"))
            d -= timedelta(days=1)
        dates.reverse()
    return dates


def get_limit_up_by_date(date_str):
    """获取指定日期的涨停股票数据"""
    stocks = []
    # 方案1：强势股池
    try:
        df = ak.stock_zt_pool_strong_em(date=date_str)
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                stocks.append({
                    "name": str(row.get("名称", "")),
                    "code": str(row.get("代码", "")),
                    "pct_chg": float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0,
                    "limit_times": int(row.get("涨停次数", 1)) if row.get("涨停次数") else 1,
                    "sector": str(row.get("所属行业", "")),
                })
            return stocks
    except Exception as e:
        pass

    # 方案2：当日涨停池
    try:
        df = ak.stock_zt_pool_em(date=date_str)
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                stocks.append({
                    "name": str(row.get("名称", "")),
                    "code": str(row.get("代码", "")),
                    "pct_chg": float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0,
                    "limit_times": int(row.get("连板数", 1)) if row.get("连板数") else 1,
                    "sector": str(row.get("所属行业", "")),
                })
            return stocks
    except Exception:
        pass

    return stocks


def classify_by_sector(stocks):
    """将涨停股票归类到概念板块，返回 {板块名: {股票名: 涨停次数}}"""
    sector_counts = defaultdict(lambda: defaultdict(int))

    for s in stocks:
        sector_str = (s.get("sector", "") or "").strip()
        if not sector_str:
            sector_counts["其他"][s["name"]] = s.get("limit_times", 1)
            continue

        matched = False
        for kw in SECTOR_KEYWORDS:
            if kw.lower() in sector_str.lower():
                sector_counts[kw][s["name"]] = s["limit_times"]
                matched = True
                break

        if not matched:
            sector_counts["其他"][s["name"]] = s.get("limit_times", 1)

    return sector_counts


def build_heatmap(days_data):
    """
    构建热力矩阵
    days_data: [(date_str, {sector: {name: count}}), ...]
    返回 (dates_list, sectors_list)
    """
    # 收集所有出现过的板块
    all_sectors_set = set()
    for _, sc in days_data:
        all_sectors_set.update(sc.keys())

    # 确保至少包含固定的热门板块
    fixed_sectors = ["其他", "半导体", "固态电池", "光伏", "军工",
                     "消费电子", "通信设备", "AI算力", "医药", "电力",
                     "地产链", "白酒消费", "券商", "机器人", "新能源车"]
    for fs in fixed_sectors:
        all_sectors_set.add(fs)

    # 按最后一天的涨停总数排序
    last_day_sc = days_data[-1][1] if days_data else {}
    sorted_sectors = sorted(
        all_sectors_set,
        key=lambda x: sum(last_day_sc.get(x, {}).values()),
        reverse=True
    )[:15]

    dates = []
    sectors_output = []

    for sec in sorted_sectors:
        sec_data = []
        for date_str, sc in days_data:
            dates.append(date_str)  # 每次都会append，后面去重
            cnt = sum(sc.get(sec, {}).values())
            sec_data.append(cnt)
        sectors_output.append({"name": sec, "data": sec_data})

    # dates 去重（因为上面循环中每个板块都会append）
    unique_dates = []
    seen = set()
    for d in dates:
        if d not in seen:
            unique_dates.append(d)
            seen.add(d)

    return unique_dates, sectors_output


def needs_rebuild(existing):
    """判断是否需要全量重建"""
    dates = existing.get("dates", [])
    if not dates or len(dates) < 3:
        return True
    # 有重复日期 → 需要重建
    if len(dates) != len(set(dates)):
        return False  # 不在这里触发，由清洗逻辑处理；改为让调用方决定
    return False


def main():
    print("=" * 60)
    print(f"  涨停热力矩阵采集  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    existing = load_json(OUTPUT, {"dates": [], "sectors": []})
    existing_dates = existing.get("dates", [])

    # ── 判断是否需要全量重建 ──
    need_rebuild = False
    if len(existing_dates) != len(set(existing_dates)):
        print(f"  🧹 检测到重复日期（{len(existing_dates)}列中有重复），触发全量重建")
        need_rebuild = True
    elif len(existing_dates) < 5:
        print(f"  📊 历史数据不足（{len(existing_dates)}列），触发全量重建")
        need_rebuild = True

    if need_rebuild:
        # ── 全量重建：拉取近10个交易日 ──
        trade_dates = get_trade_dates(10)
        print(f"  📅 拉取 {len(trade_dates)} 个交易日数据...")

        days_data = []
        for td in trade_dates:
            dt_obj = datetime.strptime(td, "%Y%m%d")
            label = dt_obj.strftime("%m/%d")
            stocks = get_limit_up_by_date(td)
            time.sleep(0.3)  # 限流

            if stocks:
                sc = classify_by_sector(stocks)
                total = sum(sum(v.values()) for v in sc.values())
                print(f"    {label}: {total} 只涨停")
                days_data.append((label, sc))
            else:
                print(f"    {label}: 无数据（可能非交易日或休市）")
                days_data.append((label, {}))

        if not days_data:
            print("  ✗ 未获取到任何数据")
            return

        new_dates, new_sectors = build_heatmap(days_data)

    else:
        # ── 增量更新：只更新今天 ──
        today = datetime.now()
        today_str = today.strftime("%m/%d")
        today_yyyymmdd = today.strftime("%Y%m%d")

        limit_stocks = get_limit_up_by_date(today_yyyymmdd)
        if not limit_stocks:
            print("  ⚠️ 今日无涨停数据（休市或API异常），保持原数据不变")
            existing["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(OUTPUT, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            print(f"  ✅ 保持原数据: {OUTPUT}")
            return

        sector_counts = classify_by_sector(limit_stocks)
        print(f"  📊 今日({today_str}): {len(limit_stocks)} 只涨停")

        # 复制现有数据结构
        sector_map = {}
        for s in existing.get("sectors", []):
            sector_map[s["name"]] = list(s["data"])

        # 合并新旧板块
        all_sec = set(sector_map.keys()) | set(sector_counts.keys())
        sorted_sec = sorted(all_sec, key=lambda x: sum(sector_counts.get(x, {}).values()), reverse=True)[:15]

        # 日期：如果今天已存在则替换，否则追加
        ed = list(existing_dates)
        if today_str in ed:
            # 替换今天的列
            idx = len(ed) - 1 - ed[::-1].index(today_str)
            new_dates = ed[:idx] + [today_str]
        else:
            new_dates = (ed[-9:] + [today_str]) if len(ed) >= 9 else (ed + [today_str])
        new_dates = new_dates[-10:]

        new_sectors = []
        for sec in sorted_sec:
            old = list(sector_map.get(sec, []))
            # 对齐旧数据长度
            target_len = len(new_dates) - 1
            if len(old) > target_len:
                old = old[-target_len:]
            while len(old) < target_len:
                old.insert(0, 0)
            # 追加今日
            today_cnt = sum(sector_counts.get(sec, {}).values())
            new_sectors.append({"name": sec, "data": old + [today_cnt]})

    # ── 写入结果 ──
    result = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dates": new_dates if need_rebuild else new_dates,
        "sectors": new_sectors if need_rebuild else new_sectors,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ 热力矩阵: {len(result['dates'])} 日 × {len(result['sectors'])} 板块")
    for s in result["sectors"]:
        total = sum(s["data"])
        print(f"     {s['name']}: {s['data']}  (累计{total})")
    print(f"\n  输出: {OUTPUT}")


if __name__ == "__main__":
    from fetch_logger import record_success, record_failure
    try:
        main()
        record_success(__file__)
    except Exception as e:
        record_failure(__file__, str(e))
        raise
