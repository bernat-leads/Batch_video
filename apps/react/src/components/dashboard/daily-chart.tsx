import {
  AreaChart,
  Area,
  XAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { DailyStats } from "@packages/api-client";
import { SectionCard } from "@/components/ui/section-card";
import { formatDuration, formatCurrency } from "@/lib/format";

const CHART_SERIES = [
  { key: "videos", label: "Videos", color: "var(--brand)" },
  { key: "tokens", label: "Tokens", color: "var(--color-chart-purple)" },
  { key: "duration_ms", label: "Video Length", color: "var(--color-chart-amber)" },
  { key: "cost_usd", label: "Cost", color: "var(--color-chart-emerald)" },
];

interface DailyChartProps {
  data: DailyStats[];
}

/** Stacked area chart showing daily video production metrics on the dashboard. */
export function DailyChart({ data }: DailyChartProps) {
  return (
    <div>
      <p className="mb-3 text-sm font-medium text-text-primary">Daily Overview</p>
      <SectionCard>
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                {CHART_SERIES.map((s) => (
                  <linearGradient
                    key={s.key}
                    id={`grad-${s.key}`}
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor={s.color} stopOpacity={0.1} />
                    <stop offset="100%" stopColor={s.color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border-color)"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "var(--text-muted)" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--card-bg)",
                  borderColor: "var(--border-color)",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "var(--text-primary)",
                }}
                labelStyle={{ color: "var(--text-muted)", marginBottom: 2 }}
                formatter={(value: number, name: string) => {
                  if (name === "Cost") return [formatCurrency(value), name];
                  if (name === "Video Length")
                    return [formatDuration(value), name];
                  if (name === "Tokens") return [value.toLocaleString(), name];
                  return [value, name];
                }}
              />
              {CHART_SERIES.map((s) => (
                <Area
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.label}
                  stroke={s.color}
                  strokeWidth={2}
                  fill={`url(#grad-${s.key})`}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex items-center justify-center gap-5">
          {CHART_SERIES.map((s) => (
            <div key={s.key} className="flex items-center gap-1.5">
              <div
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span className="text-xs text-text-muted">{s.label}</span>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
