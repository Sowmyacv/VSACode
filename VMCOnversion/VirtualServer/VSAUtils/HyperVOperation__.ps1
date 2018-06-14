Param
(
[string]$Server = $args[0],
[string]$username = $args[1],
[string]$password = $args[2],
[string]$global:VMName = $args[3],
[string]$operation = $args[4],
[string]$global:VHDName = $null,
[string]$ExtraArgs = $null
)

#Initialize
$ErrorActionPreference = "Stop"
$VerbosePreference = "SilentlyContinue"
$NameSpace =  "root\virtualization\v2"
$OsVersion = (Get-WmiObject -class Win32_OperatingSystem -computername $Server).caption
write-host $global:VHDName

if($OsVersion -imatch "2008")
{
$NameSpace =  "root\virtualization"
}

$VMs = Get-WmiObject -Class Msvm_ComputerSystem -Namespace $NameSpace -ComputerName $Server

$global:VM = $VMs | where-object {$_.elementname -eq $global:VMName}

$global:VHDService = get-wmiobject -class "Msvm_ImageManagementService" -namespace $NameSpace -computername "."

Function PowerOn($OsVersion)
{
if(($global:VMName).EnabledState -ne 2 )
{
try
{
Start-VM -Name ($global:VMName).ElementName
Write-host "Success"
return 0
}
catch
{
Write-Warning "Error occured: $_"
return 1
}}}

Function PowerOff($OsVersion)
{
if(($global:VMName).EnabledState -eq 2 )
{
try
{
Stop-VM -Name ($global:VMName).ElementName
Write-host "Success"
return 0
}
catch
{
Write-Warning "Error occured: $_"
return 1
}}}

Function Merge($OsVersion,$BaseVHDName)
{
try
{
Merge-VHD –Path $global:VHDName –DestinationPath $BaseVHDName
return 0
}
catch
{
return -1
}
}

function delvm()
{
	
	if($global:VM -ne $null)
	{
		$VSMgtService = get-wmiobject -class "Msvm_VirtualSystemManagementService" -namespace "root\virtualization"  
		$result = $VSMgtService.DestroyVirtualSystem($global:VM) 
        $job=[WMI]$result.job
	 
		if($result.ReturnValue -eq 4096)
		{
           $errcode =  WaitforJobtoFinish $job
		}
		
		return $errcode
	}
}

Function WaitforJobtoFinish($job)
{
while($job.jobstate -lt 7){$job.get()} 
return $job.ErrorCode 
}

function newstate($newState)
{
	
	if($global:VM-ne $null)
	{

		$result = $vm.RequestStateChange($newState) 
	 
	  	$job=[WMI]$result.job

		while ($job.JobState -eq 3 -or $job.JobState -eq 4)
		{
			write-host $job.PercentComplete "% complete"
			start-sleep 1
			$job=[WMI]$result.job
		}
	 
		if($result.ReturnValue -eq 4096)
		{
           $errcode =  WaitforJobtoFinish $job
		}
		
		return $errcode
	}
}



Function DeleteOldHostVM
{

newstate 3
sleep 7
if($global:VM -ne $null -and $global:VM.EnabledState -eq 2)
{
	newstate 3
	sleep 7
	delvm
	return 0
}

if($global:VM -ne $null -and $global:VM.EnabledState -eq 3)
{	
	$flag = newstate 2
	
	if($flag -eq 0)
	{	
		newstate 3
		
		sleep 7
		delvm
		return 0
	}
	else
	{
		sleep  7
		delvm
		return 1
	}
}
 
#Unknown state
if($global:VM -eq $null -or ($global:VM.EnabledState -ne 2 -and $global:VM.EnabledState -ne 3))
{
	return 1
}
}
Function Delete($OsVersion)
{
if($OsVersion -imatch "2008")
{
$result = DeleteOldHostVM
return $result
}
else
{

GET-VM –vmname $global:VMName | GET-VMHardDiskDrive | Foreach { STOP-VM –vmname $_.VMname -Force; REMOVE-VM –vmname $_.Vmname -Force}
sleep(1)
 Write-Host "Success"
 return 0
}
}


