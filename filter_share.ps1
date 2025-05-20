$threshold = 700000
$outputFile = "share_filter_output.log"
Remove-Item $outputFile -ErrorAction SilentlyContinue
Add-Content $outputFile "Filtered Results:`n"

$totalMatches = 0  # 匹配总数

Get-ChildItem -Filter *.log |
    Where-Object { $_.Name -ne $outputFile } |
    Sort-Object LastWriteTime -Descending |
    ForEach-Object {
        $file = $_
        $filename = $file.Name
        $fullpath = $file.FullName
        $usedFile = $fullpath

        # 检测是否被占用
        try {
            $stream = [System.IO.File]::Open($fullpath, 'Open', 'Read', 'None')
            $stream.Close()
        } catch {
            # 被锁定，创建副本
            $tempFile = "$($fullpath).copy"
            Copy-Item $fullpath $tempFile -Force
            $usedFile = $tempFile
        }

        # 检查前100行是否含“Selected Algorithm: Autolykos V2”
        $Algorithm = $false
        $reader = [System.IO.StreamReader]::new($usedFile)
        $checkLines = 0
        while (-not $reader.EndOfStream -and $checkLines -lt 100) {
            $line = $reader.ReadLine()
            if ($line -match "Selected Algorithm: Autolykos V2") {
                $Algorithm = $true
                break
            }
            $checkLines++
        }
        $reader.Close()

        if (-not $Algorithm) {
            Write-Host "Skipping file (not Autolykos V2): $filename"
            if ($usedFile -ne $fullpath -and (Test-Path $usedFile)) {
                Remove-Item $usedFile -Force
            }
            return
        }

        Write-Host "Processing file: $filename"
        $results = @()
        $lineNumber = 0
        $reader = [System.IO.StreamReader]::new($usedFile)

        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()
            $lineNumber++

            if ($lineNumber % 100 -eq 0) {
                Write-Host -NoNewline "`r  Progress: Line $lineNumber"
            }

            if ($line.Contains("Found a share of difficulty")) {
                if ($line -match "difficulty\s+([0-9]+(?:\.[0-9]+)?)G") {
                    $value = [decimal]$matches[1]
                    if ($value -gt $threshold) {
                        $results += "$filename Line ${lineNumber}: $line"
                        $totalMatches++
                    }
                }
            }
        }
        $reader.Close()
        Write-Host ""

        # 写入结果
        if ($results.Count -gt 0) {
            Add-Content $outputFile $results
        }

        # 删除副本
        if ($usedFile -ne $fullpath -and (Test-Path $usedFile)) {
            Remove-Item $usedFile -Force
        }
    }

Write-Host "`nDone. Total matching lines: $totalMatches"
Write-Host "Results written to $outputFile"
