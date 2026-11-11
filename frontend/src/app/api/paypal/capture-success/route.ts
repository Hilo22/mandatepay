import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const token = searchParams.get("token");

  if (token) {
    try {
      await fetch(
        `${API_BASE_URL}/api/mandates/order/${encodeURIComponent(token)}/capture`,
        {
          method: "POST",
        }
      );
    } catch {
      // Fallback handled on dashboard
    }
  }

  return NextResponse.redirect(new URL("/", request.url));
}

