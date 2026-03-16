import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface CompletionChartProps {
  completed: number;
  total: number;
  /** When true, fills the chart with error color instead of success. */
  hasFailed: boolean;
}

/** Radial progress donut showing completed/total ratio with a centered label. */
export function CompletionChart({ completed, total, hasFailed }: CompletionChartProps) {
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
  const fill = hasFailed ? "var(--color-error)" : "var(--color-success)";
  const data = [{ value: percent }];

  return (
    <div className="flex shrink-0 flex-col items-center gap-1">
      <div className="relative h-[72px] w-[72px]">
        <RadialBarChart
          width={72}
          height={72}
          cx={36}
          cy={36}
          innerRadius={27}
          outerRadius={33}
          barSize={6}
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            angleAxisId={0}
            tick={false}
          />
          <RadialBar
            background={{ fill: "var(--border-color)" }}
            dataKey="value"
            cornerRadius={3}
            fill={fill}
          />
        </RadialBarChart>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-sm font-semibold text-text-primary">
            {completed}/{total}
          </span>
        </div>
      </div>
      <span className="text-xs text-text-muted">Videos Completed</span>
    </div>
  );
}
