# LuaLaTeX build with fail-closed PDF/source checks. Pass --portable and/or --publish.
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    python scripts/build.py @args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }
