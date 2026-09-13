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
    <div className="w-full max-w-md p-8 rounded-2xl bg-[#0D1322] border border-gray-800/80 shadow-2xl shadow-indigo-950/20">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-white">Reset your password</h2>
        <p className="text-sm text-gray-400 mt-1">
          Enter your email address and we&apos;ll send you instructions to reset your password.
        </p>
      </div>

      {submitted ? (
        <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm text-center">
          If an account exists for <span className="font-semibold">{email}</span>, you will receive password reset instructions shortly.
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-3 rounded-xl bg-[#090D16] border border-gray-800 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-sm"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all"
          >
            Send Reset Link
          </button>
        </form>
      )}

      <div className="mt-8 text-center text-xs text-gray-400">
        Remember your password?{" "}
        <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold">
          Back to Sign In
        </Link>
      </div>
    </div>
  );
}
