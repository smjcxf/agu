"""
将宏观数据和UI注入到 index.html
四列布局：指标 | 数值 | 说明 | 更新

排序逻辑（2026-06-14调整）：
  货币政策(每日→月度) → 全球宏观(每日高频) → 市场情绪 → 经济基本面(周/月低频)
"""

import json
import re

DIST_HTML = 'E:/workspace/stock-scanner/dist/index.html'
MASTER_HTML = 'E:/workspace/stock-scanner/dist/index_master.html'
MACRO_JSON = 'E:/workspace/stock-scanner/data/macro_data.json'


def load_html(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def save_html(path, html):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


# ============ 1) 内嵌 MACRO_DATA 变量（幂等，不重复声明） ============
def inject_macro_data_var(html):
    with open(MACRO_JSON, 'r', encoding='utf-8') as f:
        macro_data = json.load(f)

    macro_json_str = json.dumps(macro_data, ensure_ascii=False, indent=0)
    new_decl = '\nwindow.MACRO_DATA = ' + macro_json_str + ';\n'

    # 用括号计数法精确查找已存在的 MACRO_DATA 声明（支持 window.MACRO_DATA 或 const MACRO_DATA）
    import re as _re
    # 找 marker 位置
    marker_match = _re.search(r'(?:const\s+|window\.)?MACRO_DATA\s*=\s*\{', html)
    if marker_match:
        start = marker_match.start()
        # 用括号计数法找到匹配的 }
        i = marker_match.end() - 1  # 回退到 '{'
        count = 1
        while i < len(html) and count > 0:
            i += 1
            if html[i] == '{':
                count += 1
            elif html[i] == '}':
                count -= 1
        # 找到末尾的 ;
        end = i + 1
        while end < len(html) and html[end] in ' ;\n\r\t':
            end += 1
        # 替换
        html = html[:start] + new_decl + html[end:]
        print('✅ MACRO_DATA 变量已更新（括号计数替换）')
    else:
        # 不存在 → 插入到 ETF_SUBSCRIPTION 后面
        etf_end = _re.search(r'const ETF_SUBSCRIPTION\s*=\s*\{.*?\};', html, _re.DOTALL)
        if etf_end:
            insert_pos = etf_end.end()
            html = html[:insert_pos] + '\n' + new_decl + html[insert_pos:]
            print('✅ MACRO_DATA 变量已内嵌（新插入）')
        else:
            print('⚠️ WARN: 未找到 ETF_SUBSCRIPTION，跳过变量注入')
    return html


# ============ 2) 宏观观测表格 HTML（四列完整版 - 重排后） ============
# 排序逻辑：货币政策(每日→月度) → 全球宏观(每日高频) → 市场情绪 → 经济基本面(周/月低频)
# 月度指标"更新"列带 id="upd-xxx"，用于⭐标记渲染
MACRO_TABLE_HTML = """
<!-- 宏观观测 -->
<div class="sh-section accent-bar accent-cyan">
  <div class="sh-section-title" style="font-size:15px;display:flex;align-items:center;justify-content:space-between;">🌍 宏观观测 <span style="font-size:11px;font-weight:400;color:#888;margin-left:8px;flex:1;" id="macroUpdateTime"></span><span style="font-size:11px;font-weight:400;color:#888;" id="macroStarLegend"></span></div>

  <table style="width:100%;border-collapse:collapse;font-size:13px;color:#2c3e50;">
    <!-- 货币政策 -->
    <tr><td colspan="4" style="background:#1a2a3a;padding:6px 12px;color:#00acc1;font-weight:500;border-radius:4px 4px 0 0;font-size:12px;">💰 货币政策（最重要，直接影响A股流动性）</td></tr>
    <tr style="color:#34495e;">
      <th style="padding:5px 12px;text-align:left;width:28%;">指标</th>
      <th style="padding:5px 12px;text-align:center;width:25%;">数值</th>
      <th style="padding:5px 12px;text-align:left;width:32%;">说明</th>
      <th style="padding:5px 12px;text-align:right;width:15%;">更新</th>
    </tr>
    <!-- 每日指标排在前面 -->
    <tr style="border-top:0.5px solid #333;"><td style="padding:6px 12px;">10Y中国国债收益率</td><td style="padding:6px 12px;text-align:center;" id="m-cn-bond">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">无风险利率，估值锚</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">每日</td></tr>
    <tr><td style="padding:6px 12px;">10Y美国国债收益率</td><td style="padding:6px 12px;text-align:center;" id="m-us-bond">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">全球资产定价锚</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">每日</td></tr>
    <tr><td style="padding:6px 12px;">央行公开市场操作</td><td style="padding:6px 12px;text-align:center;" id="m-omo">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">流动性投放(正)/回笼(负)</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">每日</td></tr>
    <tr><td style="padding:6px 12px;">Shibor隔夜/1周</td><td style="padding:6px 12px;text-align:center;" id="m-shibor">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">银行间拆借利率</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">每日</td></tr>
    <!-- 月度指标排在后面（带⭐标记位） -->
    <tr><td style="padding:6px 12px;">LPR利率 (1Y/5Y)</td><td style="padding:6px 12px;text-align:center;" id="m-lpr">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">政策利率信号</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;" id="upd-lpr">月度</td></tr>
    <tr><td style="padding:6px 12px;">M1-M2剪刀差</td><td style="padding:6px 12px;text-align:center;" id="m-m1m2">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">货币活性/流动性环境</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;" id="upd-m2">月度</td></tr>

    <!-- 全球宏观（每日高频，紧跟货币政策） -->
    <tr><td colspan="4" style="background:#1a2a3a;padding:6px 12px;color:#ff9800;font-weight:500;margin-top:4px;font-size:12px;">🌐 全球宏观（影响外资流向）</td></tr>
    <tr style="color:#34495e;"><th style="padding:5px 12px;text-align:left;width:28%;">指标</th><th style="padding:5px 12px;text-align:center;width:25%;">数值</th><th style="padding:5px 12px;text-align:left;width:32%;">说明</th><th style="padding:5px 12px;text-align:right;width:15%;">更新</th></tr>
    <tr style="border-top:0.5px solid #333;"><td style="padding:6px 12px;">VIX恐慌指数</td><td style="padding:6px 12px;text-align:center;" id="g-vix">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">全球风险偏好</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">每日</td></tr>
    <tr><td style="padding:6px 12px;">美元指数 DXY</td><td style="padding:6px 12px;text-align:center;" id="g-dxy">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">强美元→资本流出</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">每日</td></tr>
    <tr><td style="padding:6px 12px;">离岸人民币(CNH)</td><td style="padding:6px 12px;text-align:center;" id="g-usdcnh">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">汇率走势→外资流向</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">每日</td></tr>
    <tr><td style="padding:6px 12px;">中美利差(10Y)</td><td style="padding:6px 12px;text-align:center;" id="m-spread">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">资本流动核心驱动</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">每日</td></tr>

    <!-- 市场情绪（移到经济基本面前面） -->
    <tr><td colspan="4" style="background:#1a2a3a;padding:6px 12px;color:#e91e63;font-weight:500;margin-top:4px;font-size:12px;">📈 市场情绪（反映投资者行为）</td></tr>
    <tr style="color:#34495e;"><th style="padding:5px 12px;text-align:left;">指标</th><th style="padding:5px 12px;text-align:center;">数值</th><th style="padding:5px 12px;text-align:left;">说明</th><th style="padding:5px 12px;text-align:right;">更新</th></tr>
    <tr style="border-top:0.5px solid #333;"><td style="padding:6px 12px;">新增投资者人数</td><td style="padding:6px 12px;text-align:center;" id="mt-investors">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">散户入场热度</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;" id="upd-investors">月度</td></tr>

    <!-- 经济基本面（排在最后，周/月低频数据） -->
    <tr><td colspan="4" style="background:#1a2a3a;padding:6px 12px;color:#4caf50;font-weight:500;margin-top:4px;font-size:12px;">📊 经济基本面（影响企业盈利预期）</td></tr>
    <tr style="color:#34495e;"><th style="padding:5px 12px;text-align:left;">指标</th><th style="padding:5px 12px;text-align:center;">数值</th><th style="padding:5px 12px;text-align:left;">说明</th><th style="padding:5px 12px;text-align:right;">更新</th></tr>
    <tr style="border-top:0.5px solid #333;"><td style="padding:6px 12px;">IPC库存/贷款额</td><td style="padding:6px 12px;text-align:center;" id="e-ipo">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">供给端压力</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;">周度</td></tr>
    <tr><td style="padding:6px 12px;">制造业PMI</td><td style="padding:6px 12px;text-align:center;" id="e-pmi">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">经济荣枯线（>50扩张）</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;" id="upd-pmi">月度</td></tr>
    <tr><td style="padding:6px 12px;">CPI同比 / PPI同比</td><td style="padding:6px 12px;text-align:center;" id="e-cpi">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">通胀压力→政策空间</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;" id="upd-cpi">月度</td></tr>
    <tr><td style="padding:6px 12px;">社融规模</td><td style="padding:6px 12px;text-align:center;" id="e-szr">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">实体经济融资需求</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;" id="upd-szr">月度</td></tr>
    <tr><td style="padding:6px 12px;">出口增速(同比)</td><td style="padding:6px 12px;text-align:center;" id="e-export">--</td><td style="padding:6px 12px;color:#5d6d7e;font-size:12px;">外需强弱</td><td style="padding:6px 12px;text-align:right;color:#7f8c8d;font-size:11px;" id="upd-export">月度</td></tr>
  </table>
</div>
"""


def inject_macro_table(html):
    import re as _re
    # 先检查是否已有宏观观测表格
    if '<!-- 宏观观测 -->' in html:
        # 确保标题行包含 macroStarLegend（向后兼容旧版）
        if 'macroStarLegend' not in html:
            # 精确匹配宏观观测标题（含 🌍 宏观观测 特征文字）
            old_title = '<div class="sh-section-title" style="font-size:15px;">🌍 宏观观测 <span style="font-size:11px;font-weight:400;color:#888;margin-left:8px;" id="macroUpdateTime"></span></div>'
            if old_title in html:
                html = html.replace(old_title, '<div class="sh-section-title" style="font-size:15px;display:flex;align-items:center;justify-content:space-between;">🌍 宏观观测 <span style="font-size:11px;font-weight:400;color:#888;margin-left:8px;flex:1;" id="macroUpdateTime"></span><span style="font-size:11px;font-weight:400;color:#888;" id="macroStarLegend"></span></div>')
                print('✅ 宏观观测标题行已更新（含⭐图例）')
            else:
                # 尝试 regex 模糊匹配
                html = _re.sub(
                    r'<div class="sh-section-title"[^>]*>🌍 宏观观测[\s\S]*?id="macroUpdateTime"[\s\S]*?</div>',
                    '<div class="sh-section-title" style="font-size:15px;display:flex;align-items:center;justify-content:space-between;">🌍 宏观观测 <span style="font-size:11px;font-weight:400;color:#888;margin-left:8px;flex:1;" id="macroUpdateTime"></span><span style="font-size:11px;font-weight:400;color:#888;" id="macroStarLegend"></span></div>',
                    html,
                    count=1
                )
                print('✅ 宏观观测标题行已更新（regex，含⭐图例）')
        else:
            print('ℹ️ 宏观观测表格已存在，标题行已包含图例，跳过')
        return html
    # 插入到成交金额曲线图之前（宏观观测排最前）
    # 策略1：找成交金额section的起始位置
    marker1 = '<!-- 成交金额曲线图 -->'
    if marker1 in html:
        html = html.replace(marker1, MACRO_TABLE_HTML + '\n    ' + marker1)
        print('✅ 宏观观测表格HTML已插入（成交金额图前）')
        return html
    # 策略2：fallback 在个股查询前插入
    marker2 = '<!-- 个股查询 -->'
    if marker2 in html:
        html = html.replace(marker2, MACRO_TABLE_HTML + '\n  ' + marker2)
        print('✅ 宏观观测表格HTML已插入（个股查询前，fallback）')
        return html
    print('⚠️ WARN: 未找到插入标记')
    return html


# ============ 3) 宏观异动速报（Python端生成分析结论HTML） ============
def generate_macro_alert_html():
    """读取 macro_data.json，生成仿市场异动速览风格的分析结论HTML"""
    import json as _json
    with open(MACRO_JSON, 'r', encoding='utf-8') as _f:
        d = _json.load(_f)
    mon = d.get('monetary', {})
    eco = d.get('economy', {})
    mt = d.get('market_sentiment', {})
    g = d.get('global_macro', {})

    analyses = []

    # 流动性（国债收益率）
    cn_bond = mon.get('cn_bond_10y')
    if cn_bond and cn_bond.get('value'):
        v = cn_bond['value']
        if v < 1.8:
            analyses.append(('流动性', f'10年期国债收益率降至{v:.2f}%，处于历史低位，流动性环境宽松，利好A股估值修复。', '#4caf50'))
        elif v < 2.5:
            analyses.append(('流动性', f'10年期国债收益率{v:.2f}%，利率水平适中，市场资金面总体充裕。', '#888'))
        else:
            analyses.append(('流动性', f'10年期国债收益率升至{v:.2f}%，利率上行压力增加，需关注流动性边际变化。', '#e65100'))

    # 中美利差
    spread = mon.get('cn_us_spread')
    if spread and spread.get('value') is not None:
        s = spread['value']
        if s < -2:
            analyses.append(('利差', f'中美利差倒挂达{s:.1f}%，人民币汇率承压，外资流入动力偏弱。', '#d06b82'))
        elif s < -0.5:
            analyses.append(('利差', f'中美利差为负值({s:.1f}%)，资本外流压力仍存但幅度收窄。', '#ff9800'))
        elif s >= 0:
            analyses.append(('利差', f'中美利差转正({s:.1f}%)，人民币资产吸引力增强，外资有望回流。', '#4caf50'))

    # VIX恐慌指数
    vix = g.get('vix')
    if vix and vix.get('value'):
        vx = vix['value']
        if vx < 18:
            analyses.append(('风险偏好', f'VIX指数仅{vx:.0f}，全球风险偏好较高，权益资产配置意愿强。', '#4caf50'))
        elif vx < 25:
            analyses.append(('风险偏好', f'VIX指数{vx:.0f}，市场波动率中性，无极端避险情绪。', '#888'))
        else:
            analyses.append(('风险偏好', f'VIX指数飙至{vx:.0f}，全球恐慌情绪升温，注意控制仓位。', '#d06b82'))

    # 离岸人民币
    usdcnh = g.get('usdcnh')
    if usdcnh and usdcnh.get('price') is not None:
        price = usdcnh['price']
        if price > 7.3:
            analyses.append(('汇率', f'离岸人民币跌破7.30关口，贬值压力加大，北向资金可能承压。', '#d06b82'))
        elif price > 7.15:
            analyses.append(('汇率', f'离岸人民币在{price:.2f}附近震荡，汇率压力可控但不乐观。', '#ff9800'))
        else:
            analyses.append(('汇率', f'离岸人民币稳定在{price:.2f}下方，汇率压力缓解。', '#4caf50'))

    # PMI
    pmi = eco.get('pmi')
    if pmi and pmi.get('value') is not None:
        pv = pmi['value']
        if pv >= 50:
            analyses.append(('经济景气', f'制造业PMI为{pv:.1f}（荣枯线上方），经济扩张态势延续。', '#4caf50'))
        elif pv >= 48.5:
            analyses.append(('经济景气', f'制造业PMI{pv:.1f}（荣枯线下方），经济增长动能偏弱但未恶化。', '#ff9800'))
        else:
            analyses.append(('经济景气', f'制造业PMI仅{pv:.1f}（显著低于荣枯线），经济下行压力较大。', '#d06b82'))

    # 社融
    sf = eco.get('social_financing')
    if sf and sf.get('value') is not None:
        sv, sc = sf['value'], sf.get('change_pct', 0)
        direction = '回升' if sc > 0 else ('回落' if sc < 0 else '持平')
        if sc < -5:
            analyses.append(('信用扩张', f'社融规模{sv:.0f}亿（同比{direction}{abs(sc):.0f}%），信贷需求明显走弱，政策发力空间打开。', '#d06b82'))
        elif sc < 0:
            analyses.append(('信用扩张', f'社融规模{sv:.0f}亿（同比{direction}{abs(sc):.0f}%），信用扩张节奏放缓。', '#ff9800'))
        else:
            analyses.append(('信用扩张', f'社融规模{sv:.0f}亿（同比+{sc:.0f}%），融资需求回暖，经济活力改善信号。', '#4caf50'))

    # 新增投资者
    inv = mt.get('new_investors')
    if inv and inv.get('value') is not None:
        iv, ic = inv['value'], inv.get('change', 0) or 0
        if ic > 3:
            analyses.append(('散户情绪', f'新增投资者{iv:.2f}万（周增{ic:+.2f}万），散户入场热情高涨。', '#c62828'))
        elif ic > 0:
            analyses.append(('散户情绪', f'新增投资者{iv:.2f}万（小幅增长{ic:+.2f}万），入场意愿温和。', '#888'))
        else:
            analyses.append(('散户情绪', f'新增投资者{iv:.2f}万（减少{abs(ic):.2f}万），散户参与度下降。', '#455a64'))

    # OMO
    omo = mon.get('open_market_operation')
    if omo and omo.get('net_inflow') is not None:
        ni = omo['net_inflow']
        if ni > 500:
            analyses.append(('央行操作', f'央行公开市场净投放{ni:.0f}亿，主动释放流动性呵护市场。', '#4caf50'))
        elif ni > 0:
            analyses.append(('央行操作', f'央行公开市场净投放{ni:.0f}亿，维持合理充裕的流动性。', '#888'))
        elif ni < -500:
            analyses.append(('央行操作', f'央行回笼资金{abs(ni):.0f}亿，流动性边际收紧需关注。', '#e65100'))
        else:
            analyses.append(('央行操作', '央行公开市场操作基本平衡，流动性保持稳定。', '#888'))

    # 过滤：只保留有异常/关注的分析（排除正常/中性颜色）
    # #d06b82 = 严重红色异动, #ff9800/#e65100/#c62828 = 橙色关注
    # #4caf50 = 正常绿色, #888/#455a64 = 中性灰色 → 过滤掉
    normal_colors = {'#4caf50', '#888', '#455a64'}
    alerts = [(l, t, c) for l, t, c in analyses if c not in normal_colors]

    # 构建HTML — 仿市场异动速览格式：只显示异常项
    h = '<div style="font-size:13px;line-height:2;">'
    if alerts:
        for label, text, color in alerts:
            h += f'<div style="margin-bottom:4px;padding:2px 0;">'
            h += f'<span style="color:{color};font-weight:600;">【{label}】</span> '
            h += f'<span style="color:#444;">{text}</span></div>'
    else:
        h += '<div style="color:#4caf50;font-weight:600;padding:8px 0;">✅ 当前无异常宏观信号，各项指标运行平稳</div>'
    if not analyses:
        h += '<div style="color:#999;padding:8px 0;">暂无可分析的宏观数据</div>'
    h += '</div>'

    update_time = d.get('update_time', '')
    return h, update_time, len(analyses)


def inject_macro_alert(html):
    """将宏观异动速报的分析结论HTML直接写入卡片内容区"""
    content_html, update_time, count = generate_macro_alert_html()

    # 替换空的content div为带内容的版本
    old_content = '<div id="macroAlertContent" style="font-size:13px;line-height:1.8;"></div>'
    new_content = f'<div id="macroAlertContent" style="font-size:13px;line-height:1.8;">{content_html}</div>'
    if old_content in html:
        html = html.replace(old_content, new_content)
        print(f'✅ 宏观异动速报已注入（{count}条分析结论）')
    else:
        # fallback: 找 id="macroAlertContent" 所在div，匹配到同级的 </div>（通过括号/层级计数）
        import re as _re
        start_match = _re.search(r'<div id="macroAlertContent"[^>]*>', html)
        if start_match:
            pos = start_match.end()
            depth = 1
            while pos < len(html) and depth > 0:
                next_open = html.find('<div', pos)
                next_close = html.find('</div>', pos)
                if next_close == -1:
                    break
                if next_open != -1 and next_open < next_close:
                    depth += 1
                    pos = next_open + 4
                else:
                    depth -= 1
                    if depth == 0:
                        # 替换 macroAlertContent 及其内容
                        html = html[:start_match.start()] + f'<div id="macroAlertContent" style="font-size:13px;line-height:1.8;">{content_html}</div>' + html[next_close + 6:]
                        break
                    pos = next_close + 6
        print(f'✅ 宏观异动速报已注入（fallback模式，{count}条分析结论）')

    # 更新时间戳（用正则匹配，兼容已有残缺内容）
    import re as _re2
    html = _re2.sub(
        r'id="macroAlertTime"[^>]*>.*?</span>',
        f'id="macroAlertTime">更新时间：{update_time}</span>',
        html
    )

    return html


# ============ 4) 渲染脚本（幂等，含⭐标记渲染+数值填充，不含速报卡片渲染） ==========
RENDER_JS = """<script>
(function(){
  if(typeof window.MACRO_DATA === "undefined") return;
  const m = window.MACRO_DATA;
  var el = document.getElementById("macroUpdateTime");
  if(el) el.textContent = "更新时间：" + (m.update_time||"").slice(0,16);
  var leg = document.getElementById("macroStarLegend");
  if(leg) {
    var st = m.indicator_status || {};
    var monthlyKeys = ["lpr","m2_yoy","pmi","cpi","ppi","social_financing","export_yoy","new_investors"];
    var total = monthlyKeys.length;
    var fresh = 0;
    for(var i=0; i<monthlyKeys.length; i++) {
      var sti = st[monthlyKeys[i]];
      if(sti && sti.is_fresh) fresh++;
    }
    leg.innerHTML = "⭐ 已更新 " + fresh + "/" + total + " &nbsp; ☆ 待更新";
  }
  function v(id,val,color){var e=document.getElementById(id); if(!e)return; e.innerHTML=val||"--"; if(color)e.style.color=color;}
  /* 说明列更新：在数值行第3个td写入异常提示 */
  function note(id, level, text) {
    if(!text) return;
    var e = document.getElementById(id);
    if(!e || !e.parentNode) return;
    var td = e.parentNode.children[2]; // 第3列=说明
    if(!td || td.dataset.noted) return;
    var icon = level>=2 ? "🔴 " : (level>=1 ? "🟡 " : "");
    if(icon) {
      td.innerHTML = icon + text;
      td.style.color = level>=2 ? "#f44336" : "#ff9800";
    }
    td.dataset.noted = "1";
  }
  /* ===== ⭐ 月度指标标记渲染 ===== */
  function star(id, key){
    var e=document.getElementById(id); if(!e)return;
    var st = m.indicator_status && m.indicator_status[key];
    if(st && st.is_fresh){ e.innerHTML = "⭐ 月度"; e.style.color = "#FFD700"; }
    else { e.innerHTML = "☆ 月度"; e.style.color = "#999"; }
  }
  star("upd-lpr", "lpr");
  star("upd-m2", "m2_yoy");
  star("upd-pmi", "pmi");
  star("upd-cpi", "cpi");
  star("upd-szr", "social_financing");
  star("upd-export", "export_yoy");
  star("upd-investors", "new_investors");

  /* ===== 数值渲染（异常说明写入第3列） ===== */
  // 异常等级: 0=正常 1=关注 2=异常
  var mon = m.monetary || {};
  // 10Y中国国债: 2.0-3.5%正常
  if(mon.cn_bond_10y) { var cb=mon.cn_bond_10y.value; var cbLv=cb<1.8?2:(cb<2.0?1:0); v("m-cn-bond", cb+"%", "#4fc3f7"); note("m-cn-bond", cbLv, cb<1.8?"利率极低，流动性泛滥":(cb<2.0?"利率偏低":"")); }
  // 10Y美国国债: 3.0-4.5%正常
  if(mon.us_bond_10y) { var ub=mon.us_bond_10y.value; var ubLv=ub>=5?2:(ub>=4.5?1:0); v("m-us-bond", ub+"%", "#ff9800"); note("m-us-bond", ubLv, ub>=5?"高利率压制全球资产":(ub>=4.5?"利率偏高":"正常区间")); }
  // 中美利差
  if(mon.cn_us_spread){ var s=mon.cn_us_spread.value; var spLv=s<-2.5?2:(s<-1.5?1:0); v("m-spread", s+"%", s<0?"#f44336":"#4caf50"); note("m-spread", spLv, s<-2.5?"利差严重倒挂，资本外流压力大":(s<-1?"利差倒挂":"正常")); }
  // LPR
  if(mon.lpr) { v("m-lpr", mon.lpr.lpr_1y+"% / "+mon.lpr.lpr_5y+"%", "#81c784"); }
  // Shibor
  if(mon.shibor) { var so=mon.shibor.on; var sLv=so>3?2:(so>2?1:0); v("m-shibor", so+"% / "+mon.shibor.w1+"%", "#b0bec5"); note("m-shibor", sLv, so>3?"资金面紧张":(so>2?"偏紧":"")); }
  // M1-M2剪刀差
  if(mon.m2_yoy && mon.m2_yoy.value!==null) { var m2v=mon.m2_yoy.value; var m2Lv=m2v>10?2:(m2v>8?1:(m2v<0?2:0)); v("m-m1m2", m2v+"%", m2v>8?"#f44336":"#4caf50"); note("m-m1m2", m2Lv, m2v>8?"货币供应偏快":(m2v<0?"货币收缩":"正常")); }
  // 央行公开市场操作
  if(mon.open_market_operation){ var omo=mon.open_market_operation; v("m-omo", (omo.net_inflow>=0?"+":"")+omo.net_inflow+"亿", omo.net_inflow>=0?"#4caf50":"#f44336"); }
  var eco = m.economy || {};
  // PMI: >=50扩张, <49收缩
  if(eco.pmi){ var p=eco.pmi.value; var pCol=p>=50?"#4caf50":"#f44336"; var pLv=p<49?2:(p<50?1:0); v("e-pmi", p+(eco.pmi.forecast?" (预:"+eco.pmi.forecast+")":""), pCol); note("e-pmi", pLv, p<49?"PMI收缩，经济下行压力":(p<50?"PMI偏弱，景气度不足":"PMI扩张，经济向好")); }
  // CPI: 1-3%正常
  if(eco.cpi){ var cv=eco.cpi.value; var cStr=cv!==null&&cv!==undefined?cv+"%":(eco.cpi.previous?eco.cpi.previous+"%(前值)":"--"); v("e-cpi", cStr, undefined); if(cv!==null&&cv!==undefined){ var cLv=cv<0?2:(cv>3?2:(cv<1?1:0)); note("e-cpi", cLv, cv<0?"通缩风险":(cv>3?"通胀压力":(cv<1?"偏低":""))); } }
  // PPI: -2%~2%正常
  if(eco.ppi){ var pp=eco.ppi.value; var ppStr=pp!==null&&pp!==undefined?pp+"%":(eco.ppi.previous?eco.ppi.previous+"%(前值)":"--"); v("e-ppi", ppStr, undefined); if(pp!==null&&pp!==undefined){ var ppLv=pp<-3?2:(pp<-2?1:0); note("e-ppi", ppLv, pp<-3?"通缩压力严重":"正常"); } }
  // 社融规模
  if(eco.social_financing) { var sz=eco.social_financing; var szLv=sz.change_pct<-15?2:(sz.change_pct<-5?1:0); v("e-szr", sz.value+"亿 "+(sz.change_pct>0?"↑":"↓")+Math.abs(sz.change_pct)+"%", sz.change_pct<0?"#f44336":"#4caf50"); note("e-szr", szLv, sz.change_pct<-10?"社融大幅回落":(sz.change_pct<0?"社融回落":"")); }
  // 出口增速
  if(eco.export_yoy){ var ex=eco.export_yoy.value; var exStr=ex+"%"+(eco.export_yoy.previous?" (前:"+eco.export_yoy.previous+"%)":""); var exCol=ex>0?"#4caf50":"#f44336"; var exLv=ex<-5?2:(ex<0?1:0); v("e-export", exStr, exCol); note("e-export", exLv, ex<-5?"出口大幅下滑":"正常"); }
  // IPO
  if(eco.ipo){ var ipo=eco.ipo; var ipoLv=ipo.count>20?2:(ipo.count>10?1:0); v("e-ipo", ipo.count+"只 / "+ipo.amount+"亿", "#90caf9"); note("e-ipo", ipoLv, ipo.count>20?"IPO供给压力大":"正常"); }
  // 新增投资者
  var mt = m.market_sentiment || {};
  if(mt.new_investors){ var ni=mt.new_investors; var invStr=ni.value+"万"+(ni.change?" ("+(ni.change>=0?"+":"")+ni.change+"万)":""); var invCol=ni.change>0?"#ef5350":"#4caf50"; var niLv=ni.value>150?2:(ni.value>100?1:(ni.value<30?2:0)); v("mt-investors", invStr, invCol); note("mt-investors", niLv, ni.value>150?"散户过热，警惕":(ni.value<30?"人气极端低迷":"正常")); }
  // 全球宏观
  var g = m.global_macro || {};
  // VIX: <20低恐慌, 20-30正常, >30高恐慌
  if(g.vix){ var vx=g.vix.value; var vxCol=vx<20?"#4caf50":(vx<30?"#ff9800":"#f44336"); var vxLv=vx>30?2:(vx>25?1:0); v("g-vix", vx, vxCol); note("g-vix", vxLv, vx>30?"极度恐慌":(vx>25?"恐慌上升":"低波动")); }
  // DXY: 90-105正常
  if(g.dxy) { var dx=g.dxy.value; var dxLv=dx>105?2:(dx>100?1:0); v("g-dxy", dx, "#90caf9"); note("g-dxy", dxLv, dx>105?"强美元，新兴市场承压":(dx>100?"美元偏强":"")); }
  // 离岸人民币
  if(g.usdcnh){ var price=g.usdcnh.price; var usdStr=price?price.toFixed(4)+(g.usdcnh.prev_close?" (昨:"+g.usdcnh.prev_close+")":""):"暂无数据"; var usdCol=price>7.2?"#f44336":"#4caf50"; var usdLv=price>7.3?2:(price>7.2?1:0); v("g-usdcnh", usdStr, usdCol); note("g-usdcnh", usdLv, price>7.3?"贬值压力大，北向流出风险":(price>7.2?"轻微贬值":"正常")); }
  else { v("g-usdcnh", "暂无数据", "#666"); }
})();
</script>
"""

RENDER_JS_MARKER = 'if(typeof window.MACRO_DATA === "undefined") return;'


def inject_render_script(html):
    # 幂等：如果已存在渲染脚本，则替换；否则插入
    if RENDER_JS_MARKER in html:
        # 已存在 → 找到旧脚本块并替换
        marker_pos = html.find(RENDER_JS_MARKER)
        if marker_pos >= 0:
            # 找前面的 <script>
            script_open = html.rfind('<script>', 0, marker_pos)
            # 找后面的 </script>
            script_close = html.find('</script>', marker_pos)
            if script_open >= 0 and script_close >= 0:
                script_close_end = script_close + len('</script>')
                html = html[:script_open] + RENDER_JS + html[script_close_end:]
                print('✅ 渲染脚本已更新（替换已有+含⭐标记）')
                return html
    # 不存在 → 插入到 </body> 前
    html = html.replace('</body>', RENDER_JS + '\n</body>')
    print('✅ 渲染脚本已添加（含⭐标记+新指标）')
    return html


def main():
    print("=" * 50)
    print("宏观观测数据注入")
    print("=" * 50)

    # 处理 dist/index.html
    html = load_html(DIST_HTML)
    html = inject_macro_data_var(html)
    html = inject_macro_table(html)
    html = inject_macro_alert(html)
    html = inject_render_script(html)
    save_html(DIST_HTML, html)
    print(f"\n✅ dist/index.html 已更新，大小: {len(html)} 字符")

    # 同步到母版（确保宏观表格永久存在不被覆盖）
    master = load_html(MASTER_HTML)
    # 母版中如果已有宏观表格则跳过插入，否则也注入
    if '<!-- 宏观观测 -->' not in master:
        master = inject_macro_table(master)
        save_html(MASTER_HTML, master)
        print(f"✅ index_master.html 已同步宏观表格，大小: {len(master)} 字符")
    else:
        print("ℹ️ index_master.html 已包含宏观表格，跳过")


if __name__ == '__main__':
    main()
