import { NextRequest, NextResponse } from "next/server";

// Priority:
// 1. BACKEND_INTERNAL_URL env var (set in Vercel dashboard)
// 2. Hardcoded Render URL as production fallback
// 3. localhost for local dev
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

  try {
    console.log(`[Proxy] ${req.method} ${targetUrl}`);
    const backendRes = await fetch(targetUrl, {
      method: req.method,
      headers,
      body,
      // Give Render cold-start up to 60 seconds
      signal: AbortSignal.timeout(60000),
    });
    const responseBody = await backendRes.arrayBuffer();
    console.log(`[Proxy] Response: ${backendRes.status}`);
    return new NextResponse(responseBody, {
      status: backendRes.status,
      headers: {
        "Content-Type":
          backendRes.headers.get("content-type") || "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (error: any) {
    console.error("[API Proxy] Backend unreachable:", error.message);
    return NextResponse.json(
      { detail: "Backend is waking up (cold start). Please wait 30 seconds and try again." },
      { status: 503 }
    );
  }
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