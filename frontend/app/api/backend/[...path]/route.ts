import { NextRequest, NextResponse } from "next/server";

// Tell Vercel to allow up to 60 seconds for this route (needed for Render cold starts)
export const maxDuration = 60;
export const dynamic = "force-dynamic";

// Priority: env var → hardcoded Render URL
const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL ||
  "https://akmmotion-backend.onrender.com";

async function proxyRequest(
  req: NextRequest,
  context: { params: { path: string[] } }
) {
  const path = (context.params.path || []).join("/");
  const search = req.nextUrl.search || "";
  const targetUrl = `${BACKEND_URL}/api/v1/${path}${search}`;

  let body: BodyInit | undefined = undefined;
  if (!["GET", "HEAD"].includes(req.method)) {
    body = await req.text();
  }

  const headers: Record<string, string> = {
    "Content-Type": req.headers.get("content-type") || "application/json",
    Accept: req.headers.get("accept") || "application/json",
  };
  const auth = req.headers.get("authorization");
  if (auth) headers["Authorization"] = auth;

  // Retry once if we get a network error (handles Render cold start)
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      console.log(`[Proxy] Attempt ${attempt}: ${req.method} ${targetUrl}`);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 55000);

      const backendRes = await fetch(targetUrl, {
        method: req.method,
        headers,
        body,
        signal: controller.signal,
      });
      clearTimeout(timeout);

      const responseBody = await backendRes.arrayBuffer();
      console.log(`[Proxy] Success: ${backendRes.status}`);
      return new NextResponse(responseBody, {
        status: backendRes.status,
        headers: {
          "Content-Type":
            backendRes.headers.get("content-type") || "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } catch (error: any) {
      console.error(`[Proxy] Attempt ${attempt} failed:`, error.message);
      if (attempt === 2) {
        return NextResponse.json(
          {
            detail:
              "Backend is waking up (cold start). Please wait 30 seconds and try again.",
          },
          { status: 503 }
        );
      }
      // Wait 2 seconds before retry
      await new Promise((r) => setTimeout(r, 2000));
    }
  }

  // Unreachable but TypeScript needs it
  return NextResponse.json({ detail: "Unexpected error" }, { status: 500 });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}