import { astro } from 'iztro';
import { chaiBuJuByGanZhi } from '../frontend/node_modules/bigfishmarquis-qimen/src/engines/chaibuquju';
import { shiJiaGenerate } from '../frontend/node_modules/bigfishmarquis-qimen/src/engines/shijia';
import { getPalaceKeYing } from '../frontend/node_modules/bigfishmarquis-qimen/src/interpretation';

// ─── HELPER: READ STDIN JSON ──────────────────────────────────────
async function readStdin(): Promise<string> {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', err => reject(err));
  });
}

// ─── 1. ZIWEI CALCULATION ─────────────────────────────────────────
interface ZiweiInput {
  calendarType?: 'solar' | 'lunar';
  year: number;
  month: number;
  day: number;
  hour?: number | null;
  gender?: '男' | '女';
  isLeapMonth?: boolean;
  fixLeap?: boolean;
  targetDate?: string; // YYYY-MM-DD
}

function calculateZiwei(params: ZiweiInput) {
  const {
    calendarType = 'solar',
    year,
    month,
    day,
    hour,
    gender = '男',
    isLeapMonth = false,
    fixLeap = true,
    targetDate
  } = params;

  if (hour === null || hour === undefined) {
    return {
      success: true,
      degraded: true,
      message: '出生时辰未知，紫微斗数无法安命宫与排布十四正星。系统保留已知年月日信息，不脑内臆造时辰虚假排盘。',
      input: { calendarType, year, month, day, hour, gender },
      engine_version: 'iztro 2.6.1'
    };
  }

  // 时辰映射到 iztro timeIndex:
  // hour 0-23: hourIndex = Math.floor((hour + 1) % 24 / 2) -> 0=子, 1=丑, 2=寅...
  const timeIndex = Math.floor(((hour + 1) % 24) / 2);
  const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

  let astrolabe: any;
  if (calendarType === 'lunar') {
    astrolabe = astro.byLunar(dateStr, timeIndex, gender, isLeapMonth, fixLeap, 'zh-CN');
  } else {
    astrolabe = astro.bySolar(dateStr, timeIndex, gender, fixLeap, 'zh-CN');
  }

  // 提取12宫位详情
  const palaces = astrolabe.palaces.map((p: any, idx: number) => {
    // 找出三方四正 (对宫与三方三合)
    // 宫位索引在 0..11 对应 地支顺序
    const oppositeIdx = (idx + 6) % 12;
    const trine1Idx = (idx + 4) % 12;
    const trine2Idx = (idx + 8) % 12;

    const majorStars = p.majorStars.map((s: any) => ({
      name: s.name,
      type: s.type,
      scope: s.scope,
      brightness: s.brightness || '',
      mutagen: s.mutagen || ''
    }));

    const minorStars = p.minorStars.map((s: any) => ({
      name: s.name,
      type: s.type,
      scope: s.scope,
      brightness: s.brightness || '',
      mutagen: s.mutagen || ''
    }));

    const adjectiveStars = p.adjectiveStars.map((s: any) => ({
      name: s.name,
      type: s.type,
      scope: s.scope
    }));

    const isSoulPalace = p.name === '命宫' || p.earthlyBranch === astrolabe.earthlyBranchOfSoulPalace;
    const isBodyPalace = Boolean(p.isBodyPalace || p.earthlyBranch === astrolabe.earthlyBranchOfBodyPalace);
    const isOriginalPalace = Boolean(p.isOriginalPalace); // 来因宫 (iztro)

    return {
      index: idx,
      name: p.name,
      isSoulPalace,
      isOriginalPalace,
      isBodyPalace,
      earthlyBranch: p.earthlyBranch,
      heavenlyStem: p.heavenlyStem,
      majorStars,
      minorStars,
      adjectiveStars,
      changsheng12: p.changsheng12 || '',
      boshi12: p.boshi12 || '',
      decadal: p.decadal ? {
        range: p.decadal.range,
        heavenlyStem: p.decadal.heavenlyStem,
        earthlyBranch: p.decadal.earthlyBranch
      } : null,
      ages: p.ages || [],
      sanFangSiZheng: {
        opposite: astrolabe.palaces[oppositeIdx]?.name || '',
        trine1: astrolabe.palaces[trine1Idx]?.name || '',
        trine2: astrolabe.palaces[trine2Idx]?.name || ''
      }
    };
  });

  // 流年/大限提取
  let horoscopeData: any = null;
  if (targetDate) {
    try {
      const horo = astrolabe.horoscope(targetDate);
      horoscopeData = {
        targetDate,
        decadal: {
          index: horo.decadal.index,
          name: horo.decadal.name,
          heavenlyStem: horo.decadal.heavenlyStem,
          earthlyBranch: horo.decadal.earthlyBranch,
          mutagen: horo.decadal.mutagen
        },
        yearly: {
          index: horo.yearly.index,
          name: horo.yearly.name,
          heavenlyStem: horo.yearly.heavenlyStem,
          earthlyBranch: horo.yearly.earthlyBranch,
          mutagen: horo.yearly.mutagen
        },
        age: {
          nominalAge: horo.age.nominalAge,
          index: horo.age.index
        }
      };
    } catch {
      // 容错降级
      horoscopeData = null;
    }
  }

  // 大限列表
  const decadalList = astrolabe.decadalList || [];

  return {
    success: true,
    degraded: false,
    input: { calendarType, year, month, day, hour, gender, isLeapMonth },
    basic: {
      solarDate: astrolabe.solarDate,
      lunarDate: astrolabe.lunarDate,
      chineseDate: astrolabe.chineseDate,
      time: astrolabe.time,
      timeRange: astrolabe.timeRange,
      sign: astrolabe.sign,
      zodiac: astrolabe.zodiac,
      gender: astrolabe.gender,
      soul: astrolabe.soul,
      body: astrolabe.body,
      fiveElementsClass: astrolabe.fiveElementsClass,
      earthlyBranchOfSoulPalace: astrolabe.earthlyBranchOfSoulPalace,
      earthlyBranchOfBodyPalace: astrolabe.earthlyBranchOfBodyPalace,
      soulPalaceName: '命宫',
      bodyPalaceName: astrolabe.palaces.find((p: any) => p.isBodyPalace || p.earthlyBranch === astrolabe.earthlyBranchOfBodyPalace)?.name || '',
      originalPalaceName: astrolabe.palaces.find((p: any) => p.isOriginalPalace)?.name || '',
      earthlyBranchOfOriginalPalace: astrolabe.palaces.find((p: any) => p.isOriginalPalace)?.earthlyBranch || ''
    },
    palaces,
    decadalList,
    horoscope: horoscopeData,
    engine_version: 'iztro 2.6.1',
    rules: {
      zi_hour_mode: '早晚子时分立（00:00换日，23:00-00:00属次日子初）',
      leap_month_rule: '公历农历精准对照，闰月支持保持或中气分界',
      gender_direction: '阳男阴女顺行，阴男阳女逆行'
    }
  };
}

