import type { ResultSetHeader, RowDataPacket } from "mysql2/promise";
import { getPool, queryRows } from "@/lib/db";
import type { DisplayPayload, FlaskResult } from "@/lib/flask";
import { extractGeneratedAudioUrl, extractGeneratedImageUrl } from "@/lib/flask";

export type MessageRow = RowDataPacket & {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  text: string;
  asset_url: string | null;
  asset_kind: string | null;
  display_json: unknown;
  created_at: Date;
};

export async function insertMessage(
  conversationId: number,
  role: "user" | "assistant" | "system",
  text: string,
  options?: {
    assetUrl?: string | null;
    assetKind?: string | null;
    display?: DisplayPayload | null;
  }
) {
  const [result] = await getPool().execute<ResultSetHeader>(
    `INSERT INTO messages (conversation_id, role, text, asset_url, asset_kind, display_json)
     VALUES (:conversationId, :role, :text, :assetUrl, :assetKind, :displayJson)`,
    {
      conversationId,
      role,
      text,
      assetUrl: options?.assetUrl ?? null,
      assetKind: options?.assetKind ?? null,
      displayJson: options?.display ? JSON.stringify(options.display) : null
    }
  );

  const [message] = await queryRows<MessageRow>(
    `SELECT id, conversation_id, role, text, asset_url, asset_kind, display_json, created_at
     FROM messages
     WHERE id = :id`,
    { id: Number(result.insertId) }
  );

  return message;
}

export function buildAssistantMessageOptions(flaskResult: FlaskResult) {
  const generatedImageUrl = extractGeneratedImageUrl(flaskResult);
  const generatedAudioUrl = extractGeneratedAudioUrl(flaskResult);
  const mediaDisplay = buildMediaDisplay(flaskResult, generatedAudioUrl);

  return {
    text: cleanAssistantText(flaskResult.message),
    assetUrl: generatedImageUrl,
    assetKind: generatedImageUrl ? "image" : null,
    display: mediaDisplay ?? normalizeDisplay(flaskResult.display)
  };
}

export function enrichMessageAsset(message: MessageRow) {
  const display = parseDisplayJson(message.display_json);

  if (message.asset_url || message.role !== "assistant") {
    return {
      ...message,
      display
    };
  }

  const fallbackAssetUrl = extractAssetUrlFromText(message.text);
  if (!fallbackAssetUrl) {
    return {
      ...message,
      display
    };
  }

  return {
    ...message,
    asset_url: fallbackAssetUrl,
    asset_kind: "image",
    display
  };
}

export async function maybeUpdateConversationTitle(
  conversationId: number,
  userId: number,
  text: string
) {
  const title = text.replace(/\s+/g, " ").slice(0, 80);
  await getPool().execute(
    `UPDATE conversations
     SET title = CASE
       WHEN title = 'Nouvelle discussion' THEN :title
       ELSE title
     END,
     updated_at = CURRENT_TIMESTAMP
     WHERE id = :conversationId AND user_id = :userId`,
    { title, conversationId, userId }
  );
}

export function cleanAssistantText(value: unknown) {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }

  return "La demande a ete traitee, mais aucune reponse lisible n'a ete retournee.";
}

export function normalizeDisplay(value: unknown): DisplayPayload | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const display = value as DisplayPayload;
  if (display.type === "media") {
    if (
      typeof display.audio_url === "string" && display.audio_url.trim()
      || typeof display.image_url === "string" && display.image_url.trim()
      || typeof display.audio_generation_status === "string" && display.audio_generation_status.trim()
      || typeof display.audio_error === "string" && display.audio_error.trim()
      || typeof display.music_prompt === "string" && display.music_prompt.trim()
    ) {
      return display;
    }
    return null;
  }

  if (display.type !== "table") {
    return null;
  }
  if (!Array.isArray(display.columns) || !Array.isArray(display.rows)) {
    return null;
  }

  return display;
}

function buildMediaDisplay(
  flaskResult: FlaskResult,
  audioUrl: string | null
): DisplayPayload | null {
  const data = flaskResult.data as Record<string, unknown> | undefined;
  const audioStatus =
    typeof data?.audio_generation_status === "string"
      ? data.audio_generation_status
      : null;
  const musicPrompt =
    typeof data?.music_prompt === "string"
      ? data.music_prompt
      : null;
  const audioError =
    typeof data?.audio_error === "string"
      ? data.audio_error
      : null;

  if (!audioUrl && !audioStatus && !audioError && !musicPrompt) {
    return null;
  }

  return {
    type: "media",
    audio_url: audioUrl,
    audio_generation_status: audioStatus,
    audio_error: audioError,
    music_prompt: musicPrompt
  };
}

function extractAssetUrlFromText(text: string) {
  const pathMatch = text.match(/[A-Za-z]:\\[^\n]+?\.(png|jpg|jpeg|webp)/i);
  if (!pathMatch) {
    return null;
  }

  return `/api/media/generated-image?path=${encodeURIComponent(pathMatch[0].trim())}`;
}

function parseDisplayJson(value: unknown): DisplayPayload | null {
  if (!value) {
    return null;
  }

  if (typeof value === "object") {
    return normalizeDisplay(value);
  }

  if (typeof value !== "string") {
    return null;
  }

  try {
    return normalizeDisplay(JSON.parse(value));
  } catch {
    return null;
  }
}
