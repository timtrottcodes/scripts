Add-Type -AssemblyName System.Drawing

$folder = Get-Location

Get-ChildItem -Path $folder -Filter *.png | ForEach-Object {
    $pngPath = $_.FullName
    $jpgPath = Join-Path $folder ($_.BaseName + ".jpg")

    try {
        $image = [System.Drawing.Image]::FromFile($pngPath)

        # Create a new bitmap to strip metadata
        $bitmap = New-Object System.Drawing.Bitmap $image.Width, $image.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.DrawImage($image, 0, 0, $image.Width, $image.Height)

        # Save as JPEG with quality
        $encoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
        $encoderParams = New-Object System.Drawing.Imaging.EncoderParameters 1
        $encoderParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality, 75L)

        $bitmap.Save($jpgPath, $encoder, $encoderParams)

        $graphics.Dispose()
        $bitmap.Dispose()
        $image.Dispose()

        Write-Host "Converted: $($_.Name) -> $jpgPath"
    }
    catch {
        Write-Warning "Failed to convert: $($_.Name) - $_"
    }
}
