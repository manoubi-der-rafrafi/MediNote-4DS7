import { NextResponse } from "next/server";
import { jsonError, toPublicError } from "@/lib/api";
import { getPool } from "@/lib/db";
import { callFlaskVoiceOrchestrator } from "@/lib/flask";
import {
  buildAssistantMessageOptions,
  enrichMessageAsset,
  insertMessage,
  maybeUpdateConversationTitle
} from "@/lib/message-store";
import { assertConversationAccess, getCurrentUser } from "@/lib/session";

const ACCEPTED_AUDIO_TYPES = new Set(["mp3", "wav", "m4a", "webm", "ogg"]);
const MAX_AUDIO_SIZE = 25 * 1024 * 1024;

export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getCurrentUser();
    const conversationId = Number(params.id);
    if (!Number.isInteger(conversationId)) {
      return jsonError("Conversation invalide.", 400);
    }

    await assertConversationAccess(conversationId, user.id);

    const formData = await request.formData();
    const voice = formData.get("voice") ?? formData.get("audio") ?? formData.get("file");
    if (!(voice instanceof File)) {
      return jsonError("Le fichier vocal 'voice' est obligatoire.", 400);
    }

    if (voice.size > MAX_AUDIO_SIZE) {
      return jsonError("Le fichier vocal ne doit pas depasser 25 MB.", 400);
    }

    const extension = getFileExtension(voice);
    if (!ACCEPTED_AUDIO_TYPES.has(extension)) {
      return jsonError("Format audio non supporte. Utilisez wav, mp3, m4a, webm ou ogg.", 400);
    }

    const voicePayload = await callFlaskVoiceOrchestrator({
      userId: user.id,
      conversationId,
      voice
    });
    const transcription = typeof voicePayload.transcription === "string"
      ? voicePayload.transcription.trim()
      : "";
    const flaskResult = voicePayload.result;

    if (!transcription) {
      const message = typeof flaskResult?.message === "string"
        ? flaskResult.message
        : "La transcription du fichier vocal a echoue.";
      return jsonError(message, 502);
    }

    const userMessage = await insertMessage(conversationId, "user", transcription);
    await maybeUpdateConversationTitle(conversationId, user.id, transcription);

    const assistant = buildAssistantMessageOptions(flaskResult ?? {});
    const assistantMessage = await insertMessage(conversationId, "assistant", assistant.text, {
      assetUrl: assistant.assetUrl,
      assetKind: assistant.assetKind,
      display: assistant.display
    });

    await getPool().execute(
      "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = :conversationId",
      { conversationId }
    );

    return NextResponse.json({
      transcription,
      messages: [userMessage, assistantMessage].map(enrichMessageAsset),
      result: flaskResult,
      audio_response: voicePayload.audio_response ?? null
    });
  } catch (error) {
    return toPublicError(error);
  }
}

function getFileExtension(file: File) {
  const nameExtension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (nameExtension) {
    return nameExtension;
  }

  const mimeExtension = file.type.split("/").pop()?.toLowerCase() ?? "";
  return mimeExtension.replace(/^x-/, "");
}
