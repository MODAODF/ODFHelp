# project name
$filename = "NDCHelp"

# compression delay time
$zipdelay = 15000

$dir = get-location
$destzip = "$dir\$filename.zip"
$destoxt = "$dir\$filename.oxt"

function Add-Zip
{
    param([string]$zipfilename)

    if(-not (test-path($zipfilename)))
    {
		# The minimum size of a .ZIP file is 22 bytes.
		#Such empty zip file contains only an End of Central Directory Record (EOCD):
		#[50,4B,05,06,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00]
        set-content $zipfilename ("PK" + [char]5 + [char]6 + ("$([char]0)" * 18))
        (dir $zipfilename).IsReadOnly = $false
    }
	# return $zipFilename（Folder Object）
    $shellApplication = new-object -com shell.application
    $zipPackage = $shellApplication.NameSpace($zipfilename)

    $collection = 0..12
	$count = 0
	$start = Get-Date
	$secondsRemaining = 0

    foreach($file in $input)
    {
		$count++
		$percentComplete = ($count / $collection.Count) * 100
		Write-Progress -Activity Creating... -Status "Processing item #$($file)" -PercentComplete $percentComplete -SecondsRemaining $secondsRemaining

		# create zip file copy $sourceDirectory to $zipFilename
		$zipPackage.CopyHere($file.FullName)
		if ($file -like "*conpics") {
			Start-sleep -milliseconds $zipdelay
		} else {
			Start-sleep -milliseconds 2000
		}

        # calculating seconds elapsed and remaining
		$secondsElapsed = (Get-Date) - $start
		$secondsRemaining = ($secondsElapsed.TotalSeconds / $count) * ($collection.Count - $count)
		if ($secondsRemaining -lt 0) {
			$secondsRemaining = 0
		}
    }
    Write-Progress -Activity Updating -Status 'Finished processing all items' -Complete -SecondsRemaining 0
	Write-Host ''

}

if(-not (test-path($destoxt)))
{
	if(-not (test-path($destzip)))
	{
		Write-Host 'Create oxt file...'
		Write-Host 'please dont close windows...' -ForegroundColor red -BackgroundColor white
		dir .\src\* | Add-Zip $destzip
	}
	rename-item -path $destzip -newname $destoxt
	Write-Host 'Success.....'
	# pause
	#cmd /c pause | out-null
} else {
	Write-Host '['$filename']' 'oxt file already exist...' -ForegroundColor red -BackgroundColor white
	Write-Host 'Please push any key to exit...'
	# pause
	cmd /c pause | out-null
}