Function Checkdriveletter()
{
try
{
$regex = ".*[a-zA-Z]+.*"
$Result = Mount-VHD $global:VHDName -passthru
$drive = (Get-DiskImage -ImagePath $global:VHDName | Get-Disk | Get-Partition).DriveLetter
if($drive -match $regex)
{
Write-Host "Driveletter got assigned"
Write-Host "DriveLetter="$drive
return 0
}
else
{
write-Host "Checking if disk is online"
SetDiskOnline
write-Host "Assigning Driveletter"

$drive = ""
$num = (Get-Disk |Where-Object {$_.FriendlyName -Eq "Microsoft Virtual Disk"}).Number
$partiionlist = (Get-Partition -DiskNumber $num).PartitionNumber
foreach($eachpartition in $partiionlist)
{
$partitionDriveletter = (Get-Partition -DiskNumber $num -PartitionNumber $eachpartition).DriveLetter
if([string]::IsNullOrWhiteSpace($partitionDriveletter))
{
$drive = AssignDriveletter $num $eachpartition
$driveletter = $drive +","+$driveletter
}
}
Write-Host "DriveLetter="$driveletter
return 0
}
}
catch
{
$ErrorMessage = $_.Exception.Message
$FailedItem = $_.Exception.ItemName
write-Host $ErrorMessage
write-Host $FailedItem
}
}

Function AssignDriveletter($DiskNumber,$partitionnum)
{
$AllLetters = 65..90 | ForEach-Object {[char]$_ + ":"}
$UsedLetters = get-wmiobject win32_logicaldisk | select -expand deviceid
$FreeLetters = $AllLetters | Where-Object {$UsedLetters -notcontains $_}
$driveletter = ($FreeLetters | select-object -last 1).split(":")[0]
Get-Partition -DiskNumber $DiskNumber -PartitionNumber $partitionnum | Set-Partition -NewDriveLetter $driveletter
return $driveletter
}

Function SetDiskOnline()
{
$num = $null

$num = (Get-Disk | where-object IsOffline –Eq $True | Where-Object {$_.FriendlyName -Eq "Microsoft Virtual Disk"}).Number
if (-Not([string]::IsNullOrWhiteSpace($num)))
{
       Set-Disk -Number $num -IsOffline $False
}
}

Function ChangeExtension()
{

$Extn = [IO.Path]::GetExtension($global:VHDName)
$fileBaseName = (Get-Item $global:VHDName).Basename
$fileDirectoryName = (Get-Item $global:VHDName).DirectoryName
$Filewithoutextn = join-path $fileDirectoryName  $fileBaseName

if($Extn -ieq ".avhd")
{
$Newfilename = $Filewithoutextn+".vhd"
}
elseif($Extn -ieq ".avhdx")
{
$Newfilename = $Filewithoutextn+".vhdx"
}
$OldFileName = $global:VHDName
Rename-Item $global:VHDName $Newfilename
$global:VHDName = $Newfilename
return $OldFileName
}

Function MountVHD($OsVersion)
{

$OldFileName = ChangeExtension

if($OsVersion -imatch "2008")
{

$Result = $global:VHDService.Mount($global:VHDName)
return 0
}
else
{

$Vhdmount = Checkdriveletter $global:VHDName
}


if($Vhdmount -eq 0)
{
write-Host "Success"
return 0
}

else
{
Write-Host "issue in bringing Device online"
}
}

Function UnMountVHD
{
[CmdletBinding()]
param (
[string]$OsVersion,
[string]$rename = "true"
)

$OldFileName = ''
if($rename -imatch "true")
{
$BaseName = $global:VHDName.Substring(0, $global:VHDName.LastIndexOf('.'))
$Extn = $global:VHDName.Split(".")[1]

if($Extn -ieq "avhd")
{
$Newfilename = $BaseName+".vhd"
$OldFileName = $global:VHDName
$global:VHDName = $Newfilename
}
elseif($Extn -ieq "avhdx")
{
$Newfilename = $BaseName+".vhdx"
$OldFileName = $global:VHDName
$global:VHDName = $Newfilename
}
}

if($OsVersion -imatch "2008")
{

$Result = $global:VHDService.Unmount($global:VHDName)
Write-host "Success"
if (-Not([string]::IsNullOrWhiteSpace($OldFileName)))
{
Rename-Item $global:VHDName $OldFileName
}
return 0
}

else
{
$testmount = Get-DiskImage -ImagePath $global:VHDName | Get-Disk | Get-Partition
if (-Not([string]::IsNullOrWhiteSpace($testmount)))
{
Dismount-VHD -Path $global:VHDName
Write-host $Result
Write-host "Success"
if (-Not([string]::IsNullOrWhiteSpace($OldFileName)))
{
Rename-Item $global:VHDName $OldFileName
}
return 0
}
else
{
return 0
}}}

if($operation -ieq "Merge")
{
$BaseVHDName = $ExtraArgs
$var1 = &$operation $OsVersion $BaseVHDName
}
else
{
$var1 = &$operation $OsVersion 
return $var1
}