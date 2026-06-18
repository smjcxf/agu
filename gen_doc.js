const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: 'AAAAAA' };
const borders = { top: border, bottom: border, left: border, right: border };
const headerBorder = { style: BorderStyle.SINGLE, size: 2, color: '2E75B6' };
const headerBorders = { bottom: headerBorder, top: border, left: border, right: border };
const hdrFill = { fill: '2E75B6', type: ShadingType.CLEAR };
const subFill = { fill: 'F2F6FA', type: ShadingType.CLEAR };
const margin = { top: 80, bottom: 80, left: 100, right: 100 };

function hdrCell(text, w) {
  return new TableCell({
    borders: headerBorders, width: { size: w, type: WidthType.DXA },
    shading: hdrFill, margins: margin,
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text, bold: true, color: 'FFFFFF', font: 'Arial', size: 20 })] })]
  });
}
function c(text, w, opts) {
  return new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    shading: opts && opts.s, margins: margin,
    children: [new Paragraph({ spacing: { before: 20, after: 20 }, children: [
      new TextRun({ text, font: 'Arial', size: 19 })
    ] })]
  });
}
function row(cells, widths, alt) {
  return new TableRow({ children: cells.map((t,i) => c(t, widths[i], alt && i===0 ? {s:subFill} : {})) });
}
function sec(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 360, after: 120 },
    children: [new TextRun({ text, font: 'Arial', bold: true, size: 26, color: '2E75B6' })] });
}

// Table 1
const t1 = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2000, 3600, 3760],
  rows: [
    new TableRow({ children: [hdrCell('数据类别',2000), hdrCell('数据源',3600), hdrCell('前端位置',3760)] }),
    row(['A股行情扫描', '东方财富(akshare) / efinance', '总览(推荐列表)、金股观测'], [2000,3600,3760], true),
    row(['港股行情', '腾讯 gtimg / 东方财富', '金股观测(港股标签)'], [2000,3600,3760], true),
    row(['板块资金流向', 'akshare 行业板块API', '💰板块资金流向汇总'], [2000,3600,3760], true),
    row(['概念涨跌排名', 'akshare 概念板块API', '📊概念涨跌幅排名'], [2000,3600,3760], true),
    row(['龙虎榜', 'akshare 龙虎榜API', '🐉龙虎榜机游共振'], [2000,3600,3760], true),
    row(['资金抱团预判', 'NeoData + 东方财富', '🔮资金抱团预判'], [2000,3600,3760], true),
    row(['ETF资金流向', '腾讯 gtimg(前端) + akshare', '🔥国家队ETF资金流向速报'], [2000,3600,3760], true),
    row(['宏观数据', 'akshare(VIX/DXY/PMI等) / 新浪(汇率)', '🌍宏观观测'], [2000,3600,3760], true),
    row(['图表数据(K线/涨跌等)', '新浪 / baostock / akshare', '📈成交金额图/涨跌家数/两融/ETF'], [2000,3600,3760], true),
    row(['投行信号', 'mahoro.cn API(内部)', '增强评分(投行覆盖加分)'], [2000,3600,3760], true),
    row(['投行研报', '知识星球(zsxq) API', '金股池(投行研报标记)'], [2000,3600,3760], true),
    row(['日历事件', 'akshare / apihubs.cn', '📅重要日历'], [2000,3600,3760], true),
    row(['前端实时行情', '腾讯 qt.gtimg.cn', '🔍个股查询(按需)'], [2000,3600,3760], true),
  ]
});

// Table 2
const t2 = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2800, 6560],
  rows: [
    new TableRow({ children: [hdrCell('前端页面/模块',2800), hdrCell('依赖的数据源',6560)] }),
    row(['🧠 AI市场速览', '东方财富(指数/板块) + 腾讯(ETF)'], [2800,6560], true),
    row(['🌟 强烈关注推荐', 'scanner.py扫描结果(东方财富)'], [2800,6560], true),
    row(['🏅 金股观测', 'scanner.py + 知识星球(研报)'], [2800,6560], true),
    row(['🔮 资金抱团预判', 'NeoData + 东方财富'], [2800,6560], true),
    row(['🐉 龙虎榜机游共振', 'akshare龙虎榜API'], [2800,6560], true),
    row(['💰 板块资金流向', 'akshare行业板块API'], [2800,6560], true),
    row(['📊 概念涨跌幅', 'akshare概念板块API'], [2800,6560], true),
    row(['🌍 宏观观测', 'akshare(宏观) + 新浪(汇率)'], [2800,6560], true),
    row(['📈 图表区(4图)', '新浪(指数K线) + baostock(涨跌) + akshare(两融/ETF)'], [2800,6560], true),
    row(['🔍 个股查询', '腾讯gtimg(前端实时)'], [2800,6560], true),
    row(['🔥 ETF资金流向', 'akshare ETF API'], [2800,6560], true),
    row(['📊 斐波那契窗口', 'akshare + baostock(指数K线)'], [2800,6560], true),
    row(['📊 重要日历', 'akshare(财报) + apihubs.cn(假期)'], [2800,6560], true),
    row(['🏅 历史追踪', 'gold_pool.json(三线共振快照)'], [2800,6560], true),
  ]
});

