"use client";

import Image from "next/image";
import Link from "next/link";

interface LogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  variant?: "full" | "icon" | "full-image";
  showSubtitle?: boolean;
  href?: string;
  className?: string;
}

export default function Logo({
  size = "md",
  variant = "full",
  showSubtitle = false,
  href,
  className = "",
}: LogoProps) {
  const iconDimensions = {
    sm: { w: 22, h: 22, text: "text-sm", subText: "text-[9px]" },
    md: { w: 28, h: 28, text: "text-base", subText: "text-[10px]" },
    lg: { w: 38, h: 38, text: "text-xl", subText: "text-xs" },
    xl: { w: 52, h: 52, text: "text-2xl", subText: "text-xs" },
  }[size];

  const content = (
    <div className={`flex items-center gap-2.5 select-none ${className}`}>
      {variant === "full-image" ? (
        <div className="relative h-8 sm:h-9 w-auto">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo-dark.png"
            alt="AkmMotion"
            className="h-full w-auto object-contain"
          />
        </div>
      ) : (
        <>
          {/* 3D Brand Icon Mark */}
          <div className="flex-shrink-0 relative flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/logo-icon.png"
              alt="AkmMotion Logo"
              width={iconDimensions.w}
              height={iconDimensions.h}
              className="object-contain drop-shadow-[0_2px_8px_rgba(0,180,216,0.3)] transition-transform hover:scale-105"
            />
          </div>

          {variant === "full" && (
            <div className="flex flex-col leading-tight">
              <span className={`font-bold tracking-tight text-[#F5F1E8] font-display ${iconDimensions.text}`}>
                <span className="bg-gradient-to-r from-[#00C2E8] via-[#0091FF] to-[#9933FF] bg-clip-text text-transparent font-extrabold">
                  Akm
                </span>
                <span>Motion</span>
              </span>
              {showSubtitle && (
                <span className={`tracking-widest uppercase text-[#A9A49B] font-mono ${iconDimensions.subText}`}>
                  Video Generation Platform
                </span>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="inline-flex items-center group">
        {content}
      </Link>
    );
  }

  return content;
}
