"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api/auth";
import { useUserStore } from "@/lib/stores/userStore";
import Logo from "@/components/shared/Logo";

export default function RegisterForm() {
  const router = useRouter();
  const setAuth = useUserStore((state) => state.setAuth);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);

    try {
      const data = await authApi.register(email, password, fullName);
      setAuth(data.user, data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Could not complete registration. Please try again.");
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
        <h2 className="text-xl sm:text-2xl font-semibold text-[#F5F1E8] tracking-tight font-display">Create your account</h2>
        <p className="text-xs sm:text-sm text-[#A9A49B] mt-1">Start creating AI videos with character consistency</p>
      </div>

      {error && (
        <div className="mb-5 p-3 rounded-lg bg-[#C95C5C]/10 border border-[#C95C5C]/25 text-[#C95C5C] text-xs">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-[#A9A49B] uppercase tracking-wider mb-1.5 font-mono">
            Full Name
          </label>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Alex Smith"
            className="input-base min-h-[44px]"
          />
        </div>

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
          <label className="block text-xs font-medium text-[#A9A49B] uppercase tracking-wider mb-1.5 font-mono">
            Password
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimum 6 characters"
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
            "Start Free Studio Account"
          )}
        </button>
      </form>

      <div className="mt-6 text-center text-xs text-[#77746E]">
        Already have an account?{" "}
        <Link href="/login" className="text-[#E76536] hover:text-[#F07847] font-medium transition-colors">
          Sign In
        </Link>
      </div>
    </div>
  );
}
