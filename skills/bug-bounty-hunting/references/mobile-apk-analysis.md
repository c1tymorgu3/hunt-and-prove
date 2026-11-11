# Android APK acquisition + decompilation on this Windows host

Verified working 2026-11. Every other route was blocked.

## 1. Get the APK

`apkpure.net` -> Tencent EdgeOne captcha. `apkmirror.com` / `apkfab.com` -> 403 to scripted clients.
`apkcombo.com` / `apk.support` -> DNS failure (TR ISP block). `apkeep -d google-play` -> `Invalid payload`
from the anonymous token dispenser. `api.pureapk.com` -> 400.

What works: **androidapksfree.com**, which serves the download link from androidapks.com.

A second path, for apps the first mirror does not carry: the **apkpure HTML page** (not its API) redirects to a signed CDN link.

```
GET https://apkpure.com/<slug>/<package>/download/<version>   -> 200 HTML
GET https://d.apkpure.com/b/APK/<package>?versionCode=<n>     -> 302
  -> https://data.winudf.com/APK/<opaque>?...&filename=<Name>_<ver>_APKPure.apk
```

Mirror availability rotates week to week: an app that was captcha-walled or missing on one mirror is often present on the other, so try both before telling the user an APK cannot be obtained. Verify the same way regardless of route — `PK\x03\x04`, `file` says Android package, package id matches the in-scope app.

```python
import urllib.request, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      'Referer': 'https://androidapksfree.com/'}

# 1. landing page -> link to the download page
land = urllib.request.urlopen(urllib.request.Request(
    'https://androidapksfree.com/apk/<slug>/<package>/', headers=UA), timeout=30).read().decode('utf-8', 'ignore')
dl_page = re.findall(r'href="(https://androidapks\.com/[^"]*download[^"]*)"', land)[0]

# 2. download page -> signed CDN link
html = urllib.request.urlopen(urllib.request.Request(dl_page, headers=UA), timeout=30).read().decode('utf-8', 'ignore')
cdn = re.findall(r'https://dl\.androidapksfree\.net/file/[^"]+', html)[0]

# 3. fetch (100-200 MB, allow minutes)
UA['Referer'] = dl_page
data = urllib.request.urlopen(urllib.request.Request(cdn, headers=UA), timeout=180).read()
open('app.apk', 'wb').write(data)
```

Verify before trusting it: first 4 bytes must be `PK\x03\x04` and `file app.apk` should say
`Android package (APK), with AndroidManifest.xml`. Then confirm the package name from the manifest
matches the in-scope app id. A mirror can serve a repackaged or wrong build — if the package or
version looks off, discard it.

## 2. Decompile

Install a real JDK — the host `java` is a 32-bit JRE 1.8 and jadx dies on `-Xmx4g`:

```bash
cd /c/Users/user/bb/tools
python -c "import urllib.request;open('jdk17.zip','wb').write(urllib.request.urlopen('https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse').read())"
unzip -q -o jdk17.zip
```

jadx 1.2.0's `jadx-cli-1.2.0.jar` has **no Main-Class manifest** — `java -jar` fails with
`no main manifest attribute`. Use the classpath form:

```bash
export JAVA_HOME="C:/Users/user/bb/tools/jdk-17.0.21+9"
./jdk-17.0.21+9/bin/java -Xmx3g -cp "jadx/lib/*" jadx.cli.JadxCLI \
    --no-src -d C:/Users/user/bb/<prog>/apk_out C:/Users/user/bb/tools/apk/app.apk
```

`--no-src` exports resources plus `AndroidManifest.xml` in about a minute and is enough for
manifest-level findings (exported components, deep links, permissions, `res/values/strings.xml`).
Full Java sources for a 130 MB app take much longer — run that as a separate longer step with `-Xmx3g`.

## 3. First things to read

```bash
M=apk_out/resources/AndroidManifest.xml
grep -o 'package="[^"]*"' $M
grep -o 'android:versionName="[^"]*"' $M
grep -c 'android:exported="true"' $M
grep -o '<intent-filter>' $M | wc -l        # deep-link surface size
grep -iE 'scheme|host' $M | head -40
```

