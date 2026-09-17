package top.latribu.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.StatFs;
import android.webkit.CookieManager;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.ConnectException;
import java.net.HttpURLConnection;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONArray;
import org.json.JSONObject;

public class OfflineRepository {
    private final Context context;
    private final WebView webView;
    private final File directory;
    private final SharedPreferences metadata;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    public OfflineRepository(Context context, WebView webView) {
        this.context = context;
        this.webView = webView;
        this.directory = new File(context.getFilesDir(), "offline_web");
        this.directory.mkdirs();
        this.metadata = context.getSharedPreferences("offline_repository", Context.MODE_PRIVATE);
    }

    public void startDownload() {
        executor.execute(() -> {
            List<JSONObject> failures = new ArrayList<>();
            try {
                if (!isOnline()) throw new UnknownHostException("Conectá el dispositivo a Internet para iniciar o reanudar la descarga offline");
                JSONObject manifest = getJson("https://www.latribu.top/api/offline/manifest");
                String newVersion = manifest.optString("version", "0");
                String currentVersion = metadata.getString("manifest_version", "");
                if (currentVersion.equals(newVersion)) {
                    emit("OFFLINE_UP_TO_DATE", new JSONObject().put("message", "La copia offline ya está actualizada (versión " + newVersion + ")"));
                    return;
                }
                JSONArray pages = manifest.getJSONArray("pages");
                JSONArray files = manifest.getJSONArray("files");
                long totalBytes = manifest.optLong("total_bytes", 0);
                long available = new StatFs(directory.getAbsolutePath()).getAvailableBytes();
                if (available < totalBytes) throw new Exception("Espacio insuficiente. Disponible: " + available + " bytes; requerido: " + totalBytes + " bytes");
                int total = pages.length() + files.length();
                int completed = 0;
                int reused = 0;
                long downloadedBytes = 0;
                emit("OFFLINE_DOWNLOAD_START", new JSONObject().put("total", total).put("totalBytes", totalBytes).put("version", newVersion));
                String pageVersion = "page-" + newVersion;
                for (int i = 0; i < pages.length(); i++) {
                    String path = pages.getString(i);
                    String url = absolute(path);
                    try {
                        if (isCurrent(url, pageVersion)) {
                            reused++;
                            emitLog("info", "Ya descargado, se conserva: " + path);
                        } else {
                            emitLog("info", "Descargando página: " + path);
                            download(url, pageVersion);
                            emitLog("success", "Guardada: " + path);
                        }
                    } catch (Exception error) {
                        if (isConnectivityError(error)) throw error;
                        failures.add(failure(path, error));
                        emitLog("error", "Error " + error.getMessage() + ": " + path);
                    }
                    completed++;
                    emitProgress(completed, total, downloadedBytes, totalBytes, reused, failures);
                }
                for (int i = 0; i < files.length(); i++) {
                    JSONObject item = files.getJSONObject(i);
                    String path = item.getString("url");
                    String version = item.getString("version");
                    long size = item.optLong("size", 0);
                    String url = absolute(path);
                    try {
                        if (isCurrent(url, version)) {
                            reused++;
                            downloadedBytes += size;
                            emitLog("info", "Ya descargado, se conserva: " + path);
                        } else {
                            emitLog("info", "Descargando: " + path);
                            download(url, version);
                            downloadedBytes += size;
                            emitLog("success", "Guardado: " + path);
                        }
                    } catch (Exception error) {
                        if (isConnectivityError(error)) throw error;
                        failures.add(failure(path, error));
                        emitLog("error", "Error " + error.getMessage() + ": " + path);
                    }
                    completed++;
                    emitProgress(completed, total, downloadedBytes, totalBytes, reused, failures);
                }
                metadata.edit().putString("last_state", new JSONObject().put("completed", completed).put("total", total).put("downloadedBytes", downloadedBytes).put("totalBytes", totalBytes).put("reused", reused).put("failures", new JSONArray(failures)).put("status", failures.isEmpty() ? "completed" : "completed_with_errors").toString()).putString("manifest_version", newVersion).apply();
                emit("OFFLINE_DOWNLOAD_COMPLETE", new JSONObject().put("completed", completed).put("total", total).put("downloadedBytes", downloadedBytes).put("totalBytes", totalBytes).put("reused", reused).put("failures", new JSONArray(failures)).put("version", newVersion));
            } catch (Exception error) {
                JSONObject data;
                try {
                    String previous = metadata.getString("last_state", "");
                    data = previous.isEmpty() ? new JSONObject() : new JSONObject(previous);
                    data.put("status", isConnectivityError(error) ? "paused_no_connection" : "interrupted");
                    data.put("error", isConnectivityError(error) ? "La descarga se pausó porque se perdió la conexión o el DNS. Conectate y pulsá nuevamente para continuar." : error.getMessage());
                    metadata.edit().putString("last_state", data.toString()).apply();
                } catch (Exception ignored) {
                    data = new JSONObject();
                }
                emit("OFFLINE_DOWNLOAD_ERROR", data);
            }
        });
    }

    public WebResourceResponse responseFor(String url) {
        try {
            File file = fileFor(url);
            if (!file.isFile()) return null;
            String mime = metadata.getString("mime:" + hash(url), "application/octet-stream");
            return new WebResourceResponse(mime, "UTF-8", new FileInputStream(file));
        } catch (Exception error) {
            return null;
        }
    }

    public String state() {
        return metadata.getString("last_state", "");
    }

