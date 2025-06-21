# loop through wavelengths and store result, both rgb and spectral
$inv_period_values = @(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)

# Base command components
$scriptPath = ".\scripts\rendering\main-headless.py"
$scenePath = ".\scenes\gratings\gratings.xml"
$integrator = "plt"
$spp = 8192
$paramKey = "elm__6.bsdf.brdf_0.inv_period_x.value"

foreach ($value in $inv_period_values) {
    $override = "$paramKey=$value"
    $output_path = ".\results\gratings"
    $cmd_spectral = "python $scriptPath $scenePath -i $integrator --spectral --spp $spp -o $output_path\spectral\period=$value --override $override"

    Write-Host $cmd_spectral

    # run command in spectral mode
    Invoke-Expression $cmd_spectral

    $cmd_rgb = "python $scriptPath $scenePath -i $integrator --spp $spp -o $output_path\rgb\period=$value --override $override"

    Write-Host $cmd_rgb

    # run command
    Invoke-Expression $cmd_rgb
}
