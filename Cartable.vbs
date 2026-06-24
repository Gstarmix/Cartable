Option Explicit
Dim fso, sh, scriptDir, gui, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
gui = scriptDir & "\_scripts\cartable_gui.py"
sh.CurrentDirectory = scriptDir
cmd = "pythonw.exe """ & gui & """"
sh.Run cmd, 0, False