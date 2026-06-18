"""
生成三线共振历史数据（从2026-06-01开始）
- 处理history数组中的重复日期（使用最后一次出现）
- 历史日期：从history数组读取
- 今天：从顶层字段读取
- 缺失pct_chg自动从新浪日K线API补全
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta

# 新浪日K线缓存（symbol → [{day, close}]）
_SINA_CACHE = {}

def _fetch_day_pct_chg(code, date_str):
    """从新浪/Tencent日K线API获取指定日期涨跌幅。返回 float 或 None"""
    market_map = {'sh_': 'sh', 'sz_': 'sz', 'bj_': 'bj', 'hk_': 'hk'}
    prefix = ''
    for p in market_map:
        if code.startswith(p):
            prefix = market_map[p]
            code_short = code[len(p):]
            break
    if not prefix:
        return None

    # 港股用腾讯API
    if prefix == 'hk':
        cache_key = f'hk_{code_short}'
        if cache_key not in _SINA_CACHE:
            try:
                url = f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=hk{code_short},day,,,60,qfq'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read().decode('utf-8'))
                klines = data.get('data', {}).get(f'hk{code_short}', {}).get('day', [])
                _SINA_CACHE[cache_key] = klines
            except Exception:
                _SINA_CACHE[cache_key] = []
        klines = _SINA_CACHE[cache_key]
        for i, k in enumerate(klines):
            if k[0] == date_str and i > 0:
                prev_close = float(klines[i - 1][2])
                close = float(k[2])
                return round((close - prev_close) / prev_close * 100, 2)
        return None

    # A股用新浪API
    symbol = f'{prefix}{code_short}'
    if symbol not in _SINA_CACHE:
        try:
            url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen=60'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode('utf-8'))
            _SINA_CACHE[symbol] = data
        except Exception:
            _SINA_CACHE[symbol] = []
    data = _SINA_CACHE[symbol]
    for i, d in enumerate(data):
        if d.get('day') == date_str and i > 0:
            prev_close = float(data[i - 1]['close'])
            close = float(d['close'])
            return round((close - prev_close) / prev_close * 100, 2)
    return None

INDEX_HTML = 'E:/workspace/stock-scanner/index_master.html'
GOLD_POOL_FILE = 'E:/workspace/stock-scanner/data/gold_pool.json'
OUTPUT_FILE = 'E:/workspace/stock-scanner/data/triple_resonance_history.json'
START_DATE = '2026-06-01'
END_DATE = datetime.now().strftime('%Y-%m-%d')

def read_gold_pool(file_path):
    """从gold_pool.json读取数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取GOLD_POOL失败: {e}")
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
        '金钻_起涨': get_signal('金钻_起涨'),
        '四量图_机构变红': get_signal('四量图_机构变红'),
        '上涨趋势': get_signal('上涨趋势')
    }
    
    signal_count = sum(1 for v in signals.values() if v)
    return signals, signal_count

def generate_snapshots(gold_pool):
    snapshots = {}
    stocks = gold_pool.get('stocks', {})
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 构建每只股票的每日信号状态（处理重复日期）
    stock_daily = {}  # {code: {date: data}}
    
    for code, data in stocks.items():
        stock_daily[code] = {}
        seen_dates = {}  # {date: index_in_array}
        
        for idx, item in enumerate(data.get('history', [])):
            item_date = item.get('date', '')
            if not item_date:
                continue
            
            # 检查信号字段
            signals = {
                '缠论买_日K': item.get('缠论买_日K', False),
                '金钻_起涨': item.get('金钻_起涨', False),
                '四量图_机构变红': item.get('四量图_机构变红', False),
                '上涨趋势': item.get('上涨趋势', False)
            }
            signal_count = sum(1 for v in signals.values() if v)
            
            # 如果日期重复，使用最后一次（覆盖）
            stock_daily[code][item_date] = {
                'signals': signals,
                'signal_count': signal_count,
                'close': item.get('close', 0),
                'pct_chg': item.get('pct_chg', 0)
            }
    
    # 生成每日快照
    current = datetime.strptime(START_DATE, '%Y-%m-%d')
    end = datetime.strptime(END_DATE, '%Y-%m-%d')
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        if current.weekday() < 5:  # 只处理交易日
            daily_stocks = []
            
            # 当日数据不读历史，统一由WATCH_DATA+SCAN_DATA补充（避免GOLD_POOL历史残留假数据）
            if date_str != today:
                for code, data in stocks.items():
                    use_data = None
                    
                    if date_str in stock_daily.get(code, {}):
                        # 历史数据
                        use_data = stock_daily[code][date_str]
                    else:
                        # 最近的历史: 在股票的历史数据中找到信号最强的entries
                        # pct_chg不可继承，先设为None，后续从API补全
                        candidate_dates = sorted(
                            [d for d in stock_daily.get(code, {}).keys() if d <= date_str],
                            reverse=True
                        )
                        if candidate_dates:
                            use_data = dict(stock_daily[code][candidate_dates[0]])
                            use_data['pct_chg'] = None
                    
                    if use_data and use_data['signal_count'] >= 3:
                        # fallback时尝试从新浪API补全pct_chg
                        if use_data.get('pct_chg') is None:
                            fetched = _fetch_day_pct_chg(code, date_str)
                            if fetched is not None:
                                use_data['pct_chg'] = fetched
                        # 计算连续共振天数
                        consecutive = 0
                        for d in reversed(sorted(stock_daily.get(code, {}).keys())):
                            if d <= date_str:
                                if stock_daily[code][d]['signal_count'] >= 3:
                                    consecutive += 1
                                else:
                                    break
                        daily_stocks.append({
                            'code': code,
                        'name': data.get('name', ''),
                        'close': use_data['close'],
                        'pct_chg': use_data['pct_chg'],
                        '缠论买_日K': use_data['signals']['缠论买_日K'],
                        '金钻_起涨': use_data['signals']['金钻_起涨'],
                        '四量图_机构变红': use_data['signals']['四量图_机构变红'],
                        '上涨趋势': use_data['signals']['上涨趋势'],
                        'signal_count': use_data['signal_count'],
                        'score': use_data.get('score', use_data['signal_count'] * 3),
                        'days_in_resonance': consecutive,
                        'enter_date': data.get('enter_date', ''),
                        'duration_days': data.get('duration_days', 0)
                    })
            
            snapshots[date_str] = daily_stocks
            print(f"  {date_str}: {len(daily_stocks)}只")
        
        current += timedelta(days=1)
    
    return snapshots

def main():
    print("=== 生成三线共振历史数据（修复版） ===\n")

    gold_pool = read_gold_pool(GOLD_POOL_FILE)
    if not gold_pool or 'stocks' not in gold_pool:
        print("错误：无法读取GOLD_POOL数据")
        return

    # 加载watch_data（精监三线共振数据，可能包含金池外的股票）
    watch_file = os.path.join(os.path.dirname(GOLD_POOL_FILE), 'watch_result.json')
    watch_data = None
    if os.path.exists(watch_file):
        with open(watch_file, 'r', encoding='utf-8') as f:
            watch_data = json.load(f)
        print(f"WATCH_DATA三线共振: {len(watch_data.get('triple_signals', []))}只")

    print(f"GOLD_POOL股票数: {len(gold_pool['stocks'])}")
    print(f"\n生成历史快照 ({START_DATE} ~ {END_DATE})...")

    snapshots = generate_snapshots(gold_pool)

    # 补充：将watch_data + scan_data中的三线共振股并入当天快照（当日唯一权威来源）
    def merge_triple_signals(source, source_name):
        if not source or not source.get('triple_signals'):
            return
        today = datetime.now()
        if today.weekday() < 5:
            today_str = today.strftime('%Y-%m-%d')
            if today_str not in snapshots:
                snapshots[today_str] = []
            existing_codes = {s['code'].replace('sh_','').replace('sz_','').replace('hk_','') for s in snapshots[today_str]}
            added = 0
            for ts in source['triple_signals']:
                code = ts.get('code', '')
                code_normalized = code.replace('sh_','').replace('sz_','').replace('hk_','')
                if code_normalized in existing_codes:
                    continue
                snapshots[today_str].append({
                    'code': code,
                    'name': ts.get('name', ''),
                    'close': ts.get('close', 0),
                    'pct_chg': ts.get('pct_chg', 0),
                    '缠论买_日K': ts.get('缠论买_日K', False),
                    '金钻_起涨': ts.get('金钻_起涨', False),
                    '四量图_机构变红': ts.get('四量图_机构变红', False),
                    '上涨趋势': ts.get('上涨趋势', False),
                    'signal_count': ts.get('signal_count', 3),
                    'score': ts.get('score', ts.get('signal_count', 3) * 3),
                    'days_in_resonance': 1,
                    'enter_date': '',
                    'duration_days': 0
                })
                existing_codes.add(code_normalized)
                added += 1
            if added:
                print(f"  {today_str}: {source_name}补充 {added}只 → 共{len(snapshots[today_str])}只")

    merge_triple_signals(watch_data, 'WATCH')
    
    # 加载SCAN_DATA补充
    scan_file = os.path.join(os.path.dirname(GOLD_POOL_FILE), 'scan_result.json')
    scan_data = None
    if os.path.exists(scan_file):
        with open(scan_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        print(f"SCAN_DATA三线共振: {len(scan_data.get('triple_signals', []))}只")
    merge_triple_signals(scan_data, 'SCAN')
    
    # 合并已有数据：已有文件中的非空数据优先保留（新生成的空数组不覆盖旧数据）
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        kept = 0
        for date, data in existing.items():
            dt = datetime.strptime(date, '%Y-%m-%d')
            if dt.weekday() >= 5:  # 跳过周末
                continue
            # 如果新生成的为空，用旧的；如果旧的有数据，以旧的为准（历史数据更准确）
            if date not in snapshots or (not snapshots[date] and data):
                snapshots[date] = data
                kept += 1
        print(f"加载已有数据: {len(existing)}个日期（保留{kept}个）")
    
    # 保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2)
    
    print(f"\n历史数据已保存: {OUTPUT_FILE}")
    print(f"总日期数: {len(snapshots)}")
    
    # 统计
    total_stocks = set()
    for date, stocks in snapshots.items():
        for s in stocks:
            total_stocks.add(s['code'])
    print(f"出现过三线共振的股票总数: {len(total_stocks)}")
    print("\n=== 完成 ===")

if __name__ == '__main__':
    main()
