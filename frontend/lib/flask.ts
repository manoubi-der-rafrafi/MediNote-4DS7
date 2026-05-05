export type DisplayTableColumn = {
  key: string;
  label: string;
};

export type DisplayTableRow = Record<string, string>;

export type DisplayPayload = {
  type?: "table" | "text" | "list" | "badge" | "media";
  title?: string;
  columns?: DisplayTableColumn[];
  rows?: DisplayTableRow[];
  truncated?: boolean;
  row_count?: number;
  image_url?: string | null;
  audio_url?: string | null;
  audio_generation_status?: string | null;
  audio_error?: string | null;
  music_prompt?: string | null;
  [key: string]: unknown;
};

export type FlaskResult = {
  status?: string;
  intent?: string;
  action?: string;
  message?: string;
  display?: DisplayPayload | null;
  data?: unknown;
  task?: unknown;
  missing_fields?: string[];
  choices?: string[];
  [key: string]: unknown;
};

export type FlaskVoiceResult = {
  transcription?: string;
  result?: FlaskResult;
  audio_response?: {
    available?: boolean;
    mime_type?: string;
    encoding?: string;
    content?: string;
    [key: string]: unknown;
  };
  error?: string;
  source?: string;
  details?: unknown;
  [key: string]: unknown;
};

export function extractGeneratedImageUrl(result: FlaskResult) {
  const imagePath = getNestedString(result, ["data", "saved_files", "image_file"]);
  if (!imagePath) {
    return null;
  }

  return `/api/media/generated-image?path=${encodeURIComponent(imagePath)}`;
}

export function extractGeneratedAudioUrl(result: FlaskResult) {
  const audioPath = getNestedString(result, ["data", "saved_files", "audio_file"])
    || getNestedString(result, ["data", "audio_path"]);
  if (audioPath) {
    return `/api/media/generated-audio?path=${encodeURIComponent(audioPath)}`;
  }

  return getNestedString(result, ["data", "audio_url"]);
}

export async function callFlaskOrchestrator(input: {
  userId: number;
  conversationId: number;
  demande: string;
}) {
  const baseUrl = process.env.FLASK_API_URL || "http://127.0.0.1:5000";

  try {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/orchestrate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        id_user: input.userId,
        id_conversation: input.conversationId,
        demande: input.demande
      })
    });

    const payload = (await response.json().catch(() => ({}))) as FlaskResult;

    if (!response.ok) {
      return {
        status: "flask_error",
        message: extractFlaskErrorMessage(payload, "Le backend Flask a refuse la demande."),
        details: payload
      } satisfies FlaskResult;
    }

    return payload;
  } catch (error) {
    return {
      status: "flask_unavailable",
      message: "Le backend Flask n'est pas disponible.",
      details: error instanceof Error ? error.message : String(error)
    } satisfies FlaskResult;
  }
}

export async function callFlaskVoiceOrchestrator(input: {
  userId: number;
  conversationId: number;
  voice: File;
}) {
  const baseUrl = process.env.FLASK_API_URL || "http://127.0.0.1:5000";
  const formData = new FormData();

  formData.append("voice", input.voice, input.voice.name || "voice.webm");
  formData.append("id_user", String(input.userId));
  formData.append("id_conversation", String(input.conversationId));

  try {
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/orchestrate-voice`, {
      method: "POST",
      body: formData
    });

    const payload = (await response.json().catch(() => ({}))) as FlaskVoiceResult;

    if (!response.ok) {
      return {
        transcription: "",
        result: {
          status: "flask_error",
          message: extractFlaskErrorMessage(
            payload,
            "Le backend Flask a refuse la demande vocale."
          ),
          details: payload
        }
      } satisfies FlaskVoiceResult;
    }

    return payload;
  } catch (error) {
    return {
      transcription: "",
      result: {
        status: "flask_unavailable",
        message: "Le backend Flask n'est pas disponible.",
        details: error instanceof Error ? error.message : String(error)
      }
    } satisfies FlaskVoiceResult;
  }
}

function getNestedString(
  value: unknown,
  path: string[]
): string | null {
  let current: unknown = value;

  for (const key of path) {
    if (!current || typeof current !== "object" || !(key in current)) {
      return null;
    }
    current = (current as Record<string, unknown>)[key];
  }

  return typeof current === "string" && current.trim() ? current.trim() : null;
}

function extractFlaskErrorMessage(
  payload: Record<string, unknown>,
  fallback: string
) {
  const message = typeof payload.message === "string" ? payload.message.trim() : "";
  if (message) {
    return message;
  }

  const error = typeof payload.error === "string" ? payload.error.trim() : "";
  const details = typeof payload.details === "string" ? payload.details.trim() : "";
  const source = typeof payload.source === "string" ? payload.source.trim() : "";

  if (source === "processing" && details) {
    return details;
  }

  if (error) {
    return error;
  }

  if (details) {
    return details;
  }

  return fallback;
}
