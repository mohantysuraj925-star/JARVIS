package com.example.androidcompanion

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.content.Intent

class ConfirmationActivity : Activity() {
    private var commandId: String? = null
    private var selectedApp: CompanionApp? = null
    private var resultSent = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        commandId = intent.getStringExtra(EXTRA_COMMAND_ID)?.takeIf { it.isNotBlank() }
        selectedApp = intent.getStringExtra(EXTRA_APP)?.let(CompanionApp::fromCommand)
        val id = commandId
        val app = selectedApp
        if (id == null || app == null) {
            finish()
            return
        }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(dp(24), dp(24), dp(24), dp(24))
        }
        root.addView(TextView(this).apply {
            text = "The companion server requests to open ${app.displayName}."
            textSize = 20f
            gravity = Gravity.CENTER
        }, matchWidth())
        root.addView(TextView(this).apply {
            text = "Nothing will open unless you choose Open below."
            textSize = 15f
            gravity = Gravity.CENTER
            setPadding(0, dp(12), 0, dp(20))
        }, matchWidth())
        root.addView(Button(this).apply {
            text = "Open ${app.displayName}"
            setOnClickListener { confirm(app, id) }
        }, matchWidth())
        root.addView(Button(this).apply {
            text = "Decline"
            setOnClickListener {
                report(id, STATUS_CANCELLED)
                finish()
            }
        }, matchWidth())
        setContentView(root)
    }

    override fun onBackPressed() {
        commandId?.let { report(it, STATUS_CANCELLED) }
        super.onBackPressed()
    }

    override fun onDestroy() {
        if (!resultSent) commandId?.let { report(it, STATUS_CANCELLED) }
        super.onDestroy()
    }

    private fun confirm(app: CompanionApp, id: String) {
        val launchIntent = app.launchIntent(this)
        if (launchIntent == null) {
            report(id, STATUS_UNAVAILABLE)
            finish()
            return
        }
        try {
            startActivity(launchIntent)
            report(id, STATUS_LAUNCHED)
        } catch (_: Exception) {
            report(id, STATUS_UNAVAILABLE)
        }
        finish()
    }

    private fun report(id: String, result: String) {
        if (resultSent) return
        resultSent = true
        sendBroadcast(
            Intent(CompanionConnectionService.ACTION_COMMAND_RESULT)
                .setPackage(packageName)
                .putExtra(EXTRA_COMMAND_ID, id)
                .putExtra(EXTRA_RESULT, result)
        )
    }

    private fun matchWidth(): LinearLayout.LayoutParams =
        LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    companion object {
        const val EXTRA_COMMAND_ID = "command_id"
        const val EXTRA_APP = "app"
        const val EXTRA_RESULT = "result"
        const val STATUS_LAUNCHED = "launched"
        const val STATUS_CANCELLED = "cancelled"
        const val STATUS_UNAVAILABLE = "unavailable"
    }
}