    public String cachedPage(String url) {
        try {
            String storedUrl = url;
            File file = fileFor(storedUrl);
            if (!file.isFile() && url.contains("?")) {
                storedUrl = url.substring(0, url.indexOf('?'));
                file = fileFor(storedUrl);
            }
            if (!file.isFile()) return null;
            String mime = metadata.getString("mime:" + hash(storedUrl), "");
            if (!mime.contains("html") && !storedUrl.endsWith("/")) return null;
            try (InputStream input = new FileInputStream(file)) {
                return new String(input.readAllBytes(), StandardCharsets.UTF_8);
            }
        } catch (Exception error) {
            return null;
        }
    }

    private JSONObject getJson(String url) throws Exception {
        HttpURLConnection connection = open(url);
        if (connection.getResponseCode() != 200) throw new Exception("HTTP " + connection.getResponseCode() + " al obtener inventario");
        try (InputStream input = connection.getInputStream()) {
            return new JSONObject(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        } finally {
            connection.disconnect();
        }
    }

    private void download(String url, String version) throws Exception {
        HttpURLConnection connection = open(url);
        int status = connection.getResponseCode();
        if (status != 200) throw new Exception("HTTP " + status);
        File target = fileFor(url);
        File temporary = new File(target.getAbsolutePath() + ".part");
        try (InputStream input = connection.getInputStream(); FileOutputStream output = new FileOutputStream(temporary)) {
            byte[] buffer = new byte[1024 * 256];
            int count;
            while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
            output.getFD().sync();
        } finally {
            connection.disconnect();
        }
        if (target.exists() && !target.delete()) throw new Exception("No se pudo reemplazar el archivo local");
        if (!temporary.renameTo(target)) throw new Exception("No se pudo finalizar el archivo local");
        metadata.edit().putString("version:" + hash(url), version).putString("mime:" + hash(url), mimeFor(url, connection.getContentType())).apply();
    }

    private boolean isOnline() {
        ConnectivityManager manager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        Network network = manager.getActiveNetwork();
        if (network == null) return false;
        NetworkCapabilities capabilities = manager.getNetworkCapabilities(network);
        return capabilities != null && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);
    }

    private boolean isConnectivityError(Throwable error) {
        Throwable current = error;
        while (current != null) {
            if (current instanceof UnknownHostException || current instanceof ConnectException || current instanceof SocketTimeoutException) return true;
            current = current.getCause();
        }
        return false;
    }

    private HttpURLConnection open(String url) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setConnectTimeout(20000);
        connection.setReadTimeout(120000);
        connection.setRequestProperty("Accept-Encoding", "identity");
        String cookies = CookieManager.getInstance().getCookie(url);
        if (cookies != null) connection.setRequestProperty("Cookie", cookies);
        return connection;
    }

    private boolean isCurrent(String url, String version) throws Exception {
        return fileFor(url).isFile() && version.equals(metadata.getString("version:" + hash(url), ""));
    }

    private File fileFor(String url) throws Exception {
        return new File(directory, hash(url) + ".bin");
    }

    private String hash(String value) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
        StringBuilder result = new StringBuilder();
        for (byte item : digest) result.append(String.format("%02x", item));
        return result.toString();
    }

    private String absolute(String path) {
        return path.startsWith("http") ? path : "https://www.latribu.top" + path;
    }

    private String mimeFor(String url, String contentType) {
        if (contentType != null && !contentType.isBlank()) return contentType.split(";")[0];
        String lower = url.toLowerCase();
        if (lower.endsWith(".html")) return "text/html";
        if (lower.endsWith(".css")) return "text/css";
        if (lower.endsWith(".js")) return "application/javascript";
        if (lower.matches(".*\\.(png|jpg|jpeg|gif|webp)$")) return "image/" + (lower.endsWith(".jpg") ? "jpeg" : lower.substring(lower.lastIndexOf('.') + 1));
        if (lower.matches(".*\\.(mp4|webm|mov)$")) return "video/" + lower.substring(lower.lastIndexOf('.') + 1);
        if (lower.matches(".*\\.(mp3|wav|ogg|m4a)$")) return "audio/" + lower.substring(lower.lastIndexOf('.') + 1);
        return "application/octet-stream";
    }

    private JSONObject failure(String url, Exception error) throws Exception {
        return new JSONObject().put("url", url).put("error", error.getMessage());
    }

    private void emitProgress(int completed, int total, long downloadedBytes, long totalBytes, int reused, List<JSONObject> failures) throws Exception {
        JSONObject data = new JSONObject().put("completed", completed).put("total", total).put("downloadedBytes", downloadedBytes).put("totalBytes", totalBytes).put("reused", reused).put("failures", new JSONArray(failures));
        metadata.edit().putString("last_state", data.put("status", "running").toString()).apply();
        emit("OFFLINE_DOWNLOAD_PROGRESS", data);
    }

    private void emitLog(String level, String message) throws Exception {
        emit("OFFLINE_DOWNLOAD_LOG", new JSONObject().put("level", level).put("message", message));
    }

    private void emit(String type, JSONObject data) {
        try {
            JSONObject detail = new JSONObject(data.toString()).put("type", type);
            String script = "window.dispatchEvent(new CustomEvent('latribuNativeOffline',{detail:" + detail + "}));";
            webView.post(() -> webView.evaluateJavascript(script, null));
        } catch (Exception ignored) {}
    }
}
