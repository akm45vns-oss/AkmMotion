"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api/auth";
import { useUserStore } from "@/lib/stores/userStore";

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
    <div className="w-full max-w-md p-6 sm:p-8 rounded-2xl bg-[#141517] border border-[#24272E] shadow-2xl shadow-black/40">
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-[#E0693B]/10 border border-[#E0693B]/25 text-[#E0693B] font-bold text-lg mb-3">
          A
        </div>
        <h2 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">Create your account</h2>
        <p className="text-xs sm:text-sm text-[#9DA4B2] mt-1">Start creating AI videos with character consistency</p>
      </div>

      {error && (
        <div className="mb-5 p-3 rounded-lg bg-[#E55353]/10 border border-[#E55353]/25 text-[#E55353] text-xs">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-[#9DA4B2] uppercase tracking-wider mb-1.5">
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
          <label className="block text-xs font-medium text-[#9DA4B2] uppercase tracking-wider mb-1.5">
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
          className="w-full min-h-[44px] py-3 px-4 rounded-xl bg-[#E0693B] hover:bg-[#EB794D] text-white font-medium text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
        >
          {loading ? (
            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            "Start Free Studio Account"
          )}
        </button>
      </form>

      <div className="mt-6 text-center text-xs text-[#687082]">
        Already have an account?{" "}
        <Link href="/login" className="text-[#E0693B] hover:text-[#EB794D] font-medium transition-colors">
          Sign In
        </Link>
      </div>
    </div>
  );
}
