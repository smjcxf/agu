function renderWorldcup(){
  var el = document.getElementById('worldcupContent');
  if(!el) return;
  var d = window.WORLD_CUP || null;
  if(!d || !d.groups) {
    el.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">⚽ 等待数据...</div>';
    return;
  }

  // 辅助函数
  function pts(t){ return t.w*3 + t.d; }
  function gd(t){ return t.gf - t.ga; }
  function winRate(t){ var p=t.w+t.d+t.l||1; return Math.round((t.w*100+t.d*33)/p); }

  function wcCard(title, content){
    return '<div style="background:#f8f9fa;border-radius:8px;padding:14px;margin-bottom:10px;border:1px solid #e0e0e0;">'+
      '<div style="font-weight:700;font-size:14px;color:#1a2a4a;margin-bottom:8px;border-left:3px solid #ff6b35;padding-left:8px;">'+title+'</div>'+
      '<div style="font-size:12px;line-height:1.9;">'+content+'</div></div>';
  }

  var h = '';

  // 更新时间和比赛日
  var wft = d.update_time ? fmtDataTime(d.update_time) : null;
  h += '<div style="font-size:12px;color:#999;margin-bottom:14px;">数据更新：' + (wft ? wft.text : (d.update_time||'')) + ' · ' + (d.matchday||'') + ' <span style="color:#bbb;">· 每日 07:30 更新</span></div>';

  // 休息日/赛程提示
  if (d.status_note) {
    h += '<div style="background:#fff3e0;border:1px solid #ffe0b2;border-radius:6px;padding:8px 12px;margin-bottom:12px;font-size:12px;color:#e65100;">📢 ' + d.status_note + '</div>';
  }

  // 1. 夺冠概率 TOP8
  var odds = d.odds || [];
  h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">';
  h += wcCard('🏆 夺冠概率 TOP8（Monte Carlo 模拟）', (function(){
    var r = '';
    odds.slice(0,8).forEach(function(o,i){
      var w = i===0?100:(o.prob/odds[0].prob*80).toFixed(0);
      var c = i<3?'#ffd700':i<6?'#e67e22':'#3498db';
      r += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'+
        '<span style="font-size:12px;width:16px;">#'+(i+1)+'</span>'+
        '<span style="flex:1;min-width:60px;font-weight:600;">'+o.n+'</span>'+
        '<span style="font-weight:800;color:'+c+';width:36px;text-align:right;">'+o.prob+'%</span>'+
        '<div style="flex:1;height:6px;background:#e0e0e0;border-radius:3px;"><div style="height:100%;width:'+w+'%;background:'+c+';border-radius:3px;"></div></div></div>';
    }); return r;
  })());

  // 2. 小组赛胜率榜
  var allTeams = d.all_teams || [];
  h += wcCard('📊 小组赛胜率榜（全部48队）', (function(){
    var sorted = allTeams.slice().sort(function(a,b){return winRate(b)-winRate(a);});
    var r = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;font-size:11px;">';
    sorted.slice(0,24).forEach(function(t,i){
      var wr = winRate(t);
      r += '<div style="display:flex;justify-content:space-between;padding:1px 0;">'+
        '<span>'+(i+1)+'. '+t.n+'</span><span style="font-weight:600;color:'+(wr>=75?'#c62828':wr>=50?'#e65100':'#666')+';">'+wr+'%</span></div>';
    }); return r+'</div>';
  })());
  h += '</div>';

  // 2.5 晋级概率预测 (Monte Carlo)
  var qualProbs = d.qual_probs || {};
  h += wcCard('🎲 晋级概率预测（Monte Carlo 5000次模拟）', (function(){
    var r = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;">';
    Object.keys(qualProbs).sort().forEach(function(gid){
      var probs = qualProbs[gid];
      var sorted = Object.entries(probs).sort(function(a,b){return b[1]-a[1];});
      r += '<div style="background:#fff;border-radius:4px;padding:5px 6px;">';
      r += '<div style="font-weight:700;font-size:12px;color:#1a2a4a;margin-bottom:3px;">组 '+gid+'</div>';
      sorted.forEach(function(pair){
        var name = pair[0], prob = pair[1];
        var barColor = prob>=90?'#c62828':prob>=50?'#e67e22':prob>=20?'#3498db':'#b0bec5';
        r += '<div style="display:flex;align-items:center;gap:3px;margin-bottom:2px;font-size:11px;">'+
          '<span style="width:46px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+name+'</span>'+
          '<div style="width:50px;height:5px;background:#e0e0e0;border-radius:2px;flex-shrink:0;">'+
          '<div style="height:100%;width:'+Math.max(5,prob)+'%;background:'+barColor+';border-radius:2px;"></div></div>'+
          '<span style="font-weight:700;color:'+barColor+';">'+prob+'%</span></div>';
      });
      r += '</div>';
    });
    return r+'</div>';
  })());

  // 2.6 加权净胜球效率
  var adjEff = d.adj_eff || {};
  h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">';
  h += wcCard('⚖️ 加权进攻效率 TOP10（进球×对手强度）', (function(){
    var sorted_at = allTeams.slice().sort(function(a,b){
      return (b.adj_gf||b.gf) - (a.adj_gf||a.gf);
    }).slice(0,10);
    var r = '';
    sorted_at.forEach(function(t,i){
      var raw = t.gf||0, adj = (t.adj_gf||0).toFixed(1);
      r += '<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:12px;">'+
        '<span>'+(i+1)+'. '+t.n+'</span>'+
        '<span style="color:#888;">原始'+raw+'球 → <span style="font-weight:600;color:#c62828;">加权'+adj+'</span></span></div>';
    }); return r;
  })());
  h += wcCard('🛡️ 加权防守效率 TOP10（失球÷对手强度）', (function(){
    var sorted_dt = allTeams.slice().sort(function(a,b){
      return (a.adj_ga||a.ga) - (b.adj_ga||b.ga);
    }).slice(0,10);
    var r = '';
    sorted_dt.forEach(function(t,i){
      var raw = t.ga||0, adj = (t.adj_ga||0).toFixed(1);
      r += '<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:12px;">'+
        '<span>'+(i+1)+'. '+t.n+'</span>'+
        '<span style="color:#888;">原始'+raw+'球 → <span style="font-weight:600;color:#2e7d32;">加权'+adj+'</span></span></div>';
    }); return r;
  })());
  h += '</div>';

  // 3. 地区对比
  h += wcCard('🌍 各洲足联表现对比', (function(){
    var regions = {};
    var regionNames = {'UEFA':'欧洲','CONMEBOL':'南美','AFC':'亚洲','CAF':'非洲','CONCACAF':'北美','OFC':'大洋洲'};
    allTeams.forEach(function(t){
      var reg = t.region || '?';
      if(!regions[reg]) regions[reg] = [];
      regions[reg].push(t);
    });
    var regionData = Object.keys(regionNames).map(function(k){
      var list = regions[k] || [];
      var total = list.length || 1;
      var totalPts = list.reduce(function(s,t){return s+pts(t);},0);
      return {k:k, name:regionNames[k], n:list.length, avg:(totalPts/total).toFixed(1)};
    }).sort(function(a,b){return b.avg-a.avg;});
    var r = '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:4px;font-size:10px;">';
    regionData.forEach(function(d){
      r += '<div style="background:#fff;border-radius:4px;padding:4px 6px;text-align:center;">'+
        '<div style="font-weight:700;">'+d.name+'</div>'+
        '<div style="font-size:11px;">'+d.n+'队</div>'+
        '<div style="color:#e65100;">均'+d.avg+'分</div></div>';
    }); return r+'</div>';
  })());

  // 5. 小组积分榜
  var groups = d.groups || [];
  h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;">';
  groups.forEach(function(g){
    var sorted = g.teams.slice().sort(function(a,b){ return pts(b)-pts(a) || gd(b)-gd(a) || b.gf-a.gf; });
    h += '<div style="background:#f8f9fa;border-radius:6px;padding:8px 10px;">';
    h += '<div style="font-weight:700;font-size:13px;color:#1a2a4a;margin-bottom:6px;text-align:center;">组 '+g.id+'</div>';
    sorted.forEach(function(t,i){
      var bg = i<2?'#e8f5e9':'';
      h += '<div style="padding:3px 0;font-size:11px;'+(bg?'background:'+bg+';border-radius:3px;padding-left:4px;':'')+'display:flex;justify-content:space-between;">';
      h += '<span>'+(i<2?'⬆':'')+t.name+'</span>';
      h += '<span style="color:#888;">'+t.w+'/'+t.d+'/'+t.l+' '+pts(t)+'分 '+(gd(t)>=0?'+':'')+gd(t)+'</span>';
      h += '</div>';
    });
    h += '</div>';
  });
  h += '</div>';

  // 6. 赛程表（实时数据驱动，已结束场次显示比分）
  var results = d.results || [];
  // 按日期分组
  var resultsByDate = {};
  results.forEach(function(m){
    var dd = m.d;
    if (!resultsByDate[dd]) resultsByDate[dd] = [];
    resultsByDate[dd].push(m);
  });
  
  h += wcCard('📅 赛程表（已结束场次标红比分）', (function(){
    var r = '';
    // 淘汰赛 — 决赛排最前，按日期倒序
    r += '<div style="font-weight:700;font-size:15px;color:#333;margin-bottom:6px;">🏆 淘汰赛阶段</div>';
    var knockout = d.knockout || [];
    var knockoutByDate = {};
    knockout.forEach(function(m){
      var dd = m.date;
      if (!knockoutByDate[dd]) knockoutByDate[dd] = [];
      knockoutByDate[dd].push(m);
    });
    var koDateOrder = Object.keys(knockoutByDate).sort(function(a,b){
      var months = {'Jun':6,'Jul':7};
      var ma = a.split(' '), mb = b.split(' ');
      return (months[mb[0]]||0)*100 + (parseInt(mb[1])||0) - (months[ma[0]]||0)*100 - (parseInt(ma[1])||0);
    });
    koDateOrder.forEach(function(dd){
      var matches = knockoutByDate[dd];
      r += '<div style="display:flex;gap:8px;padding:3px 0;font-size:13px;border-bottom:1px solid #f0f0f0;">';
      r += '<span style="color:#888;min-width:70px;font-weight:600;">'+dd+'</span>';
      r += '<span>';
      matches.forEach(function(m, mi){
        if (mi > 0) r += '、';
        r += '<span style="color:#666;font-size:12px;margin-right:3px;">['+m.round+']</span>' + m.home + ' vs ' + m.away;
        if (m.score) r += ' <b style="color:#c62828;font-size:14px;">'+m.score+'</b>';
        r += ' <span style="color:#999;font-size:12px;">— '+m.venue+'</span>';
      });
      r += '</span></div>';
    });
    // 小组赛 — 日期倒序
    r += '<div style="margin-top:10px;">';
    r += '<div style="font-weight:700;font-size:15px;color:#333;margin:10px 0 6px;">⚽ 小组赛阶段</div>';
    var dateOrder = Object.keys(resultsByDate).sort(function(a,b){
      var months = {'Jun':6,'Jul':7};
      var ma = a.split(' '), mb = b.split(' ');
      return (months[mb[0]]||0)*100 + (parseInt(mb[1])||0) - (months[ma[0]]||0)*100 - (parseInt(ma[1])||0);
    });
    dateOrder.forEach(function(dd){
      var matches = resultsByDate[dd];
      r += '<div style="display:flex;gap:8px;padding:3px 0;font-size:13px;border-bottom:1px solid #f0f0f0;">';
      r += '<span style="color:#888;min-width:70px;font-weight:600;">'+dd+'</span>';
      r += '<span>';
      matches.forEach(function(m, mi){
        if (mi > 0) r += '、';
        r += m.h + ' vs ' + m.a;
        if (m.s) r += ' <b style="color:#c62828;font-size:14px;">'+m.s+'</b>';
      });
      r += '</span></div>';
    });
    r += '</div>';
    return r;
  })());

  el.innerHTML = h;
}