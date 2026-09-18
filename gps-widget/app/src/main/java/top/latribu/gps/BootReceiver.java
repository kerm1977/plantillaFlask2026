// ══ BLINDADO — RASTREO GPS WIDGET ══
// Si el teléfono se reinicia y el rastreo estaba activo, vuelve a arrancar solo.
package top.latribu.gps;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        if (!Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) return;
        SharedPreferences p = ctx.getSharedPreferences("rk", Context.MODE_PRIVATE);
        String url = p.getString("ping_url", null);
        if (p.getBoolean("activo", false) && url != null) {
            Intent i = new Intent(ctx, GpsService.class);
            i.putExtra("ping_url", url);
            ctx.startForegroundService(i);
        }
    }
}
