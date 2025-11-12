$headers = @{
    "Content-Type" = "application/json; charset=utf-8"
}
$body = @{
    prompt = "Продажи за неделю"
} | ConvertTo-Json
$bodyUtf8 = [System.Text.Encoding]::UTF8.GetBytes($body)

Invoke-RestMethod -Uri "http://localhost:8000" -Method POST -Headers $headers -Body $bodyUtf8