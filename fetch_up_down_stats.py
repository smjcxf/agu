#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涨跌家数统计抓取脚本
收盘后拉取全A股行情，统计涨/跌/平家数，追加到 sh_sz_history.json
"""
import json
import os
import sys
from datetime import datetime

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATA_FILE = os.path.join(DATA_DIR, "sh_sz_history.json")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def fetch_up_down_stats():
    """获取涨跌家数统计"""
    try:
        import akshare as ak
        
        # 获取全A股实时行情
        log("正在获取全A股行情...")
        df = ak.stock_zh_a_spot_em()
        
        # 统计涨跌平
        up = len(df[df['涨跌幅'] > 0])
        down = len(df[df['涨跌幅'] < 0])
        flat = len(df[df['涨跌幅'] == 0])
        
        # 获取日期（MMDD格式，如6/22）
        today = datetime.now()
        date_str = f"{today.month}/{today.day}"
        
        log(f"今日 {date_str}: 涨{up} 跌{down} 平{flat}")
        
        return {
            "date": date_str,
            "up": up,
            "down": down,
            "flat": flat
        }
    except Exception as e:
        log(f"获取失败: {e}")
        return None

def update_data_file(stats):
    """更新数据文件"""
    if not stats:
        return False
    
    # 读取现有数据
    data = {"update_time": "", "amount_history": [], "daily_stats": []}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            log(f"读取现有数据失败: {e}")
    
    daily_stats = data.get("daily_stats", [])
    
    # 检查是否已存在今日数据
    today_str = stats["date"]
    existing_idx = None
    for i, d in enumerate(daily_stats):
        if d.get("date") == today_str:
            existing_idx = i
            break
    
    if existing_idx is not None:
        # 更新现有数据
        daily_stats[existing_idx] = stats
        log(f"更新今日数据: {today_str}")
    else:
        # 追加新数据
        daily_stats.append(stats)
        log(f"追加新数据: {today_str}")
    
    # 只保留最近60天
    if len(daily_stats) > 60:
        daily_stats = daily_stats[-60:]
    
    data["daily_stats"] = daily_stats
    data["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 保存
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    log(f"已保存: {DATA_FILE}")
    return True

def main():
    log("=" * 40)
    log("涨跌家数统计抓取开始")
    log("=" * 40)
    
    stats = fetch_up_down_stats()
    if stats:
        update_data_file(stats)
        log("✅ 完成")
    else:
        log("❌ 失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
