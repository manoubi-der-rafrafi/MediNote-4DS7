import { NextResponse } from "next/server";
import { jsonError, toPublicError } from "@/lib/api";
import { getPool, queryRows } from "@/lib/db";
import { callFlaskOrchestrator } from "@/lib/flask";
import {
  buildAssistantMessageOptions,
  enrichMessageAsset,
  insertMessage,
  maybeUpdateConversationTitle,
  type MessageRow
} from "@/lib/message-store";
import { assertConversationAccess, getCurrentUser } from "@/lib/session";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getCurrentUser();
    const conversationId = Number(params.id);
    if (!Number.isInteger(conversationId)) {
      return jsonError("Conversation invalide.", 400);
    }

    await assertConversationAccess(conversationId, user.id);
    const messages = await queryRows<MessageRow>(
      `SELECT id, conversation_id, role, text, asset_url, asset_kind, display_json, created_at
       FROM messages
       WHERE conversation_id = :conversationId
       ORDER BY created_at ASC, id ASC`,
      { conversationId }
    );

    return NextResponse.json({ messages: messages.map(enrichMessageAsset) });
  } catch (error) {
    return toPublicError(error);
  }
}

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
    const body = (await request.json().catch(() => ({}))) as { text?: string };
    const text = typeof body.text === "string" ? body.text.trim() : "";
    if (!text) {
      return jsonError("Message vide.", 400);
    }

    const userMessage = await insertMessage(conversationId, "user", text);
    await maybeUpdateConversationTitle(conversationId, user.id, text);

    const flaskResult = await callFlaskOrchestrator({
      userId: user.id,
      conversationId,
      demande: text
    });
    const assistant = buildAssistantMessageOptions(flaskResult);
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
      messages: [userMessage, assistantMessage].map(enrichMessageAsset),
      result: flaskResult
    });
  } catch (error) {
    return toPublicError(error);
  }
}
