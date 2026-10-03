package com.example.androidcompanion

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

data class PairingResult(val deviceId: String, val accessToken: String)

class PairingClient {
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .followRedirects(false)
        .followSslRedirects(false)
        .build()

    @Throws(IOException::class)
    fun pair(baseUrl: okhttp3.HttpUrl, username: String, password: String, deviceName: String): PairingResult {
        val payload = JSONObject()
            .put("username", username)
            .put("password", password)
            .put("device_name", deviceName)
            .toString()
            .toRequestBody(JSON_MEDIA_TYPE)
        val request = Request.Builder()
            .url(CompanionConfig.pairUrl(baseUrl))
            .post(payload)
            .build()

        client.newCall(request).execute().use { response ->
            val responseBody = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                throw IOException("Pairing failed (HTTP ${response.code})")
            }
            val json = try {
                JSONObject(responseBody)
            } catch (_: Exception) {
                throw IOException("The server returned an invalid pairing response")
            }
            val deviceId = json.opt("device_id") as? String
            val token = json.opt("access_token") as? String
            if (json.opt("status") != "paired" ||
                deviceId.isNullOrBlank() ||
                token.isNullOrBlank()
            ) {
                throw IOException("The server returned an incomplete pairing response")
            }
            return PairingResult(deviceId, token)
        }
    }

    private companion object {
        val JSON_MEDIA_TYPE = "application/json; charset=utf-8".toMediaType()
    }
}
