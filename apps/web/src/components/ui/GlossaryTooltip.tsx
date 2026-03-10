"use client";

import { useState, useRef } from "react";

interface GlossaryTooltipProps {
  term: string;
  definition: string;
  children: React.ReactNode;
}

export default function GlossaryTooltip({ term, definition, children }: GlossaryTooltipProps) {
  const [show, setShow] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const handleEnter = () => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setShow(true), 300);
  };

  const handleLeave = () => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setShow(false), 200);
  };

  return (
    <span
      className="relative inline"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      onFocus={handleEnter}
      onBlur={handleLeave}
    >
      <span className="border-b border-dashed border-slate-400 cursor-help" tabIndex={0} aria-describedby={`glossary-${term}`}>
        {children}
      </span>
      {show && (
        <span
          id={`glossary-${term}`}
          role="tooltip"
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 max-w-xs p-3 rounded-lg bg-slate-800 text-white text-xs shadow-lg pointer-events-none"
        >
          <span className="font-semibold text-blue-300 block mb-1">{term}</span>
          <span className="text-slate-200 leading-relaxed">{definition}</span>
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
        </span>
      )}
    </span>
  );
}
