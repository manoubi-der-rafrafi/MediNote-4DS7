import { NextResponse } from "next/server";

export function jsonError(message: string, status = 400) {
  return NextResponse.json({ error: message }, { status });
}

export function toPublicError(error: unknown) {
  if (error instanceof Error && error.message === "CONVERSATION_NOT_FOUND") {
    return jsonError("Conversation introuvable ou non autorisee.", 404);
  }

  if (error instanceof Error) {
    return jsonError(
      process.env.NODE_ENV === "production" ? "Erreur serveur." : error.message,
      500
    );
  }

  return jsonError("Erreur serveur.", 500);
}
