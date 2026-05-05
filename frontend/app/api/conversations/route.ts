import { NextResponse } from "next/server";
import type { ResultSetHeader, RowDataPacket } from "mysql2/promise";
import { getPool, queryOne, queryRows } from "@/lib/db";
import { jsonError, toPublicError } from "@/lib/api";
import { getCurrentUser } from "@/lib/session";

type ConversationRow = RowDataPacket & {
  id: number;
  title: string;
  message_count: number;
  created_at: Date;
  updated_at: Date;
};

export async function GET() {
  try {
    const user = await getCurrentUser();
    const conversations = await queryRows<ConversationRow>(
      `SELECT conversations.id, conversations.title, conversations.created_at, conversations.updated_at,
              COUNT(messages.id) AS message_count
       FROM conversations
       LEFT JOIN messages ON messages.conversation_id = conversations.id
       WHERE user_id = :userId
       GROUP BY conversations.id, conversations.title, conversations.created_at, conversations.updated_at
       ORDER BY conversations.updated_at DESC, conversations.id DESC`,
      { userId: user.id }
    );

    return NextResponse.json({ conversations });
  } catch (error) {
    return toPublicError(error);
  }
}

export async function POST(request: Request) {
  try {
    const user = await getCurrentUser();
    const body = (await request.json().catch(() => ({}))) as { title?: string };
    const title = cleanTitle(body.title);
    const existingEmpty = await queryOne<ConversationRow>(
      `SELECT conversations.id, conversations.title, conversations.created_at, conversations.updated_at,
              COUNT(messages.id) AS message_count
       FROM conversations
       LEFT JOIN messages ON messages.conversation_id = conversations.id
       WHERE conversations.user_id = :userId
       GROUP BY conversations.id, conversations.title, conversations.created_at, conversations.updated_at
       HAVING COUNT(messages.id) = 0
       ORDER BY conversations.updated_at DESC, conversations.id DESC
       LIMIT 1`,
      { userId: user.id }
    );

    if (existingEmpty) {
      return NextResponse.json({
        conversation: existingEmpty,
        reusedExisting: true
      });
    }

    const [result] = await getPool().execute<ResultSetHeader>(
      `INSERT INTO conversations (user_id, title)
       VALUES (:userId, :title)`,
      { userId: user.id, title }
    );

    return NextResponse.json(
      {
        conversation: {
          id: Number(result.insertId),
          title,
          message_count: 0
        }
      },
      { status: 201 }
    );
  } catch (error) {
    return toPublicError(error);
  }
}

function cleanTitle(value: unknown) {
  if (typeof value !== "string") {
    return "Nouvelle discussion";
  }

  const cleaned = value.trim().slice(0, 120);
  return cleaned || "Nouvelle discussion";
}
