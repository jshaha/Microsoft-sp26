// Single source of truth for "who is viewing this dashboard".
//
// For the prototype we sign in as a fixed user (`mark_johnson`). In production
// this would be wired to Microsoft sign-in; the rest of the app only needs
// `userId` and a setter, so swapping the provider is a one-line change.
 
import { createContext, useContext, useMemo, useState } from "react";
 
const UserContext = createContext(null);
 
export function UserProvider({ children, initialUserId = "mark_johnson" }) {
  const [userId, setUserId] = useState(initialUserId);
  const value = useMemo(() => ({ userId, setUserId }), [userId]);
  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}
 
export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within <UserProvider>");
  return ctx;
}