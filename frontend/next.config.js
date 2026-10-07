/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Separate build dir per dev server so two `next dev` instances never
  // trample each other's webpack chunks (that corrupts HMR + API routes).
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

module.exports = nextConfig;
