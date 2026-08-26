<#
Convert an Office document to plain text WITHOUT python — Windows fallback.
Prefer convert.py when python3 exists; use this only when it doesn't.

Usage:  powershell -ExecutionPolicy Bypass -File convert.ps1 <input-file>   (text -> stdout)
Tries, in order: pandoc -> Word/PowerPoint/Excel COM (if Office installed) -> unzip+strip-tags.
Exit: 0 ok, 2 unsupported/missing, 3 no usable converter.
#>
param([Parameter(Mandatory=$true)][string]$InputFile)
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputFile)) { [Console]::Error.WriteLine("convert.ps1: file not found: $InputFile"); exit 2 }
$ext = ([IO.Path]::GetExtension($InputFile)).TrimStart('.').ToLower()
if ($ext -notin @('docx','pptx','xlsx')) { [Console]::Error.WriteLine("convert.ps1: unsupported .$ext"); exit 2 }
$full = (Resolve-Path -LiteralPath $InputFile).Path

# 1. pandoc if present.
if (Get-Command pandoc -ErrorAction SilentlyContinue) {
  $t = & pandoc $full -t plain 2>$null
  if ($LASTEXITCODE -eq 0) { $t; exit 0 }
}

# 2. Office COM (only if the app is installed).
function Try-COM {
  try {
    switch ($ext) {
      'docx' { $app = New-Object -ComObject Word.Application; $app.Visible=$false
               $d=$app.Documents.Open($full,$false,$true); $txt=$d.Content.Text; $d.Close($false); $app.Quit(); return $txt }
      'pptx' { $app = New-Object -ComObject PowerPoint.Application
               $p=$app.Presentations.Open($full,$true,$false,$false); $sb=New-Object Text.StringBuilder
               foreach($s in $p.Slides){foreach($sh in $s.Shapes){if($sh.HasTextFrame -and $sh.TextFrame.HasText){[void]$sb.AppendLine($sh.TextFrame.TextRange.Text)}}}
               $p.Close(); $app.Quit(); return $sb.ToString() }
      'xlsx' { $app = New-Object -ComObject Excel.Application; $app.Visible=$false; $app.DisplayAlerts=$false
               $wb=$app.Workbooks.Open($full,0,$true); $sb=New-Object Text.StringBuilder
               foreach($ws in $wb.Worksheets){$r=$ws.UsedRange; if($r.Value2){foreach($row in $r.Rows){$cells=@();foreach($c in $row.Columns){$cells+="$($c.Text)"};[void]$sb.AppendLine($cells -join "`t")}}}
               $wb.Close($false); $app.Quit(); return $sb.ToString() }
    }
  } catch { return $null }
}
$out = Try-COM
if ($out) { $out; exit 0 }

# 3. Last resort: unzip + strip tags (loses layout; words survive).
try {
  $tmp = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid())
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [IO.Compression.ZipFile]::ExtractToDirectory($full, $tmp)
  $parts = switch ($ext) {
    'docx' { @(Join-Path $tmp 'word\document.xml') }
    'pptx' { Get-ChildItem (Join-Path $tmp 'ppt\slides') -Filter 'slide*.xml' | Sort-Object Name | ForEach-Object FullName }
    'xlsx' { @(Join-Path $tmp 'xl\sharedStrings.xml') }
  }
  foreach ($p in $parts) { if (Test-Path $p) { (Get-Content -Raw $p) -replace '<[^>]+>',' ' -replace '\s{2,}',' ' } }
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
  exit 0
} catch {
  [Console]::Error.WriteLine("convert.ps1: no usable converter (pandoc/Office/zip): $_"); exit 3
}
