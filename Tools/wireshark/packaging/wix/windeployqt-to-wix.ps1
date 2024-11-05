# windeployqt-to-wix
#
# Windeployqt-to-wix - Convert the output of windeployqt to an equivalent set of
# Wix file and component statements.
#
# Copyright 2016 Michael Mann
#
# Wireshark - Network traffic analyzer
# By Gerald Combs <gerald@wireshark.org>
# Copyright 1998 Gerald Combs
#
# SPDX-License-Identifier: GPL-2.0-or-later

#requires -version 2

<#
.SYNOPSIS
Creates Wix components required for Qt packaging.

.DESCRIPTION
This script creates n Wix-compatible include file based on the output of
windeployqt. If Qt is present, version 5.3 or later is required.
Otherwise a dummy file will be created.

If building with Qt, QMake must be in your PATH.

.PARAMETER Executable
The path to a Qt application. It will be examined for dependent DLLs.

.PARAMETER FilePath
Output filename.

.INPUTS
-Executable Path to the Qt application.
-FilePath Output Wix include file.

.OUTPUTS
Wix file required to package supporting DLLs.

.EXAMPLE
C:\PS> .\windeployqt-to-wix.ps1 windeployqt.exe ..\..\staging\wireshark.exe qt-dll-manifest.wxs
#>

Param(
    [Parameter(Mandatory=$true, Position=0)]
    [String] $Executable,

    [Parameter(Position=1)]
    [String] $FilePath = "qt-dll-manifest.wxs"
)


try {
    $qtVersion = [version](qmake -query QT_VERSION)
    $wixComponents = "<Wix xmlns=`"http://schemas.microsoft.com/wix/2006/wi`">
<?include InputPaths.wxi ?>
"
    $wixComponents += @("<!-- Qt version " + $qtVersion ; "-->
")

    if ($qtVersion -lt "5.3") {
        Throw "Qt " + $qtVersion + " found. 5.3 or later is required."
    }

    # windeployqt lists translation files that it don't exist (e.g.
    # qtbase_ar.qm), so we handle those by hand.
    # https://bugreports.qt.io/browse/QTBUG-65974
    $wdqtList = windeployqt `
        --release `
        --no-compiler-runtime `
        --no-translations `
        --list relative `
        $Executable

    $dllPath = Split-Path -Parent $Executable

    $dllList = "   <Fragment>
     <DirectoryRef Id=`"INSTALLFOLDER`">
"
    $dirList = ""
    $currentDir = ""
    $startDirList = "   <Fragment>
     <DirectoryRef Id=`"INSTALLFOLDER`">
"
    $endDirList = "       </Directory>
     </DirectoryRef>
   </Fragment>
"
    $currentDirList = $startDirList

    $componentGroup = "   <Fragment>
      <ComponentGroup Id=`"CG.QtDependencies`">
"
    foreach ($entry in $wdqtList) {
        $dir = Split-Path -Parent $entry
        $wix_name = $entry -ireplace "[^a-z0-9]", "_"

        if ($dir) {
            if ($dir -ne $currentDir) {
                if ($currentDir -ne "") { # for everything but first directory found
                    $currentDirList += $endDirList

                    # Previous directory complete, add to list
                    $dirList += $currentDirList
                }

                $currentDirList = $startDirList + "       <Directory Id=`"dir$dir`" Name=`"$dir`">
    "

                $currentDir = $dir
            }

            $currentDirList += "           <Component Id=`"cmp$wix_name`" Guid=`"*`">
              <File Id=`"fil$wix_name`" KeyPath=`"yes`" Source=`"`$(var.Staging.Dir)\$entry`" />
           </Component>
"
            $componentGroup += "         <ComponentRef Id=`"cmp$wix_name`" />
"
        } else {
            $dllList += "       <Component Id=`"cmp$wix_name`" Guid=`"*`">
          <File Id=`"fil$wix_name`" KeyPath=`"yes`" Source=`"`$(var.Staging.Dir)\$entry`" />
       </Component>
"
            $componentGroup += "         <ComponentRef Id=`"cmp$wix_name`" />
"
        }
    }

    #finish up the last directory
    $currentDirList += $endDirList
    $dirList += $currentDirList

    $dllList += "     </DirectoryRef>
   </Fragment>
"
    $componentGroup += "      </ComponentGroup>
   </Fragment>
"

    $wixComponents += $dllList + $dirList + $componentGroup

    $wixComponents += @"
</Wix>
"@

}

catch {

    $wixComponents = "<?xml version=`"1.0`" encoding=`"utf-8`"?>
<Include>
<!--- Qt not configured -->
</Include>
"

}

Set-Content $FilePath @"
<?xml version=`"1.0`" encoding=`"utf-8`"?>
<!--
   Automatically generated by $($MyInvocation.MyCommand.Name)
-->
"@

Add-Content $FilePath $wixComponents
