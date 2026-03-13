"use client";

import type React from "react";
import { useEffect, useRef } from "react";
import { useInView } from "motion/react";
import { annotate } from "rough-notation";

type AnnotationAction =
  | "highlight"
  | "underline"
  | "box"
  | "circle"
  | "strike-through"
  | "crossed-off"
  | "bracket";

export interface HighlighterProps {
  children: React.ReactNode;
  action?: AnnotationAction;
  color?: string;
  strokeWidth?: number;
  animationDuration?: number;
  iterations?: number;
  padding?: number;
  multiline?: boolean;
  isView?: boolean;
  delay?: number;
}

export function Highlighter({
  children,
  action = "highlight",
  color = "#ffd1dc",
  strokeWidth = 1.5,
  animationDuration = 600,
  iterations = 2,
  padding = 2,
  multiline = true,
  isView = false,
  delay = 0,
}: HighlighterProps) {
  const elementRef = useRef<HTMLSpanElement>(null);
  const annotationRef = useRef<ReturnType<typeof annotate> | null>(null);
  const isInView = useInView(elementRef, {
    once: true,
    margin: "-10%",
  });

  // If isView is false, always show. If isView is true, wait for inView
  const shouldShow = !isView || isInView;

  useEffect(() => {
    if (!shouldShow) return;

    const element = elementRef.current;
    if (!element) return;

    const timeoutId = setTimeout(() => {
      const annotation = annotate(element, {
        type: action,
        color,
        strokeWidth,
        animationDuration,
        iterations,
        padding,
        multiline,
      });

      annotation.show();
      annotationRef.current = annotation;
    }, delay);

    return () => {
      clearTimeout(timeoutId);
      annotate(element, { type: action }).remove();
    };
  }, [
    shouldShow,
    action,
    color,
    strokeWidth,
    animationDuration,
    iterations,
    padding,
    multiline,
    delay,
  ]);

  return (
    <span ref={elementRef} className="relative inline-block bg-transparent">
      {children}
    </span>
  );
}
