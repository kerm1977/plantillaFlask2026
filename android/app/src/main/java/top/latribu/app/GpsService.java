// ══ BLINDADO — RASTREO EN VIVO ══
// Código probado y estable. NO modificar sin revisar el flujo completo.
// Servicio en primer plano: transmite el GPS del coordinador aunque la app
// esté minimizada o la pantalla apagada. Solo se detiene con stopGps()
// o cuando el servidor responde que la sesión ya no está activa (410/404).
package top.latribu.app;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import androidx.core.app.NotificationCompat;
import androidx.core.content.ContextCompat;
import org.json.JSONObject;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class GpsService extends Service implements LocationListener {
    public static volatile boolean corriendo = false;
    public static volatile int puntos = 0;
    public static volatile float ultimaAcc = -1;
    private static final String CHANNEL = "rk_gps_channel";
    private static final int NOTIF_ID = 7712;

    private LocationManager lm;
    private String pingUrl;
    private Location ultima;
    private final Handler hb = new Handler(Looper.getMainLooper());
    private final Runnable heartbeat = new Runnable() {
        @Override public void run() {
            enviar(ultima);
            hb.postDelayed(this, 30000);
        }
    };

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null || intent.getStringExtra("ping_url") == null) {
            stopSelf();
            return START_NOT_STICKY;
        }
        pingUrl = intent.getStringExtra("ping_url");
        corriendo = true;
        crearCanal();
        Notification notif = new NotificationCompat.Builder(this, CHANNEL)
                .setContentTitle("La Tribu — Rastreo en vivo")
                .setContentText("Transmitiendo la ubicación del grupo")
                .setSmallIcon(android.R.drawable.ic_menu_mylocation)
                .setContentIntent(PendingIntent.getActivity(this, 0,
                        new Intent(this, MainActivity.class), PendingIntent.FLAG_IMMUTABLE))
                .setOngoing(true)
                .build();
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(NOTIF_ID, notif, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION);
            } else {
                startForeground(NOTIF_ID, notif);
            }
        } catch (Exception e) {
            // Sin permiso de ubicación no hay nada que transmitir
            stopSelf();
            return START_NOT_STICKY;
        }
        lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        boolean fina = ContextCompat.checkSelfPermission(this,
                Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
        if (fina && lm != null) {
            lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, 10000, 5, this, Looper.getMainLooper());
            lm.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 10000, 5, this, Looper.getMainLooper());
            ultima = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            if (ultima == null) ultima = lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
        }
        hb.postDelayed(heartbeat, 30000);
        return START_STICKY;
    }

    @Override
    public void onLocationChanged(Location loc) {
        ultima = loc;
        enviar(loc);
    }

    @Override public void onProviderEnabled(String p) {}
    @Override public void onProviderDisabled(String p) {}
    @Override public void onStatusChanged(String p, int s, Bundle b) {}

    private void enviar(Location loc) {
        if (loc == null || pingUrl == null) return;
        final double lat = loc.getLatitude();
        final double lng = loc.getLongitude();
        final float acc = loc.hasAccuracy() ? loc.getAccuracy() : -1;
        new Thread(() -> {
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(pingUrl).openConnection();
                c.setRequestMethod("POST");
                c.setRequestProperty("Content-Type", "application/json");
                c.setDoOutput(true);
                c.setConnectTimeout(15000);
                c.setReadTimeout(15000);
                JSONObject j = new JSONObject();
                j.put("lat", lat);
                j.put("lng", lng);
                if (acc >= 0) j.put("acc", acc);
                OutputStream o = c.getOutputStream();
                o.write(j.toString().getBytes(StandardCharsets.UTF_8));
                o.close();
                int code = c.getResponseCode();
                c.disconnect();
                if (code == 200) {
                    puntos++;
                    ultimaAcc = acc;
                } else if (code == 410 || code == 404) {
                    stopSelf(); // sesión detenida o eliminada: el servicio se apaga solo
                }
            } catch (Exception ignored) {}
        }).start();
    }

    private void crearCanal() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager m = getSystemService(NotificationManager.class);
            if (m != null) {
                m.createNotificationChannel(new NotificationChannel(CHANNEL,
                        "Rastreo en vivo", NotificationManager.IMPORTANCE_LOW));
            }
        }
    }

    @Override
    public void onDestroy() {
        corriendo = false;
        hb.removeCallbacksAndMessages(null);
        if (lm != null) lm.removeUpdates(this);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
