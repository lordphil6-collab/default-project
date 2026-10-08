// Outbound app email (password resets, invitations). Uses SMTP when configured;
// otherwise logs the link server-side (dev) so flows stay testable. Never throws.
import nodemailer from "nodemailer";

function transporter() {
  const host = process.env.SMTP_HOST || "";
  if (!host) return null;
  return nodemailer.createTransport({
    host,
    port: Number(process.env.SMTP_PORT || 587),
    secure: Number(process.env.SMTP_PORT || 587) === 465,
    auth: process.env.SMTP_USER
      ? { user: process.env.SMTP_USER, pass: process.env.SMTP_PASSWORD || "" }
      : undefined,
  });
}

export async function sendAppEmail(to: string, subject: string, html: string): Promise<{ sent: boolean }> {
  const t = transporter();
  const from = process.env.SMTP_FROM || process.env.SMTP_USER || "no-reply@localhost";
  if (!t) {
    console.log(`[mail:logged-only] to=${to} subject=${subject}`);
    return { sent: false };
  }
  await t.sendMail({ from, to, subject, html });
  return { sent: true };
}
