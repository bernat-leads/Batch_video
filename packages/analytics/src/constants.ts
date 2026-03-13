// PostHog Event Constants
export const POSTHOG_EVENTS = {
  // Waitlist (existing)
  WAITLIST_ENTRY_CREATED: "waitlist_entry_created",
  WAITLIST_ENTRY_DELETED: "waitlist_entry_deleted",

  // Auth
  USER_SIGNED_IN: "user_signed_in",
  USER_SIGNED_UP: "user_signed_up",
  USER_SIGNED_OUT: "user_signed_out",

  // Chat
  CHAT_CONVERSATION_STARTED: "chat_conversation_started",
  CHAT_MESSAGE_SENT: "chat_message_sent",

  // Profile
  PROFILE_PAGE_VIEWED: "profile_page_viewed",

  // Page Views
  PAGE_VIEW: "$pageview",
} as const;

export const POSTHOG_PROPERTIES = {
  EVENT_TYPE: "backend",
  EVENT_SOURCE: "waitlist-service",
} as const;
