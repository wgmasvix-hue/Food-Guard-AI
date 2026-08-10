import type { Metadata } from "next";
import Link from "next/link";

import { BrandMark } from "@/components/brand-mark";

export const metadata: Metadata = {
  title: "Privacy Policy — FoodOS",
  description: "How FoodOS collects, uses, and protects your data.",
};

const LAST_UPDATED = "August 2026";

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-ink-50 px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <Link href="/">
          <BrandMark />
        </Link>

        <div className="mt-8 rounded-3xl border border-ink-200/70 bg-surface p-8 shadow-soft-lg sm:p-10">
          <h1 className="text-2xl font-semibold tracking-tight text-ink-900">Privacy Policy</h1>
          <p className="mt-1 text-sm text-ink-500">Last updated: {LAST_UPDATED}</p>

          <div className="prose prose-sm mt-8 max-w-none text-ink-700 prose-headings:text-ink-900 prose-a:text-brand-700">
            <p>
              FoodOS (&quot;we&quot;, &quot;our&quot;) is a food safety, HACCP, GMP, and compliance
              management platform operated by ChengetAi Labs. This page explains what data we collect
              through the FoodOS web app and Android app, why, and how it&apos;s handled.
            </p>

            <h2>What we collect</h2>
            <ul>
              <li>
                <strong>Account information:</strong> your name, email address, phone number (optional),
                and role, plus the company you belong to.
              </li>
              <li>
                <strong>Food safety records your company enters:</strong> HACCP plans and hazards, GMP
                checklists, audit records, corrective actions, temperature logs, product formulations, and
                any documents or evidence files you upload. This is business operational data your company
                controls — we don&apos;t use it for anything beyond running the app for you.
              </li>
              <li>
                <strong>AI Assistant messages:</strong> when you use the AI Assistant, your question and
                relevant context from your own company&apos;s records are sent to the AI model configured
                for your deployment (typically a self-hosted Ollama instance we run — not a third-party AI
                vendor). Retrieval is strictly scoped to your own company&apos;s data; it never draws on or
                exposes another company&apos;s records.
              </li>
              <li>
                <strong>Billing information:</strong> if you pay by card, card details are handled entirely
                by Stripe and never touch our servers. If you pay by EcoCash, we store only the transaction
                reference code you submit for manual reconciliation — never any mobile money PIN or
                credentials.
              </li>
              <li>
                <strong>Basic technical data:</strong> login timestamps and an audit trail of actions taken
                in the app (who did what, when), kept for accountability and troubleshooting.
              </li>
            </ul>

            <h2>What we don&apos;t do</h2>
            <ul>
              <li>We don&apos;t sell your data, to anyone, ever.</li>
              <li>We don&apos;t run third-party analytics, advertising, or tracking scripts on FoodOS.</li>
              <li>We don&apos;t share your company&apos;s data with other companies using the platform — every account is strictly isolated to its own company.</li>
              <li>We don&apos;t use cross-site cookies. Your session is kept in your device&apos;s local storage, not a tracking cookie.</li>
            </ul>

            <h2>Data retention &amp; deletion</h2>
            <p>
              We keep your data for as long as your account is active. If you&apos;d like your account or
              your company&apos;s data deleted, contact us at the email below and we&apos;ll process the
              request, subject to any records we&apos;re legally required to retain (e.g. food safety
              records relevant to an active regulatory matter).
            </p>

            <h2>Security</h2>
            <p>
              Data is encrypted in transit (HTTPS/TLS) between your device and our servers. Passwords are
              hashed, never stored in plain text. Backups are encrypted at rest where the hosting
              environment supports it, and access to production systems is restricted to the operators of
              this deployment.
            </p>

            <h2>The Android app</h2>
            <p>
              The FoodOS Android app is a thin wrapper around this same web app (a Trusted Web Activity) —
              it doesn&apos;t collect anything beyond what&apos;s described above, and doesn&apos;t request
              any device permissions beyond internet access.
            </p>

            <h2>Changes to this policy</h2>
            <p>
              If this policy changes materially, we&apos;ll update the date at the top of this page. Continued
              use of FoodOS after a change constitutes acceptance of the updated policy.
            </p>

            <h2>Contact</h2>
            <p>
              Questions about this policy or a data request? Email{" "}
              <a href="mailto:privacy@chengetailabs.co.zw">privacy@chengetailabs.co.zw</a>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
