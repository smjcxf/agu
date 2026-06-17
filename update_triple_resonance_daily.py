"""
每日更新三线共振快照（增量更新）
只更新今天的数据，不重新生成历史
"""
import json
import os
from datetime import datetime

INDEX_HTML = 'E:/workspace/stock-scanner/index_master.html'
GOLD_POOL_FILE = 'E:/workspace/stock-scanner/data/gold_pool.json'
WATCH_FILE = 'E:/workspace/stock-scanner/data/watch_result.json'
SCAN_FILE = 'E:/workspace/stock-scanner/data/scan_result.json'
OUTPUT_FILE = 'E:/workspace/stock-scanner/data/triple_resonance_history.json'

def read_gold_pool(file_path):
    """从gold_pool.json读取数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取GOLD_POOL失败: {e}")
        return None

def read_watch_result(file_path):
    """从watch_result.json读取三线共振数据（补全GOLD_POOL可能遗漏的股票）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取WATCH_RESULT失败: {e}")
        return None

def read_scan_result(file_path):
    """从scan_result.json读取三线共振数据（补全GOLD_POOL可能遗漏的股票）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取SCAN_RESULT失败: {e}")
        return None

def get_latest_signals(data):
    """获取最新信号状态（和主页面逻辑一致）"""
    history = data.get('history', [])
    latest = history[-1] if history else {}
    
    def get_signal(key):
        val = latest.get(key)
        if val is None:
            val = data.get(key)
        return val or False
    
    signals = {
        '缠论买_日K': get_signal('缠论买_日K'),
        '金钻_黄柱': get_signal('金钻_黄柱'),
        '金钻_起涨': get_signal('金钻_起涨'),
        '四量图_机构变红': get_signal('四量图_机构变红'),
        '上涨趋势': get_signal('上涨趋势')
    }

    # 金钻信号 = 黄柱 OR 起涨 (与 scanner.py 第1507行一致)
    jz_signal = signals['金钻_黄柱'] or signals['金钻_起涨']
    signal_count = sum([signals['缠论买_日K'], jz_signal, signals['四量图_机构变红'], signals['上涨趋势']])
    return signals, signal_count

def normalize_code(code):
    """去掉前缀统一比较"""
    return (code or '').replace('sh_', '').replace('sz_', '').replace('hk_', '')

def main():
    print("=== 每日更新三线共振快照 ===")
    print(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # 读取GOLD_POOL
    gold_pool = read_gold_pool(GOLD_POOL_FILE)
    # 同时读WATCH_RESULT（补全可能遗漏的股票）
    watch_result = read_watch_result(WATCH_FILE)
    # 同时读SCAN_RESULT（补全可能遗漏的股票）
    scan_result = read_scan_result(SCAN_FILE)

    if not gold_pool and not watch_result and not scan_result:
        print("错误：无法读取任何数据源")
        return

    # 用dict去重，key=normalize_code
    today_stocks_map = {}

    # 1. 从GOLD_POOL提取
    if gold_pool and 'stocks' in gold_pool:
        for code, data in gold_pool['stocks'].items():
            signals, signal_count = get_latest_signals(data)
            if signal_count >= 3:
                latest = data.get('history', [])
                latest_item = latest[-1] if latest else {}
                norm = normalize_code(code)
                today_stocks_map[norm] = {
                    'code': code,
                    'name': data.get('name', ''),
                    'close': latest_item.get('close', data.get('close', 0)),
                    'pct_chg': latest_item.get('pct_chg', data.get('pct_chg', 0)),
                    '缠论买_日K': signals['缠论买_日K'],
                    '金钻_起涨': signals['金钻_起涨'],
                    '金钻_黄柱': signals['金钻_黄柱'],
                    '四量图_机构变红': signals['四量图_机构变红'],
                    '上涨趋势': signals['上涨趋势'],
                    'signal_count': signal_count,
                    'enter_date': data.get('enter_date', ''),
                    'duration_days': data.get('duration_days', 0),
                    '_source': 'GOLD'
                }
        print(f"GOLD_POOL提取: {len([k for k,v in today_stocks_map.items() if v.get('_source')=='GOLD'])}只")

    # 2. 从WATCH_RESULT补充（信号数>=3且不在GOLD_POOL中的）
    if watch_result and 'triple_signals' in watch_result:
        for s in watch_result['triple_signals']:
            sig_cnt = s.get('signal_count', 0)
            if sig_cnt >= 3:
                norm = normalize_code(s.get('code', ''))
                # 只在不存在或信号数更高时更新
                existing = today_stocks_map.get(norm)
                if not existing or (sig_cnt > existing.get('signal_count', 0)):
                    today_stocks_map[norm] = {
                        'code': s.get('code', ''),
                        'name': s.get('name', ''),
                        'close': s.get('close', s.get('latest', {}).get('close', 0)),
                        'pct_chg': s.get('pct_chg', 0),
                        '缠论买_日K': s.get('缠论买_日K', False),
                        '金钻_起涨': s.get('金钻_起涨', False) or s.get('金钻_黄柱', False),
                        '四量图_机构变红': s.get('四量图_机构变红', False),
                        '上涨趋势': s.get('上涨趋势', False),
                        'signal_count': sig_cnt,
                        'enter_date': '',
                        'duration_days': 0,
                        '_source': 'WATCH'
                    }
        watch_added = len([k for k, v in today_stocks_map.items() if v.get('_source') == 'WATCH'])
        print(f"WATCH_RESULT补充: {watch_added}只（新增/升级）")

    # 3. 从SCAN_RESULT补充 — 从 results 中筛选三线共振=True 的股票
    if scan_result and 'results' in scan_result:
        for s in scan_result['results']:
            if s.get('三线共振'):  # 扫描结果中的三线共振标记
                sig_cnt = s.get('signal_count', 0)
                if sig_cnt >= 3:
                    norm = normalize_code(s.get('code', ''))
                    existing = today_stocks_map.get(norm)
                    if not existing or (sig_cnt > existing.get('signal_count', 0)):
                        today_stocks_map[norm] = {
                            'code': s.get('code', ''),
                            'name': s.get('name', ''),
                            'close': s.get('close', s.get('latest', {}).get('close', 0)),
                            'pct_chg': s.get('pct_chg', 0),
                            '缠论买_日K': s.get('缠论买_日K', False),
                            '金钻_起涨': s.get('金钻_起涨', False) or s.get('金钻_黄柱', False),
                            '四量图_机构变红': s.get('四量图_机构变红', False),
                            '上涨趋势': s.get('上涨趋势', False),
                            'signal_count': sig_cnt,
                            'enter_date': '',
                            'duration_days': 0,
                            '_source': 'SCAN'
                        }
        scan_added = len([k for k, v in today_stocks_map.items() if v.get('_source') == 'SCAN'])
        print(f"SCAN_RESULT补充: {scan_added}只（新增/升级）")

    today_stocks = list(today_stocks_map.values())

    # 周末非交易日，跳过不写入
    today_dt = datetime.now()
    if today_dt.weekday() >= 5:
        print(f"今天 {today_dt.strftime('%Y-%m-%d')} 是周末（非交易日），跳过更新")
        return
    # 非交易时间（9:30前）跳过不写入，避免用昨日数据污染今日
    current_hour = today_dt.hour + today_dt.minute / 60
    if current_hour < 9.5:
        print(f"当前 {today_dt.strftime('%H:%M')}，尚未开盘（开盘时间 9:30），跳过更新")
        return
    today_str = today_dt.strftime('%Y-%m-%d')
    
    print(f"今天三线共振: {len(today_stocks)}只")
    for s in today_stocks:
        print(f"  {s['code']} {s['name']}: {s['signal_count']}/4")
    
    # 读取已有历史
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = {}
    
    # 更新今天的数据
    history[today_str] = today_stocks
    
    # 保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"\n快照已保存: {OUTPUT_FILE}")
    print(f"历史日期数: {len(history)}")
    print("\n=== 完成 ===")

if __name__ == '__main__':
    main()
