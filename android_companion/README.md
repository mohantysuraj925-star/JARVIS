# Android Companion

A small Android client for authenticated pairing and an explicitly started,
visible WebSocket connection. The server can request opening only WhatsApp,
YouTube, or Android Settings. Every request is presented to the user, and the
selected app is launched only after the user taps **Open** on the confirmation
screen.

## Safety and transport

- Pairing posts `{username,password,device_name}` to
  `https://<host>/api/companion/pair`. Only a secure origin is accepted; a
  custom path, credentials in the URL, query, fragment, and cleartext HTTP are
  rejected.
- The bearer token is encrypted with AES-GCM using an Android Keystore key.
  The username and password are not persisted.
- The connection is started and stopped by the user. While active it runs as a
  foreground service with a persistent status notification and Stop action.
  Reconnect delay increases from one second to a maximum of 60 seconds.
- Incoming messages must have `action: "open_app"`, a known app identifier, and
  `requires_confirmation: true`. Unrecognized commands are rejected. No
  payload is evaluated or executed.
- Only package visibility for the three named apps is declared; the app does
  not request broad package visibility. Cleartext traffic is disabled.
- Android notification permission is requested on Android 13 and newer.

Each command result is sent once on the active WebSocket as
`{"type":"command_result","id":"<command id>","status":"launched|cancelled|unavailable"}`.
Results are never queued across connections. If a send fails, that result is
dropped, the socket is closed, and the service reconnects using the same
bounded exponential backoff.

The foreground-only composer accepts exactly `open WhatsApp`, `open YouTube`,
or `open Settings`, or offers matching quick choices. Its optional speech
button launches Android's speech recognizer only after a tap; the app does not
request microphone permission or record in the background. A selected phrase
is sent as `{"type":"request_command","app":"whatsapp|youtube|settings"}` on
the currently connected WebSocket. Requests are not queued while disconnected.
Any subsequent server command still requires a separate confirmation tap
before an app is launched.

## Build locally

Requirements: Android Studio with Android SDK Platform 35 and a Java 17 JDK.
The project uses Android Gradle Plugin 8.7.3, Kotlin 2.0.21, and Gradle 8.9.

1. Open the `android_companion` folder in Android Studio.
2. Allow Gradle sync to download the declared plugins and libraries.
3. Select **Build > Make Project**, or run the `app` configuration on an
   Android 8.0+ device/emulator.

With Android Studio/JDK 17 and `ANDROID_HOME` configured, run the wrapper from
this directory (it downloads the pinned Gradle 8.9 distribution and verifies
its SHA-256 checksum):

```powershell
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
```

To pair, enter an HTTPS origin such as `https://companion.example`, account
credentials, and a device name. After pairing, use **Start foreground
connection**. The persistent notification indicates connection state and
includes a Stop action. Tap a command notification to review it, then explicitly
choose **Open** or **Decline**.

The server must present a certificate trusted by Android. Do not disable
certificate validation or use an HTTP/WSS-insecure endpoint.
