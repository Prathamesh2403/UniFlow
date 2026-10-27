/**
 * Frontend Configuration
 * Supports production deployment on Vercel via NEXT_PUBLIC_API_URL / NEXT_PUBLIC_WS_URL,
 * with dynamic localhost fallback for local testing.
 */

const getBackendHost = () => {
    if (typeof window !== "undefined") {
        return window.location.hostname;
    }
    return "localhost";
};

/**
 * Base API URL for HTTP endpoints.
 */
export const API_BASE_URL = (
    process.env.NEXT_PUBLIC_API_URL || `http://${getBackendHost()}:8000`
).replace(/\/+$/, "");

/**
 * Base WebSocket URL for real-time classroom updates.
 */
export const WS_BASE_URL = (() => {
    if (process.env.NEXT_PUBLIC_WS_URL) {
        return process.env.NEXT_PUBLIC_WS_URL.replace(/\/+$/, "");
    }
    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL.replace(/^http/i, "ws").replace(/\/+$/, "");
    }
    const host = getBackendHost();
    const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss" : "ws";
    return `${protocol}://${host}:8000`;
})();

/**
 * Resolves file playback/view URL.
 * Handles full Cloudinary URLs (https://...) and legacy local paths (/static/...).
 */
export const getFileUrl = (url?: string | null): string => {
    if (!url) return "";
    if (url.startsWith("http://") || url.startsWith("https://")) {
        return url;
    }
    const cleanPath = url.startsWith("/") ? url : `/${url}`;
    return `${API_BASE_URL}${cleanPath}`;
};

console.log(`[Config] 🚀 API Base: ${API_BASE_URL}`);
console.log(`[Config] 🔄 WS Base: ${WS_BASE_URL}`);
