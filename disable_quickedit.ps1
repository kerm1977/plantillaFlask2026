# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# Desactiva el "modo QuickEdit" de la consola actual: un clic accidental
# dentro de la ventana ya no la deja en "Seleccionar" (lo cual congela el
# proceso hijo -p. ej. cloudflared o python- hasta presionar Escape).
$sig = @'
[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int nStdHandle);
[DllImport("kernel32.dll")] public static extern bool GetConsoleMode(IntPtr hConsoleHandle, out uint lpMode);
[DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr hConsoleHandle, uint dwMode);
'@
try {
    $type = Add-Type -MemberDefinition $sig -Name NativeConsole -Namespace Tribu -PassThru
    $STD_INPUT_HANDLE = -10
    $ENABLE_QUICK_EDIT_MODE = 0x0040
    $ENABLE_EXTENDED_FLAGS = 0x0080
    $handle = $type::GetStdHandle($STD_INPUT_HANDLE)
    [uint32]$mode = 0
    $type::GetConsoleMode($handle, [ref]$mode) | Out-Null
    $mode = $mode -band (-bnot $ENABLE_QUICK_EDIT_MODE)
    $mode = $mode -bor $ENABLE_EXTENDED_FLAGS
    $type::SetConsoleMode($handle, $mode) | Out-Null
} catch {
    # Si falla (p. ej. sin permisos), la consola sigue funcionando normal.
}
