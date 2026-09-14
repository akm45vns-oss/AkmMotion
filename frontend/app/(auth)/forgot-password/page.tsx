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
    <div className="w-full max-w-md p-6 sm:p-8 rounded-2xl bg-[#141517] border border-[#24272E] shadow-2xl shadow-black/40">
      <div className="text-center mb-6">
        <h2 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">Reset your password</h2>
        <p className="text-xs sm:text-sm text-[#9DA4B2] mt-1">
          Enter your email address and we&apos;ll send you instructions to reset your password.
        </p>
      </div>

      {submitted ? (
        <div className="p-4 rounded-xl bg-[#2EB88A]/10 border border-[#2EB88A]/25 text-[#2EB88A] text-xs text-center">
          If an account exists for <span className="font-semibold">{email}</span>, you will receive password reset instructions shortly.
        </div>
      ) : (
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

          <button
            type="submit"
            className="w-full min-h-[44px] py-3 px-4 rounded-xl bg-[#E0693B] hover:bg-[#EB794D] text-white font-medium text-sm transition-colors shadow-sm"
          >
            Send Reset Link
          </button>
        </form>
      )}

      <div className="mt-6 text-center text-xs text-[#687082]">
        Remember your password?{" "}
        <Link href="/login" className="text-[#E0693B] hover:text-[#EB794D] font-medium transition-colors">
          Back to Sign In
        </Link>
      </div>
    </div>
  );
}
