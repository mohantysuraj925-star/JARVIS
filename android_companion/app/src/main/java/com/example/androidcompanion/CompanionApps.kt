package com.example.androidcompanion

import android.content.Context
import android.content.Intent
import java.util.Locale

enum class CompanionApp(
    val commandName: String,
    val displayName: String,
    private val packageName: String
) {
    WHATSAPP("whatsapp", "WhatsApp", "com.whatsapp"),
    YOUTUBE("youtube", "YouTube", "com.google.android.youtube"),
    SETTINGS("settings", "Settings", "com.android.settings");

    fun launchIntent(context: Context): Intent? =
        context.packageManager.getLaunchIntentForPackage(packageName)

    companion object {
        fun fromCommand(value: String): CompanionApp? =
            entries.firstOrNull { it.commandName == value }

        fun fromComposerText(value: String): CompanionApp? =
            when (value.trim().lowercase(Locale.ROOT)) {
                "open whatsapp" -> WHATSAPP
                "open youtube" -> YOUTUBE
                "open settings" -> SETTINGS
                else -> null
            }
    }
}
