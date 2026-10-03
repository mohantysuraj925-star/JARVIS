package com.example.androidcompanion

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecureTokenStore(context: Context) {
    private val preferences =
        context.getSharedPreferences("companion_secure_values", Context.MODE_PRIVATE)

    @Synchronized
    fun save(token: String) {
        require(token.isNotBlank()) { "Access token cannot be empty" }
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        val ciphertext = cipher.doFinal(token.toByteArray(Charsets.UTF_8))
        check(
            preferences.edit()
                .putString(KEY_IV, Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
                .putString(KEY_CIPHERTEXT, Base64.encodeToString(ciphertext, Base64.NO_WRAP))
                .commit()
        ) { "Could not save the encrypted access token" }
    }

    @Synchronized
    fun read(): String? {
        val iv = preferences.getString(KEY_IV, null) ?: return null
        val ciphertext = preferences.getString(KEY_CIPHERTEXT, null) ?: return null
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(
            Cipher.DECRYPT_MODE,
            getOrCreateKey(),
            GCMParameterSpec(GCM_TAG_LENGTH_BITS, Base64.decode(iv, Base64.NO_WRAP))
        )
        return cipher.doFinal(Base64.decode(ciphertext, Base64.NO_WRAP))
            .toString(Charsets.UTF_8)
    }

    @Synchronized
    fun clear() {
        preferences.edit().clear().apply()
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        keyStore.deleteEntry(KEY_ALIAS)
    }

    private fun getOrCreateKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        (keyStore.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }

        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        return generator.generateKey()
    }

    private companion object {
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val KEY_ALIAS = "companion_access_token_aes"
        const val KEY_IV = "access_token_iv"
        const val KEY_CIPHERTEXT = "access_token_ciphertext"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val GCM_TAG_LENGTH_BITS = 128
    }
}
