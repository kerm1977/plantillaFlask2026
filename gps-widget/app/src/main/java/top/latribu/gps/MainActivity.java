// ══ BLINDADO — RASTREO GPS WIDGET ══
// Pantalla única y mínima: estado en escucha, token del coordinador,
// botón Iniciar/Detener. Todo lo demás corre en el servicio de fondo.
package top.latribu.gps;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends Activity {
    private static final int REQ = 42;
    private static final int NARANJA = Color.rgb(245, 140, 31);
    private EditText tokenInput;
    private TextView estado;
    private TextView detalle;
    private Button btn;
    private String pendienteUrl;
    private final Handler h = new Handler(Looper.getMainLooper());
    private final Runnable refresco = new Runnable() {
        @Override public void run() {
            pintar();
            h.postDelayed(this, 2000);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        SharedPreferences p = getSharedPreferences("rk", MODE_PRIVATE);

        TextView titulo = texto("Rastreo GPS — La Tribu", 22, true, Color.BLACK);
        estado = texto("En espera", 18, true, Color.GRAY);
        detalle = texto("", 14, false, Color.DKGRAY);
        tokenInput = new EditText(this);
        tokenInput.setHint("Token del coordinador");
        tokenInput.setSingleLine(true);
        tokenInput.setText(p.getString("token", ""));
        btn = new Button(this);
        btn.setText("Iniciar");
        btn.setOnClickListener(v -> alternar());
        TextView nota = texto("Pegá el token que aparece en el panel de Rastreo en Vivo "
                + "(\"Token del widget GPS\"). Al iniciar, la ubicación se transmite "
                + "siempre, aunque cierres esta app.", 12, false, Color.GRAY);

        LinearLayout lay = new LinearLayout(this);
        lay.setOrientation(LinearLayout.VERTICAL);
        lay.setGravity(Gravity.CENTER_HORIZONTAL);
        lay.setPadding(48, 60, 48, 48);
        lay.addView(titulo);
        lay.addView(espacio(24));
        lay.addView(estado);
        lay.addView(espacio(8));
        lay.addView(detalle);
        lay.addView(espacio(32));
        lay.addView(tokenInput, ancho());
        lay.addView(espacio(24));
        lay.addView(btn, ancho());
        lay.addView(espacio(24));
        lay.addView(nota);
        setContentView(lay);
        pintar();
    }

    private void alternar() {
        if (GpsService.corriendo) {
            stopService(new Intent(this, GpsService.class));
            GpsService.corriendo = false;
            GpsService.puntos = 0;
            getSharedPreferences("rk", MODE_PRIVATE).edit().putBoolean("activo", false).apply();
            pintar();
            return;
        }
        String t = tokenInput.getText().toString().trim();
        if (t.isEmpty()) {
            Toast.makeText(this, "Pegá el token del coordinador primero", Toast.LENGTH_LONG).show();
            return;
        }
        getSharedPreferences("rk", MODE_PRIVATE).edit().putString("token", t).apply();
        pendienteUrl = t.startsWith("http") ? t
                : "https://www.latribu.top/api/rastreo/ping/" + t;
        pedirPermisosYArrancar();
    }

    // Pide los permisos por etapas: primero ubicación de primer plano y
    // notificaciones, DESPUÉS ubicación en segundo plano (Android 11+ exige
    // pedirla aparte o la deniega automáticamente). Luego arranca el servicio.
    private void pedirPermisosYArrancar() {
        List<String> faltan = new ArrayList<>();
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            faltan.add(Manifest.permission.ACCESS_FINE_LOCATION);
            faltan.add(Manifest.permission.ACCESS_COARSE_LOCATION);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            faltan.add(Manifest.permission.POST_NOTIFICATIONS);
        }
        if (faltan.isEmpty() && Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q
                && checkSelfPermission(Manifest.permission.ACCESS_BACKGROUND_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            faltan.add(Manifest.permission.ACCESS_BACKGROUND_LOCATION);
        }
        if (faltan.isEmpty()) arrancar();
        else requestPermissions(faltan.toArray(new String[0]), REQ);
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] res) {
        super.onRequestPermissionsResult(code, perms, res);
        if (code == REQ && pendienteUrl != null) pedirPermisosYArrancar();
    }

    private void arrancar() {
        Intent i = new Intent(this, GpsService.class);
        i.putExtra("ping_url", pendienteUrl);
        pendienteUrl = null;
        startForegroundService(i);
        pintar();
    }

    private void pintar() {
        if (GpsService.corriendo) {
            estado.setText("GPS activado — en escucha siempre");
            estado.setTextColor(NARANJA);
            detalle.setText("Ubicación lista para trabajar · Puntos enviados: " + GpsService.puntos);
            btn.setText("Detener");
        } else {
            estado.setText("En espera — detenido");
            estado.setTextColor(Color.GRAY);
            detalle.setText("");
            btn.setText("Iniciar");
        }
    }

    private TextView texto(String t, float sp, boolean bold, int color) {
        TextView v = new TextView(this);
        v.setText(t);
        v.setTextSize(sp);
        v.setTextColor(color);
        v.setGravity(Gravity.CENTER);
        if (bold) v.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        return v;
    }

    private android.view.View espacio(int alto) {
        android.view.View v = new android.view.View(this);
        v.setLayoutParams(new LinearLayout.LayoutParams(1, alto));
        return v;
    }

    private LinearLayout.LayoutParams ancho() {
        return new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
    }

    @Override protected void onResume() {
        super.onResume();
        h.post(refresco);
    }

    @Override protected void onPause() {
        h.removeCallbacks(refresco);
        super.onPause();
    }
}
