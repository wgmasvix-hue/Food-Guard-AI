# Food Guard AI — Android app (Trusted Web Activity)

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
