# User Guide

This guide walks you through using the Lead Alliances Bulk Video Pipeline to create short-form video ads from your scripts.

---

## Getting Started

### Logging In

1. Open the application URL in your browser.
2. Enter the shared team password on the login screen.
3. You will be taken to the Dashboard.

Your session stays active for 7 days. After that, you will need to log in again.

---

## Dashboard

The Dashboard is the first thing you see after logging in. It provides an overview of your video production activity.

### Stats Cards

At the top of the Dashboard, you will see summary cards showing:

- **Total Videos** -- The total number of videos created across all batches.
- **Completed** -- How many videos have finished processing and are ready to download.
- **In Progress** -- Videos currently being processed through the pipeline.
- **Failed** -- Videos that encountered an error during processing.

### Daily Chart

Below the stats, a chart shows your video production over recent days. This helps you track output volume over time.

### Recent Tables

The Dashboard also shows your most recent batches and videos for quick access.

---

## Creating a Batch

A batch is a group of videos created from a single Excel upload. This is the primary way to produce videos at scale.

### Step 1: Prepare Your Excel File

Create an Excel file (.xlsx, .xls) or CSV file with your ad scripts. The file should have the following columns:

| Column | Required | Description |
|--------|----------|-------------|
| `script_text` | Yes | The full ad script text that will become the video voiceover and captions |
| `voice_id` | No | ElevenLabs voice ID to use for this script (uses default if omitted) |
| `style` | No | Visual style direction for image generation |
| `top_text` | No | Text overlay displayed at the top of the video |

Each row in the file becomes one video. You can include 10 to 100 scripts per file.

**Tips for writing scripts:**

- Keep scripts between 30 and 90 seconds when read aloud.
- Write naturally -- the text-to-speech engine handles conversational tone well.
- Avoid special characters or formatting that would not make sense when spoken.

### Step 2: Upload the File

1. From the Dashboard or the Batches page, click the **Create Batch** button.
2. In the dialog that appears, drag and drop your Excel file or click to browse and select it.
3. The system validates your file. If there are issues (wrong format, missing required columns, file too large), you will see an error message explaining what to fix.

The maximum file size is 10 MB.

### Step 3: Map Columns

After uploading, the system shows you the columns found in your file. You need to map them to the expected fields:

- Match your file's column names to the system's expected fields (script_text, voice_id, style, top_text).
- If your column names already match, they will be mapped automatically.
- If you have set default column mappings in Settings, those will be applied first.

Review the mapping to make sure each column is assigned correctly.

### Step 4: Review and Submit

Before processing begins, you will see a summary showing:

- The batch name
- Number of scripts detected
- Column mappings
- A preview of the first few rows

Click **Submit** to start processing. The system creates a video job for each row and begins processing them through the pipeline.

---

## Creating a Single Video

If you only need one video, you can create it without an Excel file:

1. Click the **Create Video** button.
2. Enter your script text in the text area.
3. Optionally adjust the voice, style, or top text.
4. The prompt field is pre-filled from your master prompt in Settings. You can modify it for this specific video if needed.
5. Click **Create** to submit.

The video enters the pipeline and you can monitor its progress from the Videos page or Dashboard.

---

## Monitoring Progress

### Batch Progress

On the Batches page, each batch shows an overall progress summary based on the status of its individual videos. Click on a batch to see the detail page with every video listed and its current status.

### Video Status

Each video shows its current status:

- **Queued** -- Waiting to be picked up by a worker.
- **Processing** -- Currently being worked on (see the stage indicator for which step).
- **Completed** -- Finished and ready to download.
- **Failed** -- An error occurred. Check the error message for details.

### Stage Indicator

While a video is processing, the stage indicator shows exactly which pipeline step it is on:

1. **Queued** -- Waiting in line
2. **Audio (TTS)** -- Generating voiceover
3. **Segmentation** -- Analyzing script and creating scene breakdowns
4. **Image Gen** -- Creating visual images for each scene
5. **Assembly** -- Composing the final video
6. **Done** -- Complete

On the Videos table, this appears as a compact progress bar. On the Video detail page, it appears as a full indicator with icons and labels for each stage.

The system polls for updates automatically every few seconds, so you do not need to refresh the page.

---

## Pipeline Stages

Understanding what happens at each stage helps you troubleshoot issues and write better scripts.

### 1. Text-to-Speech (ElevenLabs)

Your script text is sent to ElevenLabs, which generates a natural-sounding voiceover audio file. The system also receives word-level timestamps, which are used later to sync captions with the audio.

