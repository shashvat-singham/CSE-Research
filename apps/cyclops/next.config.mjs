/**
 * Cyclops build configuration.
 *
 * The app is entirely self-hosted content — no remote images, no third-party
 * scripts — so the CSP below can be strict. `unsafe-inline` on styles is
 * required by Next's own injected style tags; scripts do not need it because
 * Next emits nonce-free external bundles here.
 */

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data:",
      "font-src 'self' data:",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join("; "),
  },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // The Docker build sets this to emit a self-contained server bundle. Vercel
  // does its own tracing, so leaving it off there avoids duplicated output.
  output: process.env.BUILD_STANDALONE === "1" ? "standalone" : undefined,
  images: {
    // No remote images and no next/image usage; skip the optimizer entirely.
    unoptimized: true,
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
