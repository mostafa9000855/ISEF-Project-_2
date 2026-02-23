; SmartAI Windows Installer Script (NSIS)
; Build with: makensis smartai-installer.nsi

!include "MUI2.nsh"
!include "x64.nsh"

; Installer Settings
Name "SmartAI v1.0.0"
OutFile "SmartAI-Setup-1.0.0.exe"
InstallDir "$PROGRAMFILES\SmartAI"
InstallDirRegKey HKLM "Software\SmartAI" "InstallLocation"

; Request admin privileges
RequestExecutionLevel admin

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ==================== INSTALLER SECTIONS ====================

Section "Install"
    SetOverwrite try
    SetOutPath "$INSTDIR"
    
    ; Copy main application files
    File "dist\SmartAI-Setup.exe"
    File "package.json"
    File "README.md"
    
    ; Copy source files (C++, Python, Electron)
    SetOutPath "$INSTDIR\src\cpp"
    File /r "src\cpp\*"
    
    SetOutPath "$INSTDIR\src\python"
    File /r "src\python\*"
    
    SetOutPath "$INSTDIR\src\electron"
    File /r "src\electron\*"
    
    ; Copy database schema and dependencies
    SetOutPath "$INSTDIR\database"
    File /r "database\*"
    
    ; Copy assets
    SetOutPath "$INSTDIR\assets"
    File /r "assets\*"
    
    ; Copy compiled binaries (from build directory)
    SetOutPath "$INSTDIR\bin"
    File "build\Release\core_engine.exe"
    
    ; Create application shortcuts
    CreateDirectory "$SMPROGRAMS\SmartAI"
    CreateShortcut "$SMPROGRAMS\SmartAI\SmartAI.lnk" "$INSTDIR\SmartAI.exe"
    CreateShortcut "$SMPROGRAMS\SmartAI\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortcut "$DESKTOP\SmartAI.lnk" "$INSTDIR\SmartAI.exe"
    
    ; Write registry entries
    WriteRegStr HKLM "Software\SmartAI" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\SmartAI" "Version" "1.0.0"
    WriteRegStr HKLM "Software\SmartAI" "DisplayName" "SmartAI"
    WriteRegStr HKLM "Software\SmartAI" "DisplayVersion" "1.0.0"
    WriteRegStr HKLM "Software\SmartAI" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\SmartAI" "Publisher" "SmartAI Team"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Set file permissions for core engine
    AccessControl::GrantOnFile "$INSTDIR\bin\core_engine.exe" "(BU)" "GenericRead + GenericExecute"
    
    ; Register as Windows service (optional)
    ExecWait 'sc create SmartAI binPath= "$INSTDIR\bin\core_engine.exe" start= auto'
    ExecWait 'net start SmartAI'
    
    ; Set auto-start registry entry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "SmartAI" "$INSTDIR\SmartAI.exe"
    
    MessageBox MB_OK "SmartAI has been installed successfully!$\n$\nThe application will start automatically on next boot."
SectionEnd

; ==================== UNINSTALLER ====================

Section "Uninstall"
    ; Stop and remove service
    ExecWait 'net stop SmartAI'
    ExecWait 'sc delete SmartAI'
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\SmartAI"
    DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "SmartAI"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\SmartAI\SmartAI.lnk"
    Delete "$SMPROGRAMS\SmartAI\Uninstall.lnk"
    Delete "$DESKTOP\SmartAI.lnk"
    RMDir "$SMPROGRAMS\SmartAI"
    
    ; Remove files and folders
    RMDir /r "$INSTDIR"
    
    MessageBox MB_OK "SmartAI has been uninstalled."
SectionEnd

; ==================== INSTALLER ATTRIBUTES ====================

Section -post
    SetShellVarContext all
SectionEnd

; Version info
VIProductVersion "1.0.0.0"
VIAddVersionKey /LANG=1033 "ProductName" "SmartAI"
VIAddVersionKey /LANG=1033 "FileVersion" "1.0.0"
VIAddVersionKey /LANG=1033 "ProductVersion" "1.0.0"
VIAddVersionKey /LANG=1033 "CompanyName" "SmartAI Team"
VIAddVersionKey /LANG=1033 "LegalCopyright" "2024 SmartAI Team"
VIAddVersionKey /LANG=1033 "FileDescription" "SmartAI - Enterprise Cybersecurity Operations Center"