// ─── 2. QIMEN CALCULATION ─────────────────────────────────────────
interface QimenInput {
  solarTerm: string;
  fourPillars: {
    year: { gan: string; zhi: string };
    month: { gan: string; zhi: string };
    day: { gan: string; zhi: string };
    hour: { gan: string; zhi: string };
  };
  hourNumber?: number; // 0-23
  topic?: string;
  juMethod?: 'chaibu' | 'maoshan';
}

const PALACE_BAGUA_INFO: Record<number, { name: string; gua: string; direction: string; element: string }> = {
  1: { name: '坎一宫', gua: '坎', direction: '正北', element: '水' },
  2: { name: '坤二宫', gua: '坤', direction: '西南', element: '土' },
  3: { name: '震三宫', gua: '震', direction: '正东', element: '木' },
  4: { name: '巽四宫', gua: '巽', direction: '东南', element: '木' },
  5: { name: '中五宫', gua: '中', direction: '中央', element: '土' },
  6: { name: '乾六宫', gua: '乾', direction: '西北', element: '金' },
  7: { name: '兑七宫', gua: '兑', direction: '正西', element: '金' },
  8: { name: '艮八宫', gua: '艮', direction: '东北', element: '土' },
  9: { name: '离九宫', gua: '离', direction: '正南', element: '火' },
};

