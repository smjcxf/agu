function renderHiddenData(){
  var el = document.getElementById('hiddenDataContent');
  if(!el) return;
  console.log('[renderHiddenData] start', window.HIDDEN_DATA);

  var hd = window.HIDDEN_DATA || {};
  var html = '<div style="font-size:12px;color:#666;">';

  // ===== 区块1: 扫描执行记录（粉系）=====
  var signalLog = hd.signal_log || [];
  if(signalLog.length > 0){
    html += '<div style="border-left:3px solid #f48fb1;padding:12px 16px;background:#fce4ec;border-radius:0 8px 8px 0;margin-bottom:14px;">';
    html += '<div style="font-weight:700;font-size:14px;color:#555;margin-bottom:8px;">🔍 扫描执行记录（最近20次）</div>';
    html += '<div style="font-size:11px;line-height:1.8;">';
    signalLog.slice(0,20).forEach(function(log){
      html += '<div style="display:flex;gap:10px;padding:3px 0;border-bottom:1px solid #f8bbd0;font-family:monospace;">';
      html += '<span style="color:#888;min-width:60px;">'+(log.scan_time||'').substring(5,16)+'</span>';
      html += '<span style="min-width:50px;">'+(log.mode||'')+'</span>';
      html += '<span>扫描'+(log.total_scanned||0)+'只 / 三线'+(log.triple_count||0)+' / 双线'+(log.double_count||0);
      if(log.new_triple_count > 0) html += ' <b style="color:#c62828;">新三线'+log.new_triple_count+'</b>';
      html += '</span></div>';
    });
    html += '</div></div>';
  } else {
    html += '<div style="border-left:3px solid #f48fb1;padding:12px 16px;background:#fce4ec;border-radius:0 8px 8px 0;margin-bottom:14px;">';
    html += '<div style="font-weight:700;font-size:14px;color:#555;margin-bottom:8px;">🔍 扫描执行记录</div>';
    html += '<div style="font-size:11px;color:#999;">暂无扫描日志</div>';
    html += '</div>';
  }

  // ===== 区块2: 信号回测 + 当前扫描状态（蓝/绿并排）=====
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">';

  // 信号回测（蓝）
  var bt = hd.backtest || {};
  html += '<div style="border-left:3px solid #64b5f6;padding:12px 16px;background:#e3f2fd;border-radius:0 8px 8px 0;">';
  html += '<div style="font-weight:700;font-size:14px;color:#555;margin-bottom:8px;">📊 信号回测摘要</div>';
  html += '<div style="font-size:11px;line-height:1.9;">';
  html += '<div>样本: <b>'+((bt.total_count||0))+'</b>只 | 胜<span style="color:'+((bt.win_rate||0)>=70?'#c62828':(bt.win_rate||0)>=50?'#e65100':'#666')+';font-weight:700;">'+(bt.win_rate||0)+'%</span> | 平均收益: '+(bt.avg_return||0)+'%</div>';
  html += '<div style="color:#666;margin-top:4px;">更新: '+(bt.calc_time||'未知')+'</div>';
  html += '</div></div>';

  // 当前扫描状态（绿）
  var ss = hd.scan_stats || {};
  html += '<div style="border-left:3px solid #81c784;padding:12px 16px;background:#e8f5e9;border-radius:0 8px 8px 0;">';
  html += '<div style="font-weight:700;font-size:14px;color:#555;margin-bottom:8px;">🔧 当前扫描状态</div>';
  html += '<div style="font-size:11px;line-height:1.9;">';
  html += '<div>最新扫描: <b>'+(ss.scan_time||'未知')+'</b></div>';
  html += '<div>模式: <b>'+(ss.mode||'?')+'</b> | 扫描: <b>'+(ss.total_scanned||0)+'</b>只</div>';
  html += '<div>耗时: '+(ss.scan_duration||'?')+'</div>';
  html += '<div>金股池: <b>'+(hd.gold_pool_meta&&hd.gold_pool_meta.count||'?')+'</b>只</div>';
  html += '<div>增强日志: '+(hd.enhance_log||'无')+'</div>';
  html += '</div></div>';

  html += '</div>';

  // ===== 区块3: 部署审计记录（橙系）=====
  var audit = hd.audit || {};
  var ad = audit.details || {};
  html += '<div style="border-left:3px solid #ffb74d;padding:12px 16px;background:#fff3e0;border-radius:0 8px 8px 0;margin-bottom:14px;">';
  html += '<div style="font-weight:700;font-size:14px;color:#555;margin-bottom:8px;">📋 部署审计记录</div>';
  html += '<div style="font-size:11px;line-height:1.9;">';
  if(audit.timestamp) html += '<div>审计时间: <b>'+audit.timestamp+'</b></div>';
  html += '<div>ERROR: <b style="color:'+(audit.errors>0?'#c62828':'#2e7d32')+';">'+(audit.errors||0)+'</b> | WARNING: <b style="color:'+(audit.warnings>0?'#e65100':'#2e7d32')+';">'+(audit.warnings||0)+'</b> | OK: <b style="color:#2e7d32;">'+(audit.ok||0)+'</b></div>';
  var errs = (ad.errors || []);
  var warns = (ad.warnings || []);
  if(errs.length > 0){
    html += '<div style="margin-top:4px;"><span style="color:#c62828;font-weight:700;">ERROR明细:</span><div style="margin-left:8px;color:#c62828;max-height:80px;overflow-y:auto;">';
    errs.slice(0,10).forEach(function(e){ html += '• '+e+'<br>'; });
    html += '</div></div>';
  }
  if(warns.length > 0){
    html += '<div style="margin-top:4px;"><span style="color:#e65100;font-weight:700;">WARNING明细:</span><div style="margin-left:8px;color:#e65100;max-height:80px;overflow-y:auto;">';
    warns.slice(0,10).forEach(function(w){ html += '• '+w+'<br>'; });
    html += '</div></div>';
  }
  if(errs.length === 0 && warns.length === 0) html += '<div style="color:#2e7d32;">✅ 无ERROR/WARNING</div>';
  html += '</div></div>';

  // ===== 区块4: 历史追踪数据量（紫/青并排）=====
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">';

  var tm = hd.triple_history_meta || {};
  html += '<div style="border-left:3px solid #ba68c8;padding:12px 16px;background:#f3e5f5;border-radius:0 8px 8px 0;">';
  html += '<div style="font-weight:700;font-size:14px;color:#555;margin-bottom:8px;">🧬 三线共振历史</div>';
  html += '<div style="font-size:11px;line-height:1.9;">';
  html += '<div>数据天数: <b>'+((tm.days||0))+'</b>天</div>';
  html += '<div>日期范围: '+(tm.first||'?')+' ~ '+(tm.last||'?')+'</div>';
  html += '</div></div>';

  var mm = hd.multi_history_meta || {};
  html += '<div style="border-left:3px solid #4dd0e1;padding:12px 16px;background:#e0f7fa;border-radius:0 8px 8px 0;">';
  html += '<div style="font-weight:700;font-size:14px;color:#555;margin-bottom:8px;">🧬 多维共振历史</div>';
  html += '<div style="font-size:11px;line-height:1.9;">';
  html += '<div>数据天数: <b>'+((mm.days||0))+'</b>天</div>';
  html += '<div>日期范围: '+(mm.first||'?')+' ~ '+(mm.last||'?')+'</div>';
  html += '</div></div>';

  html += '</div>';

  // ===== 区块5: 定时任务配置表（淡青）=====
  var schedule = hd.update_schedule || {};
  var schedules = schedule.schedules || [];
  html += '<div style="border-left:3px solid #90a4ae;padding:12px 16px;background:#eceff1;border-radius:0 8px 8px 0;margin-bottom:14px;">';
  html += '<div style="font-weight:700;font-size:14px;color:#555;margin-bottom:8px;">⏰ 定时任务配置表（'+schedules.length+'个自动化）</div>';
  html += '<div style="font-size:11px;line-height:1.8;font-family:monospace;">';
  if(schedule.updated) html += '<div style="color:#888;margin-bottom:4px;">更新时间: '+schedule.updated+'</div>';
  schedules.forEach(function(s){
    html += '<div style="display:flex;gap:6px;padding:2px 0;border-bottom:1px solid #cfd8dc;">';
    html += '<span style="color:#455a64;min-width:45px;">'+s.time+'</span>';
    html += '<span style="font-weight:600;min-width:110px;">'+s.task+'</span>';
    html += '<span style="color:#666;">'+s.content+'</span>';
    html += '</div>';
  });
  html += '</div></div>';

  html += '</div>';
  el.innerHTML = html;
  console.log('[renderHiddenData] done');
}
