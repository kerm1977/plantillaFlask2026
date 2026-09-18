// ══ BLINDADO — RASTREO GPS WIDGET ══
// Servicio en primer plano: transmite el GPS del coordinador SIEMPRE,
// aunque la app esté cerrada o la pantalla apagada. Solo se apaga con
// Detener, o si el servidor responde sesión terminada/eliminada (410/404).
package top.latribu.gps;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.location.GnssStatus;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import org.json.JSONObject;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class GpsService extends Service implements LocationListener {
    public static volatile boolean corriendo = false;
    public static volatile int puntos = 0;
    public static volatile float ultimaAcc = -1;
    public static volatile int satUsados = 0;
    public static volatile int satTotal = 0;
    public static volatile int totalServidor = -1;
    public static volatile String evento = "";
    private static final String CHANNEL = "rk_gps_channel";
    private static final int NOTIF_ID = 7712;

    private LocationManager lm;
    private String pingUrl;
    private Location ultima;
    private GnssStatus.Callback gnssCb;
    private final Handler hb = new Handler(Looper.getMainLooper());
    private final Runnable heartbeat = new Runnable() {
        @Override public void run() {
            enviar(ultima);
            consultarInfo();
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
        getSharedPreferences("rk", MODE_PRIVATE).edit()
                .putBoolean("activo", true)
                .putString("ping_url", pingUrl)
                .apply();
        crearCanal();
        Notification notif = new Notification.Builder(this, CHANNEL)
                .setContentTitle("Rastreo GPS — La Tribu")
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
            stopSelf();
            return START_NOT_STICKY;
        }
        lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        boolean fina = checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
        if (fina && lm != null) {
            lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, 10000, 5, this, Looper.getMainLooper());
            lm.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 10000, 5, this, Looper.getMainLooper());
            gnssCb = new GnssStatus.Callback() {
                @Override public void onSatelliteStatusChanged(GnssStatus st) {
                    satTotal = st.getSatelliteCount();
                    int u = 0;
                    for (int i = 0; i < satTotal; i++) if (st.usedInFix(i)) u++;
                    satUsados = u;
                }
            };
            lm.registerGnssStatusCallback(gnssCb);
            ultima = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            if (ultima == null) ultima = lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
        }
        consultarInfo();
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
                    stopSelf();
                }
            } catch (Exception ignored) {}
        }).start();
    }

    // Consulta /info para saber el nombre de la sesión y el total en el
    // servidor; si la sesión ya no está activa el servicio se apaga solo.
    private void consultarInfo() {
        if (pingUrl == null) return;
        new Thread(() -> {
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(pingUrl + "/info").openConnection();
                c.setConnectTimeout(15000);
                c.setReadTimeout(15000);
                if (c.getResponseCode() == 200) {
                    java.io.InputStream in = c.getInputStream();
                    byte[] buf = new byte[4096];
                    int n = in.read(buf);
                    in.close();
                    JSONObject j = new JSONObject(new String(buf, 0, Math.max(n, 0), StandardCharsets.UTF_8));
                    if (!j.optBoolean("active", false)) { stopSelf(); return; }
                    totalServidor = j.optInt("total", -1);
                    String ev = j.optString("evento", "");
                    if (!ev.isEmpty() && !ev.equals("null")) evento = ev;
                }
                c.disconnect();
            } catch (Exception ignored) {}
        }).start();
    }

    private void crearCanal() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager m = getSystemService(NotificationManager.class);
            if (m != null) {
                m.createNotificationChannel(new NotificationChannel(CHANNEL,
                        "Rastreo GPS", NotificationManager.IMPORTANCE_LOW));
            }
        }
    }

    @Override
    public void onDestroy() {
        corriendo = false;
        getSharedPreferences("rk", MODE_PRIVATE).edit().putBoolean("activo", false).apply();
        hb.removeCallbacksAndMessages(null);
        if (lm != null) {
            lm.removeUpdates(this);
            if (gnssCb != null) lm.unregisterGnssStatusCallback(gnssCb);
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
