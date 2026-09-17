package top.latribu.app;

import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkRequest;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.Toast;
import androidx.core.view.WindowCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private OfflineRepository offlineRepository;
    private OfflineWebViewClient offlineClient;
    private long updateDownloadId = -1;
    private Uri pendingUpdateUri;
    private ConnectivityManager connectivityManager;
    private final Handler syncHandler = new Handler(Looper.getMainLooper());
    private final BroadcastReceiver downloadReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            long id = intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1);
            if (id != updateDownloadId) return;
            DownloadManager manager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
            pendingUpdateUri = manager.getUriForDownloadedFile(id);
            if (pendingUpdateUri == null) {
                Toast.makeText(MainActivity.this, "La descarga de la actualización falló.", Toast.LENGTH_LONG).show();
                return;
            }
            openPendingUpdate();
        }
    };
    private final ConnectivityManager.NetworkCallback networkCallback = new ConnectivityManager.NetworkCallback() {
        @Override
        public void onAvailable(Network network) {
            if (!isFinishing() && !isDestroyed()) syncOfflineIfNeeded();
        }

        @Override
        public void onCapabilitiesChanged(Network network, NetworkCapabilities capabilities) {
            if (capabilities != null && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)) {
                if (!isFinishing() && !isDestroyed()) syncOfflineIfNeeded();
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        WindowCompat.setDecorFitsSystemWindows(getWindow(), true);
        super.onCreate(savedInstanceState);
        IntentFilter downloadFilter = new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) registerReceiver(downloadReceiver, downloadFilter, Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(downloadReceiver, downloadFilter);
        WebView webView = bridge.getWebView();
        offlineRepository = new OfflineRepository(this, webView);
        offlineClient = new OfflineWebViewClient(bridge, this, offlineRepository);
        bridge.setWebViewClient(offlineClient);
        webView.setWebViewClient(offlineClient);
        webView.addJavascriptInterface(new AppInfoBridge(this, offlineRepository), "LaTribuAndroid");
        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> startUpdateDownload(url, userAgent));
        connectivityManager = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N && connectivityManager != null) {
            connectivityManager.registerDefaultNetworkCallback(networkCallback);
        }
        if (!isOnline()) webView.post(() -> webView.loadUrl("https://www.latribu.top/"));
    }

    @Override
    public void onResume() {
        super.onResume();
        if (pendingUpdateUri != null && (Build.VERSION.SDK_INT < Build.VERSION_CODES.O || getPackageManager().canRequestPackageInstalls())) openPendingUpdate();
        if (bridge != null && offlineClient != null) {
            bridge.setWebViewClient(offlineClient);
            bridge.getWebView().setWebViewClient(offlineClient);
        }
        syncOfflineIfNeeded();
    }

    private void syncOfflineIfNeeded() {
        syncHandler.removeCallbacksAndMessages(null);
        syncHandler.postDelayed(() -> {
            if (offlineRepository == null) return;
            offlineRepository.startDownload();
        }, 2000);
    }

    private boolean isOnline() {
        ConnectivityManager manager = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        Network network = manager.getActiveNetwork();
        if (network == null) return false;
        NetworkCapabilities capabilities = manager.getNetworkCapabilities(network);
        return capabilities != null && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
    }

    private void startUpdateDownload(String url, String userAgent) {
        runOnUiThread(() -> {
            try {
                DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                String fileName = "LaTribu-update-" + System.currentTimeMillis() + ".apk";
                request.setMimeType("application/vnd.android.package-archive");
                if (userAgent != null && !userAgent.isEmpty()) request.addRequestHeader("User-Agent", userAgent);
                String cookies = CookieManager.getInstance().getCookie(url);
                if (cookies != null) request.addRequestHeader("Cookie", cookies);
                request.setTitle(fileName);
                request.setDescription("Descargando actualización de La Tribu");
                request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, fileName);
                request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                DownloadManager manager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                updateDownloadId = manager.enqueue(request);
                Toast.makeText(this, "Descarga iniciada. La Tribu seguirá abierta.", Toast.LENGTH_LONG).show();
            } catch (Exception error) {
                Toast.makeText(this, "No se pudo iniciar la descarga: " + error.getMessage(), Toast.LENGTH_LONG).show();
            }
        });
    }

    private void openPendingUpdate() {
        if (pendingUpdateUri == null) return;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && !getPackageManager().canRequestPackageInstalls()) {
            Intent settingsIntent = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + getPackageName()));
            startActivity(settingsIntent);
            Toast.makeText(this, "Autorizá instalar aplicaciones y regresá a La Tribu.", Toast.LENGTH_LONG).show();
            return;
        }
        Intent installIntent = new Intent(Intent.ACTION_VIEW);
        installIntent.setDataAndType(pendingUpdateUri, "application/vnd.android.package-archive");
        installIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(installIntent);
        pendingUpdateUri = null;
    }

    @Override
    public void onDestroy() {
        try {
            unregisterReceiver(downloadReceiver);
        } catch (Exception ignored) {}
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N && connectivityManager != null) {
            try {
                connectivityManager.unregisterNetworkCallback(networkCallback);
            } catch (Exception ignored) {}
        }
        super.onDestroy();
    }

    private static class AppInfoBridge {
        private final MainActivity activity;
        private final OfflineRepository repository;

        AppInfoBridge(MainActivity activity, OfflineRepository repository) {
            this.activity = activity;
            this.repository = repository;
        }

        @JavascriptInterface
        public int getVersionCode() {
            return 14;
        }

        @JavascriptInterface
        public String getVersionName() {
            return "2.3.0";
        }

        @JavascriptInterface
        public void downloadUpdate(String url) {
            activity.startUpdateDownload(url, activity.bridge.getWebView().getSettings().getUserAgentString());
        }

        @JavascriptInterface
        public void downloadAllOffline() {
            repository.startDownload();
        }

        @JavascriptInterface
        public String getOfflineState() {
            return repository.state();
        }
    }
}
