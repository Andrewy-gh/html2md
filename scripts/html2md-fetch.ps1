param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $Url,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $RemainingArgs
)

$ErrorActionPreference = "Stop"

$commandTemplate = if ($env:HTML2MD_FETCH_COMMAND) {
    $env:HTML2MD_FETCH_COMMAND
} else {
    'html2md ${url}'
}

$quotedUrl = "'" + ($Url.Replace("'", "''")) + "'"
$command = $commandTemplate.Replace('${url}', $quotedUrl)

if ($RemainingArgs.Count -gt 0) {
    $quotedArgs = $RemainingArgs | ForEach-Object {
        "'" + ($_.Replace("'", "''")) + "'"
    }
    $command = "$command $($quotedArgs -join ' ')"
}

Invoke-Expression $command
