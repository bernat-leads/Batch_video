/**
 * Mock data factories for E2E tests.
 *
 * Each factory generates data with unique IDs to ensure test isolation.
 * Tests never share data — each call produces fresh objects.
 */

import { randomUUID } from "crypto";

// ---------------------------------------------------------------------------
// Types (mirrors API schemas)
// ---------------------------------------------------------------------------

interface AICost {
  token_count: number;
  cost_usd: number;
}

interface BatchRead {
  id: string;
  name: string;
  status: "processing" | "completed" | "failed";
  total_videos: number;
  completed_count: number;
  failed_count: number;
  pending_count: number;
  duration_ms: number;
  tts: AICost;
  segmentation: AICost;
  image_generation: AICost;
  total: AICost;
  column_mapping: Record<string, string> | null;
  file_name: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
}

interface VideoRead {
  id: string;
  batch_id: string | null;
  script_text: string;
  voice_id: string | null;
  style: string | null;
  top_text: string | null;
  prompt: string;
  status: "processing" | "finished" | "failed";
  current_stage: string;
  error_message: string | null;
  output_url: string | null;
  audio_url: string | null;
  duration_ms: number;
  file_size_bytes: number;
  tts: AICost;
  segmentation: AICost;
  image_generation: AICost;
  total: AICost;
  created_at: string;
  updated_at: string | null;
}

interface DashboardStats {
  total_videos: number;
  completed_videos: number;
  failed_videos: number;
  processing_videos: number;
  total_batches: number;
  total_duration_ms: number;
  tts: AICost;
  segmentation: AICost;
  image_generation: AICost;
  total: AICost;
  avg_tts: AICost;
  avg_segmentation: AICost;
  avg_image_generation: AICost;
  avg_total: AICost;
  avg_duration_ms: number;
}

interface DailyStats {
  date: string;
  videos: number;
  cost_usd: number;
  duration_ms: number;
}

interface DashboardResponse {
  stats: DashboardStats;
  daily: DailyStats[];
}

interface Settings {
  master_prompt: string;
  retention_days: number;
  default_voice_id: string;
  default_style: string;
}

export interface MockData {
  batches: BatchRead[];
  videos: VideoRead[];
  dashboardResponse: DashboardResponse;
}

// ---------------------------------------------------------------------------
// Factories
// ---------------------------------------------------------------------------

const zeroCost: AICost = { token_count: 0, cost_usd: 0 };

function isoNow(): string {
  return new Date().toISOString();
}

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString();
}

export const mockFactories = {
  batch(overrides: Partial<BatchRead> = {}): BatchRead {
    return {
      id: randomUUID(),
      name: `Batch ${Math.random().toString(36).slice(2, 6)}`,
      status: "completed",
      total_videos: 5,
      completed_count: 5,
      failed_count: 0,
      pending_count: 0,
      duration_ms: 25000,
      tts: { token_count: 500, cost_usd: 0.05 },
      segmentation: { token_count: 1200, cost_usd: 0.02 },
      image_generation: { token_count: 0, cost_usd: 0.10 },
      total: { token_count: 1700, cost_usd: 0.17 },
      column_mapping: { script: "script_text" },
      file_name: "campaign.xlsx",
      error_message: null,
      created_at: isoDaysAgo(2),
      updated_at: isoDaysAgo(1),
      ...overrides,
    };
  },

  video(overrides: Partial<VideoRead> = {}): VideoRead {
    return {
      id: randomUUID(),
      batch_id: null,
      script_text: "Buy our amazing product today! Limited time offer.",
      voice_id: "rachel",
      style: "energetic",
      top_text: null,
      prompt: "Create a compelling ad video",
      status: "finished",
      current_stage: "done",
      error_message: null,
      output_url: "videos/output.mp4",
      audio_url: "videos/audio.mp3",
      duration_ms: 5000,
      file_size_bytes: 1024000,
      tts: { token_count: 100, cost_usd: 0.01 },
      segmentation: { token_count: 250, cost_usd: 0.004 },
      image_generation: { token_count: 0, cost_usd: 0.02 },
      total: { token_count: 350, cost_usd: 0.034 },
      created_at: isoDaysAgo(1),
      updated_at: isoNow(),
      ...overrides,
    };
  },

  dashboardResponse(overrides: Partial<DashboardStats> = {}): DashboardResponse {
    return {
      stats: {
        total_videos: 0,
        completed_videos: 0,
        failed_videos: 0,
        processing_videos: 0,
        total_batches: 0,
        total_duration_ms: 0,
        tts: zeroCost,
        segmentation: zeroCost,
        image_generation: zeroCost,
        total: zeroCost,
        avg_tts: zeroCost,
        avg_segmentation: zeroCost,
        avg_image_generation: zeroCost,
        avg_total: zeroCost,
        avg_duration_ms: 0,
        ...overrides,
      },
      daily: [],
    };
  },

  settings(overrides: Partial<Settings> = {}): Settings {
    return {
      master_prompt: "Create a compelling short-form video ad.",
      retention_days: 7,
      default_voice_id: "rachel",
      default_style: "energetic",
      ...overrides,
    };
  },

  /** Generate a full dataset with linked batches and videos. */
  fullDataset(): MockData {
    const batch1 = mockFactories.batch({ name: "Q1 Campaign", total_videos: 3, completed_count: 2, failed_count: 1 });
    const batch2 = mockFactories.batch({ name: "Product Launch", status: "processing", total_videos: 2, completed_count: 0, pending_count: 2, failed_count: 0 });

    const videos: VideoRead[] = [
      mockFactories.video({ batch_id: batch1.id, script_text: "Try our new skincare line today!", status: "finished" }),
      mockFactories.video({ batch_id: batch1.id, script_text: "Limited time offer — 50% off!", status: "finished" }),
      mockFactories.video({ batch_id: batch1.id, script_text: "Best results guaranteed.", status: "failed", current_stage: "image_generation", error_message: "Gemini API error" }),
      mockFactories.video({ batch_id: batch2.id, script_text: "Introducing our latest product.", status: "processing", current_stage: "tts", output_url: null }),
      mockFactories.video({ batch_id: batch2.id, script_text: "Order now and save big!", status: "processing", current_stage: "segmentation", output_url: null }),
    ];

    return {
      batches: [batch1, batch2],
      videos,
      dashboardResponse: mockFactories.dashboardResponse({
        total_videos: 5,
        completed_videos: 2,
        failed_videos: 1,
        processing_videos: 2,
        total_batches: 2,
        total_duration_ms: 10000,
      }),
    };
  },
};
