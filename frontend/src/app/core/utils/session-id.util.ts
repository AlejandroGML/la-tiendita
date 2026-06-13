/** Key used to persist the guest session id in localStorage. */
export const GUEST_SESSION_ID_KEY = 'guest_session_id';

/**
 * Returns the current guest session ID from localStorage, or generates a new
 * cryptographically-random UUID and persists it when none exists yet.
 * The session ID is NOT a user identifier — it is scoped to cart/checkout
 * operations for anonymous visitors.
 */
export function getSessionId(): string {
  let id = localStorage.getItem(GUEST_SESSION_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(GUEST_SESSION_ID_KEY, id);
  }
  return id;
}