Then: `android:debuggable`, `android:allowBackup`, `networkSecurityConfig`, `usesCleartextTraffic`,
WebView `addJavascriptInterface` in smali, hardcoded API keys in `strings.xml`, Firebase/Google API
keys in `res/values`, and the `assetlinks.json` trust file for debug-variant fingerprints.

## 4. Runtime proof for manifest findings

An exported activity/service in the manifest is a **hypothesis** until something launches it. `am start` either opens it or throws `SecurityException` — that difference is the finding.

Bring up a headless SDK emulator (scriptable, no GUI, survives an unattended agent):

```bash
SDK=C:/Users/user/bb/android-sdk
# cmdline-tools -> $SDK/cmdline-tools/latest (so bin/sdkmanager.bat lands there)
$SDK/cmdline-tools/latest/bin/sdkmanager.bat --sdk_root=$SDK \
  "platform-tools" "emulator" "system-images;android-33;google_apis;x86_64"
$SDK/cmdline-tools/latest/bin/avdmanager.bat create avd -n bb \
  -k "system-images;android-33;google_apis;x86_64" -d pixel_5
$SDK/emulator/emulator.exe -avd bb -no-window -no-audio -no-snapshot \
  -gpu swiftshader_indirect -no-boot-anim &
```

Then, in a poll loop (boot takes 3-8 minutes, the download is 2-4 GB):

```bash
ADB=$SDK/platform-tools/adb.exe
$ADB wait-for-device
$ADB shell getprop sys.boot_completed      # poll until 1
$ADB install -r app.apk
$ADB shell am start -n com.example/.ExportedComponent
$ADB logcat -d | tail -60
$ADB exec-out screencap -p > proof.png
```

- `SecurityException` / permission denial → **NOT exploitable**. Report that as the verdict; it is a real, useful result.
- The activity opens with no permission → **EXPLOITABLE**, and the logcat + screenshot is the evidence a triager will accept.
- Run `emulator -accel-check` first: with no virtualization the boot is glacial or fails, and knowing that before a 3 GB download saves the whole budget.
- Prefer the SDK emulator over consumer emulators (BlueStacks/LDPlayer/MuMu). Those need GUI interaction to finish setup, which stalls an agent that has no hands; the SDK emulator is CLI end to end.
- Re-signing a copy of the APK is legitimate for testing an `assetlinks.json` debug-variant hypothesis locally, but never install a modified build anywhere that talks to production accounts.

**Deep links need a different launcher than a component.** `am start -n pkg/.Activity` proves an activity is exported; it says nothing about what a URI does. Launch the URI itself and watch the app act:

```bash
$ADB shell am start -a android.intent.action.VIEW -d 'scheme://host/path?param=value'
$ADB logcat -d | grep -iE 'deep|link|login|token|server'
```

The classes that pay: a link that performs an authenticated action with no confirmation — logging in, adding an attacker-chosen server to the server list, joining a team — and a legacy callback scheme (`appauth://callback?TOKEN=…`) that still accepts a session token from the URL. Evidence is the logcat line plus a screenshot of the resulting state; "the manifest declares the scheme" is only a hypothesis.

Two classes are worth killing early with a grep rather than a hunt: token storage (if the app uses the platform keystore and `allowBackup=false`, plaintext-at-rest is gone) and an authenticated WebView (`grep -r react-native-webview` returning nothing in app code means the token-theft-via-embedded-browser story has no surface).

## 5. iOS without an IPA

The AASA file is served publicly by the in-scope web host:
`https://<host>/.well-known/apple-app-site-association` (also try the bare path). It gives bundle ids,
100+ universal-link paths, app clips and `webcredentials` apps. Custom schemes and deeplink parameters
can be scraped out of the web page's SSR JSON. That is enough to produce testable hypotheses without
ever touching the binary.
