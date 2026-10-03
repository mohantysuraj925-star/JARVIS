package com.example.androidcompanion

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class CompanionConfigTest {
    @Test
    fun acceptsOnlySecureOriginBaseUrls() {
        assertEquals("https://companion.example/", CompanionConfig.validatedBaseUrl("https://companion.example")?.toString())
        assertNull(CompanionConfig.validatedBaseUrl("http://companion.example"))
        assertNull(CompanionConfig.validatedBaseUrl("https://user@companion.example"))
        assertNull(CompanionConfig.validatedBaseUrl("https://companion.example/custom"))
        assertNull(CompanionConfig.validatedBaseUrl("https://companion.example/?next=other"))
    }

    @Test
    fun buildsOnlyContractEndpoints() {
        val base = requireNotNull(CompanionConfig.validatedBaseUrl("https://companion.example"))
        assertEquals("https://companion.example/api/companion/pair", CompanionConfig.pairUrl(base).toString())
        assertEquals("https://companion.example/ws/companion", CompanionConfig.websocketUrl(base).toString())
    }

    @Test
    fun composerAcceptsOnlyExactAllowedPhrases() {
        assertEquals(CompanionApp.WHATSAPP, CompanionApp.fromComposerText("open WhatsApp"))
        assertEquals(CompanionApp.YOUTUBE, CompanionApp.fromComposerText(" OPEN YOUTUBE "))
        assertEquals(CompanionApp.SETTINGS, CompanionApp.fromComposerText("open Settings"))
        assertNull(CompanionApp.fromComposerText("open Gmail"))
        assertNull(CompanionApp.fromComposerText("open WhatsApp and send a message"))
    }
}