function calculateQimen(params: QimenInput) {
  const { solarTerm, fourPillars, hourNumber = 12, topic = '' } = params;

  const dayGan = fourPillars.day.gan;
  const dayZhi = fourPillars.day.zhi;
  const hourGan = fourPillars.hour.gan;
  const hourZhi = fourPillars.hour.zhi;

  // 1. 拆补定局
  const juResult = chaiBuJuByGanZhi(solarTerm, dayGan, dayZhi, hourNumber);

  // 2. 生成时家转盘奇门
  const chart = shiJiaGenerate(
    hourGan,
    hourZhi,
    juResult.juNumber,
    juResult.isYangDun ? 'yang' : 'yin',
    fourPillars,
    solarTerm
  );

  // 3. 增强九宫数据
  const palaces = chart.palaces.map(p => {
    const meta = PALACE_BAGUA_INFO[p.palaceNumber] || { name: `${p.palaceNumber}宫`, gua: '', direction: '', element: '' };

    // 获取十干克应 (天盘干 + 地盘干)
    // 在 bigfishmarquis-qimen 内部约定中:
    // p.earthStem 存放天盘干 (tianPanGan)
    // p.skyStem 存放地盘干 (diPanGan)
    // getPalaceKeYing(p.skyStem, p.earthStem, p.hiddenStems, p.jiGanStem) 会按 (天盘干+地盘干) 匹配断语
    const tianStem = p.earthStem;
    const diStem = p.skyStem;
    const keYingList = getPalaceKeYing(p.skyStem, p.earthStem, p.hiddenStems, p.jiGanStem);

    const isZhiFu = p.palaceNumber === chart.zhiFuPalace;
    const isZhiShi = p.palaceNumber === chart.zhiShiPalace;
    const isKongWang = (chart.kongWang || []).some(kw => {
      // 检查空亡地支是否落在此宫对应的地支
      const branchesForPalace: Record<number, string[]> = {
        1: ['子'], 2: ['未','申'], 3: ['卯'], 4: ['辰','巳'],
        5: [], 6: ['戌','亥'], 7: ['酉'], 8: ['丑','寅'], 9: ['午']
      };
      return (branchesForPalace[p.palaceNumber] || []).includes(kw);
    });

    return {
      palaceNumber: p.palaceNumber,
      palaceName: p.palaceName,
      fullName: meta.name,
      gua: meta.gua,
      direction: meta.direction,
      element: meta.element,
      tianPanGan: tianStem, // 规范命名: 天盘天干
      diPanGan: diStem,     // 规范命名: 地盘天干
      skyStem: diStem,     // 历史兼容字段: 地盘天干
      earthStem: tianStem, // 历史兼容字段: 天盘天干
      hiddenStems: p.hiddenStems, // 暗干支
      jiGanStem: p.jiGanStem,
      star: p.star,
      starElement: p.starElement,
      door: p.door,
      doorElement: p.doorElement,
      god: p.god,
      godShort: p.godShort,
      diGod: p.diGod,
      keYing: keYingList,
      isZhiFu,
      isZhiShi,
      isKongWang
    };
  });

  return {
    success: true,
    input: {
      solarTerm,
      fourPillars,
      hourNumber,
      topic
    },
    meta: {
      type: 'shijia',
      system: '时家转盘奇门',
      juMethod: '拆补法',
      dun: chart.dun === 'yang' ? '阳遁' : '阴遁',
      dunRaw: chart.dun,
      juNumber: chart.juNumber,
      yuan: juResult.yuan + '元',
      solarTerm,
      zhiFuStar: chart.zhiFuStar,
      zhiFuPalace: chart.zhiFuPalace,
      zhiShiDoor: chart.zhiShiDoor,
      zhiShiPalace: chart.zhiShiPalace,
      kongWang: chart.kongWang,
      tianYiStar: chart.tianYiStar,
      tianYiPalace: chart.tianYiPalace
    },
    palaces,
    engine_version: 'bigfishmarquis-qimen 1.0.0',
    rules: {
      system: '时家转盘奇门',
      ju_method: '拆补定局（以精确节气交节为界，符头甲己定三元）',
      ji_gong: '中五宫天禽寄坤二宫天芮，天盘转盘顺布八神',
      layout_rule: '洛书九宫南上北下（离九南、坎一北、震三东、兑七西）'
    }
  };
}

// ─── MAIN DISPATCHER ──────────────────────────────────────────────
async function main() {
  try {
    const rawInput = await readStdin();
    if (!rawInput.trim()) {
      console.log(JSON.stringify({ error: 'No input provided on stdin' }));
      process.exit(1);
    }

    const payload = JSON.parse(rawInput);
    const { action, params } = payload;

    if (action === 'calculate_ziwei') {
      const res = calculateZiwei(params);
      console.log(JSON.stringify(res));
    } else if (action === 'calculate_qimen') {
      const res = calculateQimen(params);
      console.log(JSON.stringify(res));
    } else {
      console.log(JSON.stringify({ error: `Unknown action: ${action}` }));
      process.exit(1);
    }
  } catch (err: any) {
    console.log(JSON.stringify({ error: err?.message || String(err) }));
    process.exit(1);
  }
}

main();
