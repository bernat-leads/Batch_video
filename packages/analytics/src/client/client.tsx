"use client";

import React, { useEffect } from "react";
import type { ReactNode } from "react";
import posthog, { type PostHog } from "posthog-js";
import { PostHogProvider as PostHogProviderRaw } from "posthog-js/react";
import { env } from "../env";

type PostHogProviderProps = {
  readonly children: ReactNode;
};

export const PostHogProvider: React.FC<PostHogProviderProps> = ({ children }) => {
  const apiKey = env.NEXT_PUBLIC_POSTHOG_KEY;
  const host = env.NEXT_PUBLIC_POSTHOG_HOST;

  useEffect(() => {
    if (!apiKey || !host) return;

    posthog.init(apiKey, {
      api_host: "/ingest",
      ui_host: host,
      person_profiles: "identified_only",
      capture_pageview: false, // Disable automatic pageview capture, as we capture manually
      capture_pageleave: true, // Overrides the `capture_pageview` setting
    }) as PostHog;
  }, [apiKey, host]);

  if (!apiKey || !host) {
    return <>{children}</>;
  }

  return <PostHogProviderRaw client={posthog}>{children}</PostHogProviderRaw>;
};

export { usePostHog as useAnalytics } from "posthog-js/react";
