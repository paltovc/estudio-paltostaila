# Crea en el escritorio los accesos "Sala de edición" y "Sala de edición (red de la casa)".
# Se corre una vez por computador (instalar-estudio lo hace solo):  powershell -ExecutionPolicy Bypass -File accesos_escritorio.ps1
$motor = Split-Path -Parent $MyInvocation.MyCommand.Path
$escritorio = [Environment]::GetFolderPath('Desktop')
$ws = New-Object -ComObject WScript.Shell
foreach ($a in @(@('Sala de edición', 'sala.cmd', 'Mirar y editar los videos del Estudio Palto Style'),
                 @('Sala de edición (red de la casa)', 'sala_red.cmd', 'Igual, pero también se puede abrir desde otro aparato del mismo wifi'))) {
    $l = $ws.CreateShortcut((Join-Path $escritorio ($a[0] + '.lnk')))
    $l.TargetPath = Join-Path $motor $a[1]
    $l.WorkingDirectory = $motor
    $l.Description = $a[2]
    $l.IconLocation = "$env:SystemRoot\System32\imageres.dll,18"
    $l.WindowStyle = 7
    $l.Save()
    "acceso creado: " + $a[0]
}