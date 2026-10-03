package com.example.androidcompanion

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.IntentFilter
import android.content.ActivityNotFoundException
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.core.content.ContextCompat
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private val worker = Executors.newSingleThreadExecutor()
    private lateinit var baseUrlInput: EditText
    private lateinit var usernameInput: EditText
    private lateinit var passwordInput: EditText
    private lateinit var deviceNameInput: EditText
    private lateinit var statusText: TextView
    private lateinit var commandInput: EditText
    private lateinit var commandStatusText: TextView
    private lateinit var pairButton: Button
    private lateinit var startButton: Button
    private lateinit var stopButton: Button
    private val tokenStore by lazy { SecureTokenStore(this) }
    private val commandStatusReceiver = object : android.content.BroadcastReceiver() {
        override fun onReceive(context: android.content.Context?, intent: Intent?) {
            if (intent?.action == CompanionConnectionService.ACTION_REQUEST_STATUS) {
                commandStatusText.text = intent.getStringExtra(EXTRA_REQUEST_STATUS)
                    ?: "Command request was not sent."
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestNotificationPermissionIfNeeded()
        buildUi()
        val preferences = getSharedPreferences(CompanionConfig.PREFS, MODE_PRIVATE)
        baseUrlInput.setText(preferences.getString(CompanionConfig.KEY_BASE_URL, "https://"))
        ContextCompat.registerReceiver(
            this,
            commandStatusReceiver,
            IntentFilter(CompanionConnectionService.ACTION_REQUEST_STATUS),
            ContextCompat.RECEIVER_NOT_EXPORTED
        )
        refreshPairingState()
    }

    override fun onDestroy() {
        unregisterReceiver(commandStatusReceiver)
        worker.shutdown()
        super.onDestroy()
    }

    @Deprecated("Deprecated in Android API")
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_NOTIFICATIONS &&
            grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED
        ) {
            showStatus("Notifications enabled. You can start the foreground connection.")
        }
    }

    private fun buildUi() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(24), dp(24), dp(24))
        }
        root.addView(TextView(this).apply {
            text = "Pair with your server"
            textSize = 24f
        }, matchWidth())
        root.addView(TextView(this).apply {
            text = "Pairing uses HTTPS. Commands can only open one of the listed apps after you confirm on this device."
            textSize = 14f
            setPadding(0, dp(8), 0, dp(16))
        }, matchWidth())

        baseUrlInput = field("HTTPS server base URL", "https://server.example")
        usernameInput = field("Username", "Username")
        passwordInput = field("Password", "Password").apply {
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
        }
        deviceNameInput = field("Device name", "My Android phone")
        listOf(baseUrlInput, usernameInput, passwordInput, deviceNameInput).forEach {
            root.addView(it, matchWidth())
        }

        pairButton = Button(this).apply {
            text = "Pair"
            setOnClickListener { pair() }
        }
        root.addView(pairButton, matchWidth())

        root.addView(TextView(this).apply {
            text = "Request an app"
            textSize = 20f
            setPadding(0, dp(16), 0, dp(4))
        }, matchWidth())
        root.addView(TextView(this).apply {
            text = "Choose a shortcut, or enter exactly “open WhatsApp”, “open YouTube”, or “open Settings”. This sends a request; it does not open the app."
            textSize = 14f
            setPadding(0, 0, 0, dp(8))
        }, matchWidth())
        commandInput = field("App request", "open WhatsApp")
        root.addView(commandInput, matchWidth())
        val quickChoices = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
        }
        listOf(CompanionApp.WHATSAPP, CompanionApp.YOUTUBE, CompanionApp.SETTINGS).forEach { app ->
            quickChoices.addView(Button(this).apply {
                text = app.displayName
                setOnClickListener { requestCommand(app) }
            }, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        }
        root.addView(quickChoices, matchWidth())
        val requestActions = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
        }
        requestActions.addView(Button(this).apply {
            text = "Send request"
            setOnClickListener {
                val app = CompanionApp.fromComposerText(commandInput.text.toString())
                if (app == null) {
                    commandStatusText.text =
                        "Use exactly “open WhatsApp”, “open YouTube”, or “open Settings”."
                } else {
                    requestCommand(app)
                }
            }
        }, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        requestActions.addView(Button(this).apply {
            text = "Speak request"
            setOnClickListener { startSpeechRecognition() }
        }, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        root.addView(requestActions, matchWidth())
        commandStatusText = TextView(this).apply {
            textSize = 14f
            setPadding(0, dp(4), 0, dp(8))
        }
        root.addView(commandStatusText, matchWidth())

        statusText = TextView(this).apply {
            textSize = 15f
            setPadding(0, dp(12), 0, dp(8))
        }
        root.addView(statusText, matchWidth())
        startButton = Button(this).apply {
            text = "Start foreground connection"
            setOnClickListener { startConnection() }
        }
        stopButton = Button(this).apply {
            text = "Stop connection"
            setOnClickListener { stopConnection() }
        }
        root.addView(startButton, matchWidth())
        root.addView(stopButton, matchWidth())
        root.addView(TextView(this).apply {
            text = "Allowed apps: WhatsApp, YouTube, and Android Settings."
            textSize = 13f
            setPadding(0, dp(16), 0, 0)
        }, matchWidth())

        setContentView(ScrollView(this).apply {
            isFillViewport = true
            addView(root)
        })
    }

    private fun requestCommand(app: CompanionApp) {
        commandInput.setText("open ${app.displayName}")
        sendBroadcast(
            Intent(CompanionConnectionService.ACTION_REQUEST_COMMAND)
                .setPackage(packageName)
                .putExtra(CompanionConnectionService.EXTRA_REQUEST_APP, app.commandName)
        )
        commandStatusText.text = "Sending request for ${app.displayName} over the active connection…"
    }

    private fun startSpeechRecognition() {
        val speechIntent = Intent(android.speech.RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            .putExtra(
                android.speech.RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                android.speech.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            .putExtra(
                android.speech.RecognizerIntent.EXTRA_PROMPT,
                "Say: open WhatsApp, open YouTube, or open Settings"
            )
        try {
            startActivityForResult(speechIntent, REQUEST_SPEECH)
        } catch (_: ActivityNotFoundException) {
            commandStatusText.text = "Speech recognition is unavailable on this device."
        }
    }

    @Deprecated("Deprecated in Android API")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != REQUEST_SPEECH || resultCode != RESULT_OK) return
        val phrases = data?.getStringArrayListExtra(android.speech.RecognizerIntent.EXTRA_RESULTS)
        val app = phrases?.firstOrNull()?.let(CompanionApp::fromComposerText)
        if (app == null) {
            commandStatusText.text =
                "Request not recognized. Say exactly “open WhatsApp”, “open YouTube”, or “open Settings”."
        } else {
            requestCommand(app)
        }
    }

    private fun pair() {
        val base = CompanionConfig.validatedBaseUrl(baseUrlInput.text.toString())
        if (base == null) {
            showStatus("Enter an HTTPS base URL such as https://server.example.")
            return
        }
        val username = usernameInput.text.toString().trim()
        val password = passwordInput.text.toString()
        val deviceName = deviceNameInput.text.toString().trim()
        if (username.isBlank() || password.isBlank() || deviceName.isBlank()) {
            showStatus("Enter a username, password, and device name.")
            return
        }

        pairButton.isEnabled = false
        showStatus("Pairing securely…")
        worker.execute {
            try {
                val result = PairingClient().pair(base, username, password, deviceName)
                tokenStore.save(result.accessToken)
                getSharedPreferences(CompanionConfig.PREFS, MODE_PRIVATE).edit()
                    .putString(CompanionConfig.KEY_BASE_URL, base.toString())
                    .putString(CompanionConfig.KEY_DEVICE_ID, result.deviceId)
                    .apply()
                runOnUiThread {
                    passwordInput.text.clear()
                    showStatus("Paired as device ${result.deviceId}.")
                    refreshPairingState()
                }
            } catch (error: Exception) {
                runOnUiThread {
                    showStatus(error.message ?: "Pairing failed.")
                    pairButton.isEnabled = true
                }
            }
        }
    }

    private fun startConnection() {
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            showStatus("Allow notifications to receive and review commands.")
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), REQUEST_NOTIFICATIONS)
            return
        }
        val tokenAvailable = try {
            tokenStore.read() != null
        } catch (_: Exception) {
            false
        }
        if (!tokenAvailable) {
            showStatus("Pair this device before starting the connection.")
            return
        }
        val preferences = getSharedPreferences(CompanionConfig.PREFS, MODE_PRIVATE)
        val base = CompanionConfig.validatedBaseUrl(
            preferences.getString(CompanionConfig.KEY_BASE_URL, "").orEmpty()
        )
        if (base == null) {
            showStatus("The saved server URL is invalid. Pair again.")
            return
        }
        val intent = Intent(this, CompanionConnectionService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ContextCompat.startForegroundService(this, intent)
        } else {
            startService(intent)
        }
        showStatus("Connection service started. Its ongoing notification shows connection state.")
    }

    private fun stopConnection() {
        stopService(Intent(this, CompanionConnectionService::class.java))
        showStatus("Connection stopped.")
    }

    private fun refreshPairingState() {
        val paired = try {
            tokenStore.read() != null
        } catch (_: Exception) {
            false
        }
        pairButton.isEnabled = true
        startButton.isEnabled = paired
        stopButton.isEnabled = true
        if (paired) showStatus("This device is paired.")
        else showStatus("Not paired.")
    }

    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), REQUEST_NOTIFICATIONS)
        }
    }

    private fun field(label: String, hint: String): EditText =
        EditText(this).apply {
            contentDescription = label
            this.hint = hint
            singleLine = true
            setPadding(dp(12), dp(8), dp(12), dp(8))
        }

    private fun showStatus(message: String) {
        statusText.text = message
    }

    private fun matchWidth(): LinearLayout.LayoutParams =
        LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private companion object {
        const val REQUEST_NOTIFICATIONS = 401
        const val REQUEST_SPEECH = 402
        const val EXTRA_REQUEST_STATUS = "request_status"
    }
}