// Table 3
const t3 = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [1200, 5360, 2800],
  rows: [
    new TableRow({ children: [hdrCell('时间',1200), hdrCell('任务',5360), hdrCell('依赖数据源',2800)] }),
    row(['09:15', '盘前部署: 观澜研报→全量扫描→推荐→部署', '东方财富/知识星球'], [1200,5360,2800], true),
    row(['09:45/10:00/10:30', '盘中扫描→部署(3轮)', '东方财富'], [1200,5360,2800], true),
    row(['13:30/14:30/16:30', '盘中扫描+概念/板块/预判→部署(3轮)', '东方财富/NeoData'], [1200,5360,2800], true),
    row(['19:30', '盘后全量: 研报→龙虎榜→主力→预判→全扫→推荐→部署', '东方财富/知识星球/NeoData/mahoro'], [1200,5360,2800], true),
    row(['21:00', '自动备份', '本地文件'], [1200,5360,2800], true),
  ]
});

const now = new Date().toISOString().slice(0,10);

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, font: 'Arial', color: '1A3A5C' },
        paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: 'Arial', color: '2E75B6' },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    headers: {
      default: new Header({ children: [
        new Paragraph({ alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '2E75B6', space: 4 } },
          children: [new TextRun({ text: '九宝量化 v6.0 \u00b7 数据源映射文档', font: 'Arial', size: 18, color: '888888', italics: true })] })
      ] })
    },
    footers: {
      default: new Footer({ children: [
        new Paragraph({ alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: '生成于 '+now+' \u00b7 第 ', size: 16, color: '999999' }),
          new TextRun({ children: [PageNumber.CURRENT], size: 16, color: '999999' }),
          new TextRun({ text: ' 页', size: 16, color: '999999' })
        ] })
      ] })
    },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
        children: [new TextRun({ text: '九宝量化 v6.0', font: 'Arial', size: 48, bold: true, color: '1A3A5C' })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
        children: [new TextRun({ text: '数据源 \u2192 前端页面 完整映射', font: 'Arial', size: 32, color: '2E75B6' })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 },
        children: [new TextRun({ text: 'https://ah-quant999.github.io/quant-scanner-v6/', font: 'Arial', size: 20, color: '666666' })] }),

      sec('一、数据类别 \u2192 数据源 \u2192 前端位置'),
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: '下表按数据类别列出每个模块的数据来源和前端显示位置。', font: 'Arial', size: 20, color: '444444' })] }),
      t1,

      sec('二、前端页面 \u2192 数据源映射'),
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: '以下从用户视角出发，列出每个页面/模块依赖的数据源。', font: 'Arial', size: 20, color: '444444' })] }),
      t2,

      sec('三、定时任务执行表'),
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: '每天自动执行的定时任务及其依赖的第三方数据源。', font: 'Arial', size: 20, color: '444444' })] }),
      t3,

      new Paragraph({ spacing: { before: 360 }, children: [new TextRun({ text: '\u300c注\u300d', font: 'Arial', size: 20, bold: true, color: '888888' })] }),
      new Paragraph({ children: [new TextRun({ text: '后端共 7 个脚本每日定时采集 \u2192 注入 HTML \u2192 部署到 GitHub Pages。前端仅 1 个实时查询接口（腾讯 gtimg）按需调用。核心数据源为东方财富（~70%），新浪、腾讯为辅助，mahoro.cn 和知识星球提供研报/投行信号特色数据。', font: 'Arial', size: 19, color: '666666' })] }),
    ]
  }]
});

const outPath = 'E:/workspace/stock-scanner/outputs/数据源前端映射_九宝量化v6.docx';
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log('OK: ' + outPath + ' (' + buf.length + ' bytes)');
});
