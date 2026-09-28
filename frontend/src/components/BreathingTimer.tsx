// frontend/src/components/BreathingTimer.tsx - 观息与专注陪伴计时 (自然节律，无功德考核，非强迫)

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Play, Pause, RotateCcw, CheckCircle2, Wind, Eye, EyeOff, Info, Clock } from 'lucide-react';

interface BreathingTimerProps {
  onComplete?: () => void;
}

type TimerState = 'idle' | 'running' | 'paused' | 'completed';

export const BreathingTimer: React.FC<BreathingTimerProps> = ({ onComplete }) => {
  // 预设时长（秒）：3分钟、5分钟、10分钟
  const [selectedMinutes, setSelectedMinutes] = useState<number>(5);
  const [customMinutes, setCustomMinutes] = useState<string>('5');
  const [isCustom, setIsCustom] = useState<boolean>(false);

  // 运行状态与经过时间（毫秒）
  const [timerState, setTimerState] = useState<TimerState>('idle');
  const [elapsedMs, setElapsedMs] = useState<number>(0);
  const [showRhythm, setShowRhythm] = useState<boolean>(true);

  // 呼吸节律阶段 (4秒吸气，6秒呼气，共10秒一周期，自然放松副交感神经)
  const [breathPhase, setBreathPhase] = useState<'inhale' | 'exhale'>('inhale');
  const [phaseSecondsLeft, setPhaseSecondsLeft] = useState<number>(4);

  // 引用变量追踪高精度时钟，防 setInterval 漂移
  const startTimeRef = useRef<number>(0);
  const accumulatedMsRef = useRef<number>(0);
  const timerRef = useRef<number | null>(null);

  const targetSeconds = useMemo(() => {
    if (isCustom) {
      const parsed = parseInt(customMinutes, 10);
      if (isNaN(parsed) || parsed < 1) return 60;
      if (parsed > 60) return 3600;
      return parsed * 60;
    }
    return selectedMinutes * 60;
  }, [isCustom, customMinutes, selectedMinutes]);

  const targetMs = targetSeconds * 1000;
  const remainingMs = Math.max(0, targetMs - elapsedMs);
  const remainingSeconds = Math.ceil(remainingMs / 1000);

  // 清理计时器防泄漏
  const clearTimer = () => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      clearTimer();
    };
  }, []);

  // 页面离开/切换/熄屏恢复支持：基于真实物理时钟 Date.now() 更新
  const handleTick = () => {
    if (startTimeRef.current === 0) return;
    const currentNow = Date.now();
    const currentRun = currentNow - startTimeRef.current;
    const totalElapsed = accumulatedMsRef.current + currentRun;

    if (totalElapsed >= targetMs) {
      clearTimer();
      setElapsedMs(targetMs);
      setTimerState('completed');
      startTimeRef.current = 0;
      accumulatedMsRef.current = 0;
      if (onComplete) onComplete();
      return;
    }

    setElapsedMs(totalElapsed);

    // 呼吸引导阶段计算 (每 10000ms 一个循环：前 4000ms 为吸，后 6000ms 为呼)
    const cycleTime = totalElapsed % 10000;
    if (cycleTime < 4000) {
      setBreathPhase('inhale');
      setPhaseSecondsLeft(Math.ceil((4000 - cycleTime) / 1000));
    } else {
      setBreathPhase('exhale');
      setPhaseSecondsLeft(Math.ceil((10000 - cycleTime) / 1000));
    }
  };

  // 开始计时
  const handleStart = () => {
    if (timerState === 'running') return; // 防重复点击
    clearTimer();
    startTimeRef.current = Date.now();
    setTimerState('running');
    timerRef.current = window.setInterval(handleTick, 100);
  };

  // 暂停计时
  const handlePause = () => {
    if (timerState !== 'running') return;
    clearTimer();
    if (startTimeRef.current > 0) {
      accumulatedMsRef.current += Date.now() - startTimeRef.current;
      startTimeRef.current = 0;
    }
    setTimerState('paused');
  };

  // 恢复继续
  const handleResume = () => {
    if (timerState !== 'paused') return;
    startTimeRef.current = Date.now();
    setTimerState('running');
    timerRef.current = window.setInterval(handleTick, 100);
  };

  // 提前舒缓收束 (不判定为破功或失败)
  const handleEarlyFinish = () => {
    clearTimer();
    setTimerState('completed');
    startTimeRef.current = 0;
    accumulatedMsRef.current = 0;
  };

  // 重置
  const handleReset = () => {
    clearTimer();
    startTimeRef.current = 0;
    accumulatedMsRef.current = 0;
    setElapsedMs(0);
    setTimerState('idle');
    setBreathPhase('inhale');
    setPhaseSecondsLeft(4);
  };

  // 格式化时间 mm:ss
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col items-center gap-6 max-w-xl mx-auto w-full">
      {/* 头部理念与边界告知 */}
      <div className="text-center">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-[var(--daiqing-light)] text-[var(--daiqing)] text-xs font-song mb-2 border border-[var(--border)]">
          <Wind size={13} />
          自然观息 · 身心守正
        </div>
        <h3 className="font-song text-xl font-bold text-[var(--ink)]">专注与呼吸陪伴</h3>
        <p className="text-xs text-[var(--ink-muted)] mt-1 max-w-md mx-auto leading-relaxed">
          不限体位，无需闭气强练。若觉胸闷、疲乏或注意力散乱，随时可停，恢复自然作息。
        </p>
      </div>

      {/* 时长选项选择 (仅在未开始或完成重置时可换) */}
      {timerState === 'idle' && (
        <div className="flex flex-wrap items-center justify-center gap-2 w-full">
          {[3, 5, 10].map((mins) => (
            <button
              key={mins}
              onClick={() => {
                setIsCustom(false);
                setSelectedMinutes(mins);
              }}
              className={`px-4 py-2 rounded text-xs font-medium border transition ${
                !isCustom && selectedMinutes === mins
                  ? 'bg-[var(--daiqing)] text-white border-[var(--daiqing)]'
                  : 'bg-[var(--xuanzhi-card)] text-[var(--ink)] border-[var(--border)] hover:bg-[var(--border-light)]'
              }`}
            >
              {mins} 分钟
            </button>
          ))}

          <button
            onClick={() => setIsCustom(true)}
            className={`px-4 py-2 rounded text-xs font-medium border transition ${
              isCustom
                ? 'bg-[var(--daiqing)] text-white border-[var(--daiqing)]'
                : 'bg-[var(--xuanzhi-card)] text-[var(--ink)] border-[var(--border)] hover:bg-[var(--border-light)]'
            }`}
          >
            自定义时长
          </button>

          {isCustom && (
            <div className="flex items-center gap-1.5 ml-2">
              <input
                type="number"
                min="1"
                max="60"
                value={customMinutes}
                onChange={(e) => setCustomMinutes(e.target.value)}
                className="input-xuan w-16 text-center text-xs py-1.5 px-2"
                aria-label="自定义专注分钟数"
              />
              <span className="text-xs text-[var(--ink-muted)]">分钟</span>
            </div>
          )}
        </div>
      )}

      {/* 视觉呼吸节律指示器与计时核心圈 */}
      <div className="relative flex flex-col items-center justify-center my-2">
        {/* 背景轻柔水墨波纹动画 */}
        <div
          className={`w-64 h-64 rounded-full border border-[var(--border)] flex flex-col items-center justify-center transition-all duration-1000 ${
            timerState === 'running' && showRhythm
              ? breathPhase === 'inhale'
                ? 'scale-105 bg-[var(--daiqing-light)] border-[var(--daiqing)]'
                : 'scale-95 bg-[var(--xuanzhi-card)] border-[var(--border)]'
              : 'bg-[var(--xuanzhi-card)] shadow-inner'
          }`}
          style={{ transitionDuration: breathPhase === 'inhale' ? '4000ms' : '6000ms' }}
        >
          {/* 剩余倒计时 */}
          <div className="font-song text-4xl font-bold tracking-wider text-[var(--ink)]">
            {formatTime(remainingSeconds)}
          </div>

          {/* 状态与呼吸阶段文案 */}
          <div className="mt-2 text-xs font-song flex flex-col items-center">
            {timerState === 'idle' && (
              <span className="text-[var(--ink-muted)]">静心准备 · 点击开始</span>
            )}

            {timerState === 'running' && (
              <>
                {showRhythm ? (
                  <span className="text-[var(--daiqing)] font-medium">
                    {breathPhase === 'inhale' ? '吸气 · 自然舒缓' : '呼气 · 渐次放下'} ({phaseSecondsLeft}s)
                  </span>
                ) : (
                  <span className="text-[var(--ink-muted)]">专注计时进行中...</span>
                )}
              </>
            )}

            {timerState === 'paused' && (
              <span className="text-[var(--zhusha)] font-medium">已暂停 · 放松休息</span>
            )}

            {timerState === 'completed' && (
              <div className="flex items-center gap-1 text-[var(--daiqing)] font-medium">
                <CheckCircle2 size={14} />
                <span>此轮已恬然收束</span>
              </div>
            )}
          </div>

          {/* 进度弧形条比例 */}
          <div className="w-36 h-1.5 bg-[var(--border-light)] rounded-full mt-4 overflow-hidden">
            <div
              className="h-full bg-[var(--daiqing)] transition-all duration-200"
              style={{
                width: `${Math.min(100, Math.round((elapsedMs / (targetMs || 1)) * 100))}%`
              }}
            />
          </div>
        </div>
      </div>

      {/* 控制按钮区域 */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {timerState === 'idle' && (
          <button
            onClick={handleStart}
            className="btn-primary px-6 py-2.5 text-sm font-song flex items-center gap-2"
          >
            <Play size={16} />
            开始观息
          </button>
        )}

        {timerState === 'running' && (
          <>
            <button
              onClick={handlePause}
              className="btn-secondary px-4 py-2 text-xs font-song flex items-center gap-1.5"
            >
              <Pause size={14} />
              暂停
            </button>
            <button
              onClick={handleEarlyFinish}
              className="btn-secondary px-4 py-2 text-xs font-song border-[var(--border)] text-[var(--ink-muted)] hover:text-[var(--ink)]"
            >
              提前结束
            </button>
          </>
        )}

        {timerState === 'paused' && (
          <>
            <button
              onClick={handleResume}
              className="btn-primary px-5 py-2 text-xs font-song flex items-center gap-1.5"
            >
              <Play size={14} />
              继续
            </button>
            <button
              onClick={handleReset}
              className="btn-secondary px-4 py-2 text-xs font-song flex items-center gap-1.5"
            >
              <RotateCcw size={14} />
              重置
            </button>
          </>
        )}

        {timerState === 'completed' && (
          <button
            onClick={handleReset}
            className="btn-secondary px-5 py-2 text-xs font-song flex items-center gap-1.5"
          >
            <RotateCcw size={14} />
            再行一轮
          </button>
        )}

        {/* 呼吸引导节律开关 */}
        <button
          onClick={() => setShowRhythm(!showRhythm)}
          className="btn-secondary px-3 py-2 text-xs text-[var(--ink-muted)] hover:text-[var(--ink)] flex items-center gap-1"
          title="开关视觉呼吸引导"
        >
          {showRhythm ? <Eye size={13} /> : <EyeOff size={13} />}
          <span>{showRhythm ? '节律引导已开' : '纯静纯钟模式'}</span>
        </button>
      </div>

      {/* 底部理性声明与无功德考核说明 */}
      <div className="w-full card-xuan p-4 bg-[var(--xuanzhi-light)] text-[var(--ink-muted)] text-xs flex flex-col gap-2">
        <div className="flex items-start gap-2">
          <Info size={14} className="text-[var(--daiqing)] shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold text-[var(--ink)]">理性守则与身心防线：</span>
            本模块为清雅专注陪伴，绝不计连胜、不宣称“功德”、不因中断产生“破功”焦虑，更无任何强迫跟拍机制。
            若有任何头晕、呼吸急促或不适，请立刻恢复日常自然呼吸。
          </div>
        </div>
        <div className="flex items-start gap-2 border-t border-[var(--border-light)] pt-2 text-[11px] text-[var(--ink-subtle)]">
          <Clock size={13} className="shrink-0 mt-0.5" />
          <span>
            浏览器边界说明：依赖当前浏览器标签页保持活动运行。若设备进入系统级睡眠、熄屏挂起或深度省电模式，计时器可能被操作系统暂停，计时将在唤醒后按真实时间核算继续，不具备操作系统级强提醒闹钟功能。
          </span>
        </div>
      </div>
    </div>
  );
};
