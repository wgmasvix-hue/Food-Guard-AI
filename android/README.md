# FoodOS — Android app (Trusted Web Activity)

This wraps the live PWA at `https://foodguard.chengetailabs.co.zw` in a
Trusted Web Activity (TWA) — a thin native Android shell around the
existing web app. There is no separate native codebase to maintain: the
UI, features, and bug fixes all come from the web app itself.

## How the APK gets built

`.github/workflows/build-android-apk.yml` builds it in CI using
[Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap), Google's
official TWA tooling. It reads `twa-manifest.json` in this directory and
needs the release signing keystore supplied via repository secrets (see
below) — the Android SDK download this requires is blocked from most
sandboxed dev environments, which is why this runs in GitHub Actions
rather than being built locally by an agent.

Trigger it from the Actions tab ("Build Android APK" → Run workflow) or
push a change under `android/`. The signed `.apk` is uploaded as a
workflow run artifact, and — as long as the repository secrets below are
set — also published to a GitHub Release. That gives a stable public
download link that always serves the most recent successful build,
without needing a GitHub login (unlike workflow artifacts):

```
https://github.com/wgmasvix-hue/Food-Guard-AI/releases/latest/download/FoodGuardAI.apk
```

This is the link the web app's "Download Android App" footer button
points to.

## Required repository secrets

| Secret | Value |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | The release keystore, base64-encoded |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | `foodguard` |
| `ANDROID_KEY_PASSWORD` | Key password (same as keystore password for a PKCS12 keystore) |

Add these under the repo's **Settings → Secrets and variables → Actions →
New repository secret**. Whoever generated the keystore should have
handed you the actual values separately — never commit them to the repo.

## Digital Asset Links (removes the browser address bar)

`frontend/public/.well-known/assetlinks.json` already contains the
fingerprint of the keystore used for the first build, so once deployed,
the installed APK opens in full "trusted" mode (no browser chrome) rather
than falling back to a Custom Tab. If you ever re-generate the keystore,
recompute the fingerprint (`keytool -list -v -keystore <file> -alias
foodguard`) and update `assetlinks.json` to match, then redeploy the web
app.

## Bumping the version for an update

Edit `appVersionName` and increment `appVersionCode` in
`twa-manifest.json`, then re-run the workflow. Android requires
`appVersionCode` to strictly increase between installs of the same
`packageId` for an upgrade (rather than "app already installed") to work.

## Building locally instead (optional)

Only works from a network that can reach `dl.google.com` (most sandboxed
CI/dev environments can't):

```bash
npm i -g @bubblewrap/cli
cd android
bubblewrap build
```

## Publishing to the Google Play Store

The CI build also produces a signed `.aab` (Android App Bundle) —
Bubblewrap generates one alongside the `.apk` automatically. It's
uploaded as a private workflow artifact named
`food-guard-ai-android-bundle` (Actions tab → the run → Artifacts),
**not** published to the public GitHub Release like the `.apk` — Play
Console is the only place the `.aab` should go.

Steps (each only needs doing once per new listing):

1. **Create a Google Play Developer account** — [play.google.com/console](https://play.google.com/console/signup),
   one-time $25 registration fee. Only the account owner can do this.
2. **Create the app** in Play Console → set the app name (`FoodOS`),
   default language, app/game = App, free/paid = Free (billing happens
   in-app via Stripe/EcoCash, not through Play Billing).
3. **Upload the `.aab`** under Production (or Internal testing first,
   recommended) → Create new release. Play App Signing will offer to
   manage your app signing key — accept it (Google re-signs releases
   with its own key derived from your upload key; the upload key here
   is the same `android.keystore` used for the `.apk`).
4. **Privacy Policy URL**: `https://foodguard.chengetailabs.co.zw/privacy`
   (required — the app handles user accounts and company data).
5. **Data safety form**: declare what's collected — account info (name,
   email, phone), and the food-safety records the company itself enters
   (HACCP/GMP/audit/temperature/document data). None of it is sold or
   shared with third parties; all of it is deletable via account/company
   deletion. See `docs/OPERATIONS.md` for the actual data model if you
   need exact field-level detail for the form.
6. **Store listing assets needed**: app icon (512×512, already have —
   `frontend/public/icons/icon-512.png`), a feature graphic (1024×500,
   not yet created), and 2–8 phone screenshots (not yet created — this
   sandboxed agent environment's network policy blocks reaching the
   live custom domain directly, so these need to come from a real
   device/browser: log into the live site or installed app and take a
   few screenshots of Dashboard, HACCP, and the AI Assistant).
7. **Content rating questionnaire**: answer as a business/productivity
   utility app with no user-generated public content, no ads, no
   in-app purchases processed through Google — should land in the
   lowest rating tier.
8. Submit for review. First review is typically 1–7 days.

Package ID is `com.chengetailabs.foodos` (renamed from the pre-rebrand
`ai.foodguard.twa` before any Play Store submission — Google doesn't
allow changing it after the first upload, so this was done early
deliberately). If you ever regenerate the signing keystore, recompute
its fingerprint and update `frontend/public/.well-known/assetlinks.json`
to match, then redeploy the web app.
