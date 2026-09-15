"use client";

import { useState } from "react";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="w-full max-w-md p-6 sm:p-8 rounded-xl bg-[#151616] border border-[#292A29] shadow-2xl shadow-black/60">
      <div className="text-center mb-6">
        <h2 className="text-xl sm:text-2xl font-semibold text-[#F5F1E8] tracking-tight font-display">Reset your password</h2>
        <p className="text-xs sm:text-sm text-[#A9A49B] mt-1">
          Enter your email address and we&apos;ll send you instructions to reset your password.
        </p>
      </div>

      {submitted ? (
        <div className="p-4 rounded-lg bg-[#4FAE7B]/10 border border-[#4FAE7B]/25 text-[#4FAE7B] text-xs text-center">
          If an account exists for <span className="font-semibold">{email}</span>, you will receive password reset instructions shortly.
        </div>
      ) : (
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

          <button
            type="submit"
            className="btn-primary w-full min-h-[44px] py-3 px-4 rounded-md text-sm font-medium flex items-center justify-center gap-2 shadow-sm touch-target"
          >
            Send Reset Link
          </button>
        </form>
      )}

      <div className="mt-6 text-center text-xs text-[#77746E]">
        Remember your password?{" "}
        <Link href="/login" className="text-[#E76536] hover:text-[#F07847] font-medium transition-colors">
          Back to Sign In
        </Link>
      </div>
    </div>
  );
}
