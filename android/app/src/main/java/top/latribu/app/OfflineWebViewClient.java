package top.latribu.app;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.Uri;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import com.getcapacitor.Bridge;
import com.getcapacitor.BridgeWebViewClient;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class OfflineWebViewClient extends BridgeWebViewClient {
    private final Context context;
    private final OfflineRepository repository;
    private final String offlineHtml;

    public OfflineWebViewClient(Bridge bridge, Context context, OfflineRepository repository) {
        super(bridge);
        this.context = context;
        this.repository = repository;
        this.offlineHtml = buildOfflineHtml();
    }

    @Override
    public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
        String url = request.getUrl().toString();
        if (!"GET".equalsIgnoreCase(request.getMethod()) || !isOurUrl(request.getUrl())) {
            return super.shouldInterceptRequest(view, request);
        }

        WebResourceResponse cached = findCachedResponse(url);
        if (cached != null) return cached;

        if (isOnline()) return super.shouldInterceptRequest(view, request);

        if (request.isForMainFrame()) return offlinePageResponse();
        return emptyResourceResponse(url);
    }

    @Override
    public WebResourceResponse shouldInterceptRequest(WebView view, String url) {
        if (!isOurUrl(Uri.parse(url))) {
            return super.shouldInterceptRequest(view, url);
        }

        WebResourceResponse cached = findCachedResponse(url);
        if (cached != null) return cached;

        if (isOnline()) return super.shouldInterceptRequest(view, url);

        if (looksLikeMainFrame(url)) return offlinePageResponse();
        return emptyResourceResponse(url);
    }

    private boolean isOurUrl(Uri uri) {
        String host = uri.getHost();
        return host != null && isOurHost(host);
    }

    private boolean isOurHost(String host) {
        return host.equalsIgnoreCase("www.latribu.top") ||
               host.equalsIgnoreCase("latribu.top") ||
               host.equalsIgnoreCase("www.latribu.com") ||
               host.equalsIgnoreCase("latribu.com");
    }

    private boolean looksLikeMainFrame(String url) {
        String lower = url.toLowerCase();
        if (lower.endsWith(".css") || lower.endsWith(".js") ||
            lower.matches(".*\\.(png|jpg|jpeg|gif|webp|svg|ico|mp4|webm|mov|mp3|wav|ogg|m4a|pdf|zip|woff|woff2|ttf|eot)$")) {
            return false;
        }
        return lower.contains("/caminatas") || lower.contains("/profile") || lower.contains("/nuestra") ||
               lower.contains("/mision") || lower.contains("/oracion") || lower.contains("/terminos") ||
               lower.contains("/quienes-somos") || lower.contains("/gestor-fechas") ||
               lower.contains("/offline") || lower.endsWith("/") || lower.indexOf("/", 10) == -1;
    }

    private WebResourceResponse findCachedResponse(String url) {
        WebResourceResponse response = repository.responseFor(url);
        if (response != null) return response;

        if (url.contains("?")) {
            String withoutQuery = url.substring(0, url.indexOf('?'));
            response = repository.responseFor(withoutQuery);
            if (response != null) return response;
        }

        if (url.contains("#")) {
            String withoutFragment = url.substring(0, url.indexOf('#'));
            response = repository.responseFor(withoutFragment);
            if (response != null) return response;
            if (withoutFragment.contains("?")) {
                String clean = withoutFragment.substring(0, withoutFragment.indexOf('?'));
                response = repository.responseFor(clean);
                if (response != null) return response;
            }
        }

        if (url.endsWith("/")) {
            response = repository.responseFor(url.substring(0, url.length() - 1));
            if (response != null) return response;
        } else {
            response = repository.responseFor(url + "/");
            if (response != null) return response;
        }

        return null;
    }

    private WebResourceResponse offlinePageResponse() {
        InputStream stream = new ByteArrayInputStream(offlineHtml.getBytes(StandardCharsets.UTF_8));
        return new WebResourceResponse("text/html", "UTF-8", 200, "OK", null, stream);
    }

    private WebResourceResponse emptyResourceResponse(String url) {
        String mime = mimeForUrl(url);
        return new WebResourceResponse(mime, null, 200, "OK", null, new ByteArrayInputStream(new byte[0]));
    }

    private String mimeForUrl(String url) {
        String lower = url.toLowerCase();
        if (lower.endsWith(".css")) return "text/css";
        if (lower.endsWith(".js")) return "application/javascript";
        if (lower.endsWith(".png")) return "image/png";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
        if (lower.endsWith(".gif")) return "image/gif";
        if (lower.endsWith(".webp")) return "image/webp";
        if (lower.endsWith(".svg")) return "image/svg+xml";
        if (lower.endsWith(".mp4")) return "video/mp4";
        if (lower.endsWith(".webm")) return "video/webm";
        if (lower.endsWith(".mp3")) return "audio/mpeg";
        if (lower.endsWith(".wav")) return "audio/wav";
        if (lower.endsWith(".ogg")) return "audio/ogg";
        if (lower.endsWith(".m4a")) return "audio/mp4";
        return "application/octet-stream";
    }

    private String buildOfflineHtml() {
        return "<!doctype html><html lang=\"es\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\"><title>La Tribu sin conexión</title><style>*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:2rem;background:#fff3e0;color:#242424;font-family:system-ui,sans-serif}.card{width:min(100%,32rem);padding:2rem;text-align:center;background:#fff;border-radius:1.5rem;box-shadow:0 1rem 3rem #0002}button{padding:.85rem 1.25rem;border:0;border-radius:2rem;background:#ff8c00;color:#fff;font-weight:700}</style></head><body><main class=\"card\"><h1>Sin conexión</h1><p>Esta página no está disponible sin Internet o todavía no fue descargada para uso offline.</p><p style=font-size:.8rem;word-break:break-all;color:#666 id=url></p><button type=\"button\" onclick=\"location.reload()\">Volver a intentar</button></main><script>document.getElementById('url').textContent=location.href</script></body></html>";
    }

    @Override
    public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
        if (handleError(view, request.getUrl().toString())) return;
        super.onReceivedError(view, request, error);
    }

    @Override
    public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
        if (handleError(view, failingUrl)) return;
        super.onReceivedError(view, errorCode, description, failingUrl);
    }

    @Override
    public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse errorResponse) {
        if (handleError(view, request.getUrl().toString())) return;
        super.onReceivedHttpError(view, request, errorResponse);
    }

    private boolean handleError(WebView view, String url) {
        if (url == null) return false;
        Uri uri = Uri.parse(url);
        if (!isOurUrl(uri)) return false;
        String html = repository.cachedPage(url);
        if (html == null) html = findCachedPageVariant(url);
        if (html == null) html = offlineHtml;
        final String content = html;
        view.post(() -> view.loadDataWithBaseURL(url, content, "text/html", "UTF-8", url));
        return true;
    }

    private String findCachedPageVariant(String url) {
        String[] variants = { url, url.contains("?") ? url.substring(0, url.indexOf('?')) : url };
        for (String variant : variants) {
            String html = repository.cachedPage(variant);
            if (html != null) return html;
            if (variant.endsWith("/")) {
                html = repository.cachedPage(variant.substring(0, variant.length() - 1));
            } else {
                html = repository.cachedPage(variant + "/");
            }
            if (html != null) return html;
        }
        return null;
    }

    private boolean isOnline() {
        ConnectivityManager manager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        Network network = manager.getActiveNetwork();
        if (network == null) return false;
        NetworkCapabilities capabilities = manager.getNetworkCapabilities(network);
        return capabilities != null && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
    }
}
