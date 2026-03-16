/**
 * URL builders for endpoints that return redirects or binary content.
 * Used for <a href>, <video src>, <img src> where axios can't be used.
 */
import { env } from "./env";

export const videoPreviewUrl = (videoId: string) =>
  `${env.PUBLIC_API_URL}/api/v1/videos/${videoId}/preview`;

export const shotPreviewUrl = (videoId: string, shotOrder: number) =>
  `${env.PUBLIC_API_URL}/api/v1/videos/${videoId}/shots/${shotOrder}/preview`;

export const videoEventsUrl = (videoId: string) =>
  `${env.PUBLIC_API_URL}/api/v1/events/videos/${videoId}`;

export const batchEventsUrl = (batchId: string) =>
  `${env.PUBLIC_API_URL}/api/v1/events/batches/${batchId}`;
