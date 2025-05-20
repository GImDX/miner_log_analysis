$url = "https://ergo.herominers.com/api/workers_stream?address=9fg7qxJffnGE6wYzTKot4C8LKHEab3GyGYTB8ynbWYR1xFQs5H7"
$outputFile = "workers_stream.jsonl"
$proxy = "127.0.0.1:7890"

while ($true) {
    try {
        Write-Host "🔌 Connecting to stream through proxy..."

        cmd /c "curl --proxy $proxy $url" |
        ForEach-Object {
            if ($_ -ne "") {
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                $lineWithTimestamp = "[$timestamp] $_"
                Add-Content -Path $outputFile -Value $lineWithTimestamp
                # Write-Host "📥 Received: $lineWithTimestamp"  # 已注释：不实时打印
            }
        }
    } catch {
        Write-Host "⚠️ Error: $($_.Exception.Message)"
    }

    Write-Host "🔁 Reconnecting in 1 seconds..."
    Start-Sleep -Seconds 1
}
