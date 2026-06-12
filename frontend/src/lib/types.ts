export type AutomationStatus = "active" | "paused" | "error";
export type LogoPosition =
  | "top_left"
  | "top_center"
  | "top_right"
  | "center"
  | "bottom_left"
  | "bottom_center"
  | "bottom_right"
  | "full_overlay";

export type QueueStatus =
  | "draft"
  | "queued"
  | "waiting"
  | "downloading"
  | "editing"
  | "uploading"
  | "submitting"
  | "completed"
  | "retrying"
  | "failed"
  | "force_stopped"
  | "rejected";

export interface Automation {
  id: string;
  name: string;
  platform: "instagram" | "youtube" | "tiktok";
  status: AutomationStatus;
  instagram_account_id: string | null;
  min_reel_duration_seconds: number;
  logo_position: LogoPosition;
  logo_size_percent: number;
  logo_opacity_percent: number;
  chroma_key_color: string | null;
  caption_template: string | null;
  daily_upload_target: number;
  daily_target_overrides: (number | null)[] | null;
  night_mode_start: string;
  night_mode_end: string;
  timezone: string;
  queue_capacity: number;
  clipster_submission_url: string | null;
  clipster_error: string | null;
  logo_file_path: string | null;
  logo_type: string | null;
  has_thumbnail: boolean;
  has_clipster_cookies: boolean;
  proxy_url: string | null;
}

export interface QueueItem {
  id: string;
  automation_id: string;
  source_url: string;
  status: QueueStatus;
  rejection_reason: "too_short" | "duplicate" | "queue_full" | "invalid_url" | null;
  duration_seconds: number | null;
  scheduled_at: string | null;
  uploaded_reel_url: string | null;
  retry_count: number;
  last_error: string | null;
  has_thumbnail: boolean;
}

export interface IgAccount {
  id: string;
  ig_user_id: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface Me {
  id: string;
  email: string;
  display_name: string | null;
  role: "user" | "admin" | "master_admin";
  plan_name?: string | null;
}
