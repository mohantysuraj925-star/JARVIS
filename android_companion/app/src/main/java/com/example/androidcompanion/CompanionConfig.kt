package com.example.androidcompanion

import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

object CompanionConfig {
    const val PREFS = "companion_config"
    const val KEY_BASE_URL = "base_url"
    const val KEY_DEVICE_ID = "device_id"

    fun validatedBaseUrl(raw: String): HttpUrl? {
        val url = raw.trim().toHttpUrlOrNull() ?: return null
        if (url.scheme != "https" || url.host.isBlank()) return null
        if (url.username.isNotEmpty() || url.password.isNotEmpty()) return null
        if (url.encodedPath != "/" || url.query != null || url.fragment != null) return null
        return url
    }

    fun pairUrl(base: HttpUrl): HttpUrl =
        base.newBuilder().encodedPath("/api/companion/pair").build()

    // OkHttp's WebSocket API takes an HTTPS URL and upgrades it to WSS for the handshake.
    fun websocketUrl(base: HttpUrl): HttpUrl =
        base.newBuilder().encodedPath("/ws/companion").build()
}
