import React from "react";

export default function Logo({
  className = "",
  size = 32,
}: {
  className?: string;
  size?: number;
}) {
  return (
    <span
      className={`relative inline-flex items-center justify-center rounded-[10px] bg-zinc-900 dark:bg-white ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg
        width={size * 0.62}
        height={size * 0.62}
        viewBox="0 0 24 24"
        fill="none"
        className="text-white dark:text-zinc-900"
      >
        {/* back sheet */}
        <rect
          x="6.5"
          y="4"
          width="11"
          height="14"
          rx="2.4"
          stroke="currentColor"
          strokeWidth="1.7"
          opacity="0.45"
        />
        {/* front sheet */}
        <rect
          x="4"
          y="6.5"
          width="11"
          height="14"
          rx="2.4"
          fill="currentColor"
        />
        {/* accent query line */}
        <path
          d="M6.7 11.5h5.6M6.7 14.3h3.4"
          stroke="var(--accent)"
          strokeWidth="1.7"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
