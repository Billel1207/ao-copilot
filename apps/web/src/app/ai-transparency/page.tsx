import { redirect } from "next/navigation";

/**
 * Redirect /ai-transparency → /legal/ai-transparency
 * This shortcut URL is used in the AIDisclaimer component badge.
 */
export default function AITransparencyRedirect() {
  redirect("/legal/ai-transparency");
}
