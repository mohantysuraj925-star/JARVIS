function triggerJarvisDownload(platform) {
    fetch('/api/track-download', { method: 'POST' }).catch(() => {});
    const targetUrl = '/get-package/' + platform;
    const a = document.createElement('a');
    a.href = targetUrl;
    a.download = (platform === 'windows') ? 'JARVIS_Installer.exe' : 'JARVIS_Mobile.apk';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => a.remove(), 300);
    if (/Android|iPhone|iPad/i.test(navigator.userAgent)) {
        window.location.assign(targetUrl);
    }
}