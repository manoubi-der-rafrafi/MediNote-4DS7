import { NextResponse } from "next/server";
import type { ResultSetHeader } from "mysql2/promise";
import { getPool } from "@/lib/db";
import { jsonError, toPublicError } from "@/lib/api";
import { assertConversationAccess, getCurrentUser } from "@/lib/session";

export async function PATCH(
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
    const body = (await request.json().catch(() => ({}))) as { title?: string };
    const title = typeof body.title === "string" ? body.title.trim().slice(0, 120) : "";
    if (!title) {
      return jsonError("Titre invalide.", 400);
    }

    await getPool().execute(
      `UPDATE conversations
       SET title = :title, updated_at = CURRENT_TIMESTAMP
       WHERE id = :conversationId AND user_id = :userId`,
      { title, conversationId, userId: user.id }
    );

    return NextResponse.json({ conversation: { id: conversationId, title } });
  } catch (error) {
    return toPublicError(error);
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getCurrentUser();
    const conversationId = Number(params.id);
    if (!Number.isInteger(conversationId)) {
      return jsonError("Conversation invalide.", 400);
    }

    const [result] = await getPool().execute<ResultSetHeader>(
      "DELETE FROM conversations WHERE id = :conversationId AND user_id = :userId",
      { conversationId, userId: user.id }
    );

    if (result.affectedRows === 0) {
      return jsonError("Conversation introuvable ou non autorisee.", 404);
    }

    return NextResponse.json({ deleted: true });
  } catch (error) {
    return toPublicError(error);
  }
}
