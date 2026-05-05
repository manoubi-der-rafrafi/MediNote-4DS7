import { cookies, headers } from "next/headers";
import { randomBytes } from "crypto";
import type { ResultSetHeader, RowDataPacket } from "mysql2/promise";
import { ensureConversationSchema, getPool, queryOne } from "./db";

const DEFAULT_COOKIE_NAME = "vital_browser_session";

export type CurrentUser = {
  id: number;
  role: string;
};

type SessionRow = RowDataPacket & {
  user_id: number;
  role: string;
};

type ConversationOwnerRow = RowDataPacket & {
  id: number;
};

export async function getCurrentUser(): Promise<CurrentUser> {
  await ensureConversationSchema();
  const cookieStore = cookies();
  const cookieName = getSessionCookieName();
  const existingToken = cookieStore.get(cookieName)?.value;

  if (existingToken) {
    const session = await queryOne<SessionRow>(
      `SELECT browser_sessions.user_id, users.role
       FROM browser_sessions
       JOIN users ON users.id = browser_sessions.user_id
       WHERE browser_sessions.session_token = :token
       LIMIT 1`,
      { token: existingToken }
    );

    if (session) {
      await getPool().execute(
        "UPDATE browser_sessions SET last_seen_at = CURRENT_TIMESTAMP WHERE session_token = :token",
        { token: existingToken }
      );
      return { id: Number(session.user_id), role: session.role };
    }
  }

  const token = randomBytes(32).toString("hex");
  const userAgent = headers().get("user-agent") || null;
  const pool = getPool();
  const [userResult] = await pool.execute<ResultSetHeader>(
    "INSERT INTO users (role) VALUES ('user')"
  );

  const userId = Number(userResult.insertId);
  await pool.execute(
    `INSERT INTO browser_sessions (user_id, session_token, user_agent)
     VALUES (:userId, :token, :userAgent)`,
    { userId, token, userAgent }
  );

  cookieStore.set(cookieName, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 365
  });

  return { id: userId, role: "user" };
}

export async function assertConversationAccess(
  conversationId: number,
  userId: number
) {
  const conversation = await queryOne<ConversationOwnerRow>(
    "SELECT id FROM conversations WHERE id = :conversationId AND user_id = :userId LIMIT 1",
    { conversationId, userId }
  );

  if (!conversation) {
    throw new Error("CONVERSATION_NOT_FOUND");
  }
}

function getSessionCookieName() {
  return process.env.SESSION_COOKIE_NAME || DEFAULT_COOKIE_NAME;
}
