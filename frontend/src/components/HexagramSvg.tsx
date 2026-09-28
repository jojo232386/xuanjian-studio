// frontend/src/components/HexagramSvg.tsx - 精致六爻 SVG 绘制组件

import React from 'react';
import type { HexagramData, LineDetail } from '../types';

interface HexagramSvgProps {
  hexagram: HexagramData;
  lines: LineDetail[];
  title?: string;
  selectedLine?: number | null;
  onSelectLine?: (linePos: number) => void;
  showMovingMarks?: boolean;
}

export const HexagramSvg: React.FC<HexagramSvgProps> = ({
  hexagram,
  lines,
  title,
  selectedLine,
  onSelectLine,
  showMovingMarks = true
}) => {
  // 六爻自下而上排列：初爻为 lines[0]，上爻为 lines[5]
  // SVG 绘制坐标：从上往下 y 递增，所以 lines[5] 画在顶部，lines[0] 画在底部
  const width = 180;
  const height = 180;
  const lineHeight = 12;
  const lineSpacing = 24;
  const startY = 24; // 顶部起绘点

  return (
    <div className="flex flex-col items-center p-3 bg-[var(--xuanzhi-light)] border border-[var(--border)] rounded-lg shadow-sm transition-colors">
      {/* 卦名与简报 */}
      <div className="text-center mb-2">
        <div className="font-song text-base font-bold text-[var(--ink)]">
          {title ? `${title} · ` : ''}【{hexagram.name}】
        </div>
        <div className="text-xs text-[var(--ink-muted)]">
          {hexagram.full_name}（上{hexagram.upper_trigram} 下{hexagram.lower_trigram}）
        </div>
      </div>

      {/* SVG 卦画 */}
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="cursor-pointer select-none"
        role="img"
        aria-label={`${hexagram.name} 卦象图`}
      >
        {lines.map((line) => {
          // line.position 是 1..6 (1是初爻，6是上爻)
          // 视觉呈现：6在最上 (index=0 in visual), 1在最底 (index=5 in visual)
          const visualIndex = 6 - line.position;
          const y = startY + visualIndex * lineSpacing;
          const isSelected = selectedLine === line.position;
          const isMoving = line.is_moving && showMovingMarks;

          // 颜色定义：动爻用朱砂红，静爻用墨字色；选中时加光晕/高亮
          const fillColor = isMoving ? 'var(--zhusha)' : 'var(--ink)';

          return (
            <g
              key={line.position}
              onClick={() => onSelectLine && onSelectLine(line.position)}
              className="transition-transform duration-150 hover:opacity-80"
              tabIndex={0}
              role="button"
              aria-label={`第${line.position}爻 ${line.yao_name} (${line.nature}爻${isMoving ? ' 动爻' : ''})`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSelectLine && onSelectLine(line.position);
                }
              }}
            >
              {/* 爻位底框（点击区域） */}
              <rect
                x="10"
                y={y - 4}
                width={width - 20}
                height={lineHeight + 8}
                fill={isSelected ? 'var(--daiqing-light)' : 'transparent'}
                rx="3"
                stroke={isSelected ? 'var(--daiqing)' : 'transparent'}
                strokeWidth="1.5"
              />

              {line.bit === 1 ? (
                // 阳爻 (⚊ 一整条横线)
                <rect
                  x="20"
                  y={y}
                  width="140"
                  height={lineHeight}
                  fill={fillColor}
                  rx="2"
                />
              ) : (
                // 阴爻 (⚋ 中间断开两条线)
                <g>
                  <rect
                    x="20"
                    y={y}
                    width="62"
                    height={lineHeight}
                    fill={fillColor}
                    rx="2"
                  />
                  <rect
                    x="98"
                    y={y}
                    width="62"
                    height={lineHeight}
                    fill={fillColor}
                    rx="2"
                  />
                </g>
              )}

              {/* 动爻标记 (朱砂红小圆点/圈) */}
              {isMoving && (
                <circle
                  cx={line.bit === 1 ? "90" : "90"}
                  cy={y + lineHeight / 2}
                  r="4"
                  fill="var(--xuanzhi-card)"
                  stroke="var(--zhusha)"
                  strokeWidth="2"
                />
              )}

              {/* 爻位提示小文字 */}
              <text
                x="8"
                y={y + lineHeight - 2}
                fontSize="9"
                fill={isSelected ? 'var(--daiqing)' : 'var(--ink-subtle)'}
                fontFamily="sans-serif"
                textAnchor="end"
              >
                {line.position}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="text-[11px] text-[var(--ink-subtle)] mt-1">
        点击爻线可联动查看爻辞
      </div>
    </div>
  );
};
