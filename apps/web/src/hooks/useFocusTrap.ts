"use client";

import { useEffect, useRef, useCallback } from "react";

/**
 * Hook for WCAG 2.4.3 focus trap in modals / dialogs.
 *
 * Traps Tab / Shift+Tab inside the referenced container while active.
 * Restores focus to the previously focused element on close.
 * Also closes the modal on Escape key press.
 *
 * @param active - Whether the focus trap is active
 * @param onClose - Optional callback to close the modal on Escape
 * @returns ref to attach to the modal container div
 *
 * Usage:
 *   const trapRef = useFocusTrap(isOpen, () => setIsOpen(false));
 *   return isOpen ? <div ref={trapRef}>...</div> : null;
 */
export function useFocusTrap<T extends HTMLElement = HTMLDivElement>(
  active: boolean,
  onClose?: () => void,
) {
  const containerRef = useRef<T>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Save focus on open, restore on close
  useEffect(() => {
    if (active) {
      previousFocusRef.current = document.activeElement as HTMLElement;

      // Wait for DOM to render, then focus the first focusable element
      const timer = setTimeout(() => {
        const container = containerRef.current;
        if (!container) return;

        const focusable = getFocusableElements(container);
        if (focusable.length > 0) {
          focusable[0].focus();
        } else {
          // If no focusable child, focus the container itself
          container.setAttribute("tabindex", "-1");
          container.focus();
        }
      }, 50);

      return () => clearTimeout(timer);
    } else {
      // Restore focus when trap deactivates
      if (previousFocusRef.current && typeof previousFocusRef.current.focus === "function") {
        previousFocusRef.current.focus();
        previousFocusRef.current = null;
      }
    }
  }, [active]);

  // Keyboard handler: trap Tab, close on Escape
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!active || !containerRef.current) return;

      if (e.key === "Escape" && onClose) {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key !== "Tab") return;

      const focusable = getFocusableElements(containerRef.current);
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        // Shift+Tab: if at first element, wrap to last
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        // Tab: if at last element, wrap to first
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [active, onClose],
  );

  useEffect(() => {
    if (active) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [active, handleKeyDown]);

  return containerRef;
}

/** Query all focusable elements inside a container. */
function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const selector = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled]):not([type='hidden'])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])",
  ].join(", ");

  return Array.from(container.querySelectorAll<HTMLElement>(selector)).filter(
    (el) => !el.hasAttribute("disabled") && el.offsetParent !== null,
  );
}

export default useFocusTrap;
