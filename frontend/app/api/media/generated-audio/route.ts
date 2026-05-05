import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const path = searchParams.get("path");

  if (!path) {
    return new NextResponse("Missing path.", { status: 400 });
  }

  const baseUrl = process.env.FLASK_API_URL || "http://127.0.0.1:5000";
  const target = new URL("/media/generated-audio", baseUrl.replace(/\/$/, ""));
  target.searchParams.set("path", path);

  const response = await fetch(target.toString(), { cache: "no-store" });
  if (!response.ok) {
    return new NextResponse("Audio unavailable.", { status: response.status });
  }

  return new NextResponse(response.body, {
    status: 200,
    headers: {
      "Content-Type": response.headers.get("Content-Type") || "audio/wav",
      "Cache-Control": "no-store"
    }
  });
}