### 2. Segmentation (Claude AI)

The script and audio timestamps are sent to Claude, which analyzes the narrative flow and breaks the script into 5 to 8 second visual segments (called "shots"). For each shot, Claude generates:

- An image prompt describing what the viewer should see
- Ken Burns camera directions (pan, zoom, direction) to add motion to the still images

### 3. Image Generation (Gemini Imagen 3)

Each shot's image prompt is sent to Google's Gemini Imagen 3, which generates a 1080x1920 portrait image. Multiple images within a single video are generated in parallel to speed up processing.

### 4. Assembly (Remotion)

All the pieces come together:

- The voiceover audio plays as the soundtrack
- Generated images display in sequence with Ken Burns pan and zoom effects
- TikTok-style captions are burned into the video, synced word-by-word with the audio
- The output is a 1080x1920 H.264 MP4 file

The finished video is uploaded to cloud storage and a download link becomes available.

---

## Downloading Videos

### Individual Download

On any video's detail page, click the **Download** button to download the MP4 file directly to your computer.

You can also download from the Videos table using the actions menu on each row.

### Batch ZIP Export

On a batch's detail page, you can download all completed videos in that batch as a single ZIP file. This is useful when you need to deliver a full set of videos at once.

### Storage Expiry

Videos are stored in the cloud for **7 days** after creation. After that, the files are automatically deleted to manage storage costs. The batch and video records remain in the system (marked as expired), but the MP4 files will no longer be available for download.

Download your videos promptly after they are completed.

---

## Retrying Failed Videos

If a video fails during processing:

1. Go to the video's detail page to see the error message and which stage failed.
2. Click the **Retry** button to resubmit the video to the pipeline.
3. The system retries from the failed stage, not from the beginning, so previously completed stages are preserved.

Common reasons for failure:

- **API rate limits** -- External services (ElevenLabs, Gemini) may temporarily reject requests if too many are sent at once. The system automatically retries up to 5 times with increasing wait times, but persistent rate limiting can still cause failures. Wait a few minutes and retry.
- **Content policy** -- Image generation may be rejected if the script content triggers content safety filters. Revise the script to avoid restricted topics.
- **Timeout** -- Very long scripts may exceed processing time limits. Try splitting into shorter scripts.

---

## Settings

Access Settings from the navigation sidebar. These settings apply to all new videos.

### Master Prompt

The master prompt provides overall creative direction for the AI when generating image prompts and segmentation decisions. It is copied into each video at creation time. Changes to the master prompt only affect videos created after the change.

### Retention Days

Configure how many days videos are kept in cloud storage before automatic deletion. The default is 7 days.

### Default Column Mapping

Set default mappings between your Excel column names and the system's expected fields. This saves time when you consistently use the same column naming in your spreadsheets. During batch creation, these defaults are applied automatically but can be overridden.

---

## Troubleshooting

### "File format not supported"

The system accepts `.xlsx`, `.xls`, and `.csv` files only. Make sure your file has the correct extension and is not corrupted. The maximum file size is 10 MB.

### "Missing required column: script_text"

Your Excel file must have a column that maps to `script_text`. Check that your file has a column containing the ad script text and that it is correctly mapped during the column mapping step.

### Videos stuck in "Queued" status

This usually means the Celery workers are not running or are busy with other tasks. If you are running the system locally, make sure you started the Celery worker. In production, the workers start automatically. If all workers are busy, new videos wait in the queue until a worker becomes available.

### Videos fail at the "Image Gen" stage

This is most commonly caused by content policy filtering from the image generation service, or by rate limiting. Check the error message on the video detail page. If it mentions content policy, revise the script. If it mentions rate limits, wait a few minutes and retry.

### Videos fail at the "Audio (TTS)" stage

Check that the ElevenLabs API key is valid and has sufficient quota. If you specified a custom `voice_id` in your Excel file, verify that the voice ID exists in your ElevenLabs account.

### Downloaded video has no audio or captions

This can happen if the assembly stage encountered a partial failure. Try retrying the video. If the problem persists, check the video detail page for any warnings.

### Cannot download -- "File expired"

Videos are automatically deleted from storage after the retention period (default 7 days). Once expired, the MP4 file cannot be recovered. The video record and metadata remain visible in the system, but the download button will be disabled.

### Page shows stale data

The application polls for updates every 3 seconds. If data appears stale, try refreshing the page in your browser. If the issue persists, log out and log back in.
