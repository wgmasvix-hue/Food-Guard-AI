"use client";

import { PenLine } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth-context";
import type { SignatureMeaning } from "@/lib/types";

const MEANING_COPY: Record<SignatureMeaning, string> = {
  audit_completion: "completing this audit",
  haccp_plan_approval: "approving this HACCP plan",
  corrective_action_verification: "verifying this corrective action as effective",
};

interface SignatureDialogProps {
  open: boolean;
  onClose: () => void;
  onSign: (typedName: string) => Promise<void> | void;
  meaning: SignatureMeaning;
  title?: string;
  error?: string | null;
}

/** Lightweight e-signature capture: the signer must type their own full name
 * to attest to a specific action. Not a cryptographic signature — a
 * re-authentication-style attestation recorded with a timestamp and IP. */
export function SignatureDialog({ open, onClose, onSign, meaning, title, error }: SignatureDialogProps) {
  const { user } = useAuth();
  const [typedName, setTypedName] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await onSign(typedName);
      setTypedName("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title={title ?? "Sign to confirm"} className="max-w-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-3 rounded-lg bg-ink-50 p-3">
          <PenLine className="h-4 w-4 shrink-0 text-ink-500" />
          <p className="text-sm text-ink-600">
            By typing your full name below, you are electronically signing and attesting to{" "}
            {MEANING_COPY[meaning]}. This is recorded with your account, a timestamp, and your IP address.
          </p>
        </div>
        <div>
          <Label htmlFor="typed_name">Type your full name to sign</Label>
          <Input
            id="typed_name"
            required
            autoComplete="off"
            value={typedName}
            onChange={(e) => setTypedName(e.target.value)}
            placeholder={user?.full_name ?? "Your full name"}
          />
        </div>
        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={busy}>Cancel</Button>
          <Button type="submit" disabled={busy}>{busy ? "Signing…" : "Sign & Confirm"}</Button>
        </div>
      </form>
    </Dialog>
  );
}
