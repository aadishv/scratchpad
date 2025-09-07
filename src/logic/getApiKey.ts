export function getApiKey(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("apiKey");
}
