package com.example.androidcompanion

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.TimeUnit
import kotlin.math.min

class CompanionConnectionService : Service() {
    private lateinit var scheduler: ScheduledExecutorService
    private lateinit var client: OkHttpClient
    private lateinit var tokenStore: SecureTokenStore
    @Volatile
    private var socket: WebSocket? = null
    private var reconnectFuture: ScheduledFuture<*>? = null
    @Volatile
    private var running = false
    private var retryAttempt = 0

    private val resultReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == ACTION_REQUEST_COMMAND) {
                val app = intent.getStringExtra(EXTRA_REQUEST_APP)
                    ?.let(CompanionApp::fromCommand) ?: return
                sendCommandRequest(app)
                return
            }
            if (intent?.action != ACTION_COMMAND_RESULT) return
            val id = intent?.getStringExtra(ConfirmationActivity.EXTRA_COMMAND_ID)
                ?.takeIf { it.isNotBlank() } ?: return
            val result = intent.getStringExtra(ConfirmationActivity.EXTRA_RESULT)
                ?.takeIf {
                    it == ConfirmationActivity.STATUS_LAUNCHED ||
                        it == ConfirmationActivity.STATUS_CANCELLED ||
                        it == ConfirmationActivity.STATUS_UNAVAILABLE
                } ?: return
            acknowledge(id, result)
        }
    }

    override fun onCreate() {
        super.onCreate()
        tokenStore = SecureTokenStore(this)
        scheduler = Executors.newSingleThreadScheduledExecutor()
        client = OkHttpClient.Builder()
            .pingInterval(30, TimeUnit.SECONDS)
            .connectTimeout(15, TimeUnit.SECONDS)
            .followRedirects(false)
            .followSslRedirects(false)
            .build()
        registerResultReceiver()
        ensureNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopConnection()
            return START_NOT_STICKY
        }
        if (!running) {
            running = true
            startForeground(NOTIFICATION_ID, connectionNotification("Connecting securely…"))
            connect()
        }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        running = false
        reconnectFuture?.cancel(true)
        socket?.close(1000, "User stopped connection")
        socket = null
        scheduler.shutdownNow()
        client.dispatcher.cancelAll()
        try {
            unregisterReceiver(resultReceiver)
        } catch (_: IllegalArgumentException) {
            // Receiver may not have been registered if service initialization failed.
        }
        super.onDestroy()
    }

    private fun connect() {
        if (!running) return
        val base = CompanionConfig.validatedBaseUrl(
            getSharedPreferences(CompanionConfig.PREFS, MODE_PRIVATE)
                .getString(CompanionConfig.KEY_BASE_URL, "").orEmpty()
        )
        val token = try {
            tokenStore.read()
        } catch (_: Exception) {
            null
        }
        if (base == null || token.isNullOrBlank()) {
            updateConnectionNotification("Pairing is unavailable. Stop and pair again.")
            stopConnection()
            return
        }

        updateConnectionNotification("Connecting securely…")
        val request = Request.Builder()
            .url(CompanionConfig.websocketUrl(base))
            .header("Authorization", "Bearer $token")
            .build()
        socket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                if (!running) {
                    webSocket.close(1000, "Service stopped")
                    return
                }
                socket = webSocket
                retryAttempt = 0
                updateConnectionNotification("Connected securely")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                handleCommand(text)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                if (socket === webSocket) socket = null
                if (code == 4401 || code == 4403) {
                    running = false
                    reconnectFuture?.cancel(true)
                    reconnectFuture = null
                    stopForeground(STOP_FOREGROUND_REMOVE)
                    stopSelf()
                    return
                }
                scheduleReconnect("Connection closed")
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                if (socket === webSocket) socket = null
                if (response?.code == 403 || response?.code == 401) {
                    running = false
                    reconnectFuture?.cancel(true)
                    reconnectFuture = null
                    stopForeground(STOP_FOREGROUND_REMOVE)
                    stopSelf()
                    return
                }
                scheduleReconnect("Connection lost; reconnecting")
            }
        })
    }

    private fun handleCommand(raw: String) {
        val json = try {
            JSONObject(raw)
        } catch (_: Exception) {
            return
        }
        val id = json.optString("id").takeIf { it.isNotBlank() && it.length <= 256 } ?: return
        val app = CompanionApp.fromCommand(json.optString("app"))
        if (json.optString("action") != "open_app" ||
            json.opt("requires_confirmation") != true ||
            app == null
        ) {
            acknowledge(id, ConfirmationActivity.STATUS_UNAVAILABLE)
            return
        }

        val openIntent = Intent(this, ConfirmationActivity::class.java)
            .putExtra(ConfirmationActivity.EXTRA_COMMAND_ID, id)
            .putExtra(ConfirmationActivity.EXTRA_APP, app.commandName)
        val notificationId = nextCommandNotificationId.getAndIncrement()
        val pendingIntent = PendingIntent.getActivity(
            this,
            notificationId,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val notification = NotificationCompat.Builder(this, COMMAND_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Companion command")
            .setContentText("Tap to review a request to open ${app.displayName}")
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                "The server requests to open ${app.displayName}. Tap to review; the app will not open until you confirm."
            ))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()
        getSystemService(NotificationManager::class.java)
            .notify(notificationId, notification)
    }

    private fun acknowledge(id: String, result: String) {
        if (!running) return
        val ack = JSONObject()
            .put("type", "command_result")
            .put("id", id)
            .put("status", result)
            .toString()
        val activeSocket = socket
        if (activeSocket == null || !activeSocket.send(ack)) {
            activeSocket?.close(1011, "Command result could not be sent")
            scheduleReconnect("Result not sent; reconnecting")
        }
    }

    private fun sendCommandRequest(app: CompanionApp) {
        val request = JSONObject()
            .put("type", "request_command")
            .put("app", app.commandName)
            .toString()
        val activeSocket = socket
        if (!running || activeSocket == null || !activeSocket.send(request)) {
            if (activeSocket != null) {
                activeSocket.close(1011, "Command request could not be sent")
                scheduleReconnect("Request not sent; reconnecting")
            } else {
                scheduleReconnect("Not connected; request not sent")
            }
            reportRequestStatus("Not connected; request was not sent.")
            return
        }
        reportRequestStatus("Request for ${app.displayName} sent. Approve any app launch separately.")
    }

    private fun reportRequestStatus(message: String) {
        sendBroadcast(
            Intent(ACTION_REQUEST_STATUS)
                .setPackage(packageName)
                .putExtra(EXTRA_REQUEST_STATUS, message)
        )
    }

    @Synchronized
    private fun scheduleReconnect(message: String) {
        if (!running || reconnectFuture != null) return
        retryAttempt += 1
        val delaySeconds = min(60L, 1L shl min(retryAttempt - 1, 6))
        updateConnectionNotification(message)
        reconnectFuture = scheduler.schedule({
            synchronized(this) {
                reconnectFuture = null
            }
            connect()
        }, delaySeconds, TimeUnit.SECONDS)
    }

    private fun stopConnection() {
        running = false
        reconnectFuture?.cancel(true)
        reconnectFuture = null
        socket?.close(1000, "User stopped connection")
        socket = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun connectionNotification(message: String): Notification {
        val stopIntent = PendingIntent.getService(
            this,
            STOP_REQUEST_CODE,
            Intent(this, CompanionConnectionService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val openIntent = PendingIntent.getActivity(
            this,
            OPEN_REQUEST_CODE,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, SERVICE_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setContentTitle("Android Companion")
            .setContentText(message)
            .setContentIntent(openIntent)
            .setOngoing(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .addAction(0, "Stop", stopIntent)
            .build()
    }

    private fun updateConnectionNotification(message: String) {
        if (running) {
            getSystemService(NotificationManager::class.java)
                .notify(NOTIFICATION_ID, connectionNotification(message))
        }
    }

    private fun ensureNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(SERVICE_CHANNEL_ID, "Connection status", NotificationManager.IMPORTANCE_LOW)
        )
        manager.createNotificationChannel(
            NotificationChannel(COMMAND_CHANNEL_ID, "Command confirmations", NotificationManager.IMPORTANCE_HIGH)
        )
    }

    private fun registerResultReceiver() {
        val filter = IntentFilter().apply {
            addAction(ACTION_COMMAND_RESULT)
            addAction(ACTION_REQUEST_COMMAND)
        }
        ContextCompat.registerReceiver(
            this,
            resultReceiver,
            filter,
            ContextCompat.RECEIVER_NOT_EXPORTED
        )
    }

    companion object {
        const val ACTION_COMMAND_RESULT = "com.example.androidcompanion.COMMAND_RESULT"
        const val ACTION_REQUEST_COMMAND = "com.example.androidcompanion.REQUEST_COMMAND"
        const val ACTION_REQUEST_STATUS = "com.example.androidcompanion.REQUEST_STATUS"
        const val EXTRA_REQUEST_APP = "request_app"
        private const val EXTRA_REQUEST_STATUS = "request_status"
        private const val ACTION_STOP = "com.example.androidcompanion.STOP_CONNECTION"
        private const val SERVICE_CHANNEL_ID = "companion_connection"
        private const val COMMAND_CHANNEL_ID = "companion_commands"
        private const val NOTIFICATION_ID = 7101
        private const val STOP_REQUEST_CODE = 7102
        private const val OPEN_REQUEST_CODE = 7103
        private val nextCommandNotificationId = AtomicInteger(7200)
    }
}
