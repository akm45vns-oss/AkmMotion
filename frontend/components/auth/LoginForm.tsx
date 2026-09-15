"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api/auth";
import { useUserStore } from "@/lib/stores/userStore";
import Logo from "@/components/shared/Logo";

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
    <div className="w-full max-w-md p-6 sm:p-8 rounded-xl bg-[#151616] border border-[#292A29] shadow-2xl shadow-black/60">
      <div className="text-center mb-6">
        <div className="flex justify-center mb-3">
          <Logo variant="icon" size="xl" />
        </div>
        <h2 className="text-xl sm:text-2xl font-semibold text-[#F5F1E8] tracking-tight font-display">Welcome back</h2>
        <p className="text-xs sm:text-sm text-[#A9A49B] mt-1">Sign in to your AkmMotion studio account</p>
      </div>

      {error && (
        <div className="mb-5 p-3 rounded-lg bg-[#C95C5C]/10 border border-[#C95C5C]/25 text-[#C95C5C] text-xs">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-[#A9A49B] uppercase tracking-wider mb-1.5 font-mono">
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
            <label className="block text-xs font-medium text-[#A9A49B] uppercase tracking-wider font-mono">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs text-[#E76536] hover:text-[#F07847] transition-colors"
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
          className="btn-primary w-full min-h-[44px] py-3 px-4 rounded-md text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm touch-target"
        >
          {loading ? (
            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            "Sign In"
          )}
        </button>
      </form>

      <div className="mt-6 text-center text-xs text-[#77746E]">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="text-[#E76536] hover:text-[#F07847] font-medium transition-colors">
          Create account
        </Link>
      </div>
    </div>
  );
}
