import { Resend } from "resend";

export interface EmailConfig {
  token: string;
  from?: string;
}

export function createEmailClient(config: EmailConfig) {
  return new Resend(config.token);
}
