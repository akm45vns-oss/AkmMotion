"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api/auth";
import { useUserStore } from "@/lib/stores/userStore";

export default function LoginForm() {
  const router = useRouter();
  const setAuth = useUserStore((state) => state.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await authApi.login(email, password);
      setAuth(data.user, data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid email or password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md p-6 sm:p-8 rounded-2xl bg-[#141517] border border-[#24272E] shadow-2xl shadow-black/40">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-[#E0693B]/10 border border-[#E0693B]/25 text-[#E0693B] font-bold text-lg mb-3">
          A
        </div>
        <h2 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">Welcome back</h2>
        <p className="text-xs sm:text-sm text-[#9DA4B2] mt-1">Sign in to your AkmMotion studio account</p>
      </div>

      {error && (
        <div className="mb-5 p-3 rounded-lg bg-[#E55353]/10 border border-[#E55353]/25 text-[#E55353] text-xs">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-[#9DA4B2] uppercase tracking-wider mb-1.5">
            Email Address
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="input-base min-h-[44px]"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-xs font-medium text-[#9DA4B2] uppercase tracking-wider">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs text-[#E0693B] hover:text-[#EB794D] transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="input-base min-h-[44px]"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full min-h-[44px] py-3 px-4 rounded-xl bg-[#E0693B] hover:bg-[#EB794D] text-white font-medium text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
        >
          {loading ? (
            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            "Sign In"
          )}
        </button>
      </form>

      <div className="mt-6 text-center text-xs text-[#687082]">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="text-[#E0693B] hover:text-[#EB794D] font-medium transition-colors">
          Create account
        </Link>
      </div>
    </div>
  );
}
