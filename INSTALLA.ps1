# SO.MI.CA. S.p.A. - Gestionale Acquisizioni - Installer
# Eseguire come Amministratore

param([string]$InstallPath = "$env:LOCALAPPDATA\SoMiCa")

Write-Host ""
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "  SO.MI.CA. S.p.A. - Gestionale Acquisizioni" -ForegroundColor White
Write-Host "  Installazione in corso..." -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Blue
Write-Host ""

# Crea cartella installazione
if (!(Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

# Copia i file
Write-Host "  Copia file in $InstallPath..." -ForegroundColor Gray
Copy-Item -Path "$PSScriptRoot\*" -Destination $InstallPath -Recurse -Force

# Crea collegamento desktop
$DesktopPath = [System.Environment]::GetFolderPath("CommonDesktopDirectory")
$ShortcutPath = "$DesktopPath\SO.MI.CA. Gestionale.lnk"
$IconPath = "$InstallPath\static\img\icon.ico"
$ExePath = "$InstallPath\SoMiCa_Gestionale.exe"

# Controlla se esiste l'exe, altrimenti punta al .bat
if (!(Test-Path $ExePath)) {
    $ExePath = "$InstallPath\AVVIA.bat"
}

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $ExePath
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.IconLocation = $IconPath
$Shortcut.Description = "SO.MI.CA. S.p.A. - Gestionale Richieste di Acquisizione"
$Shortcut.Save()

Write-Host "  Collegamento desktop creato!" -ForegroundColor Green

# Crea anche collegamento nella barra delle applicazioni (Start Menu)
$StartMenuPath = [System.Environment]::GetFolderPath("CommonPrograms")
$StartMenuFolder = "$StartMenuPath\SO.MI.CA."
if (!(Test-Path $StartMenuFolder)) {
    New-Item -ItemType Directory -Path $StartMenuFolder -Force | Out-Null
}
$StartShortcutPath = "$StartMenuFolder\SO.MI.CA. Gestionale.lnk"
$Shortcut2 = $WshShell.CreateShortcut($StartShortcutPath)
$Shortcut2.TargetPath = $ExePath
$Shortcut2.WorkingDirectory = $InstallPath
$Shortcut2.IconLocation = $IconPath
$Shortcut2.Description = "SO.MI.CA. S.p.A. - Gestionale Richieste di Acquisizione"
$Shortcut2.Save()

Write-Host "  Collegamento Start Menu creato!" -ForegroundColor Green
Write-Host ""
Write-Host "  Installazione completata!" -ForegroundColor Green
Write-Host "  Trovi l'icona sul Desktop e nel menu Start." -ForegroundColor White
Write-Host ""
pause
