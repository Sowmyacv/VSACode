param(
$global:Server = $args[0],
$global:user = $args[1],
$global:pwd = $args[2],
$global:vmName = $args[3],
$property= $args[4],
[string]$ExtraArgs = $null
) 
Function NOOFDISKS()
{
   
$idecount=0
$scsicount=0
$ides=get-vm $global:vmName -ComputerName $global:Server| get-vmharddiskdrive
foreach($ide in $ides)
{ 
if($ides.controllertype -match 'IDE')
{
$idecount=$idecount+1

}
else
{
$scsicount=$scsicount+1
}
}
#write-host "ide controller: $idecount"
#write-host "scsi controller: $scsicount"
return $scsicount + $idecount

}

Function DiskType($type,$num,$loc)
{
$DiskPath = (Get-VM -Name $global:vmName -ComputerName $global:Server | Get-VMHardDiskDrive -ControllerType $type -ControllerNumber $num -ControllerLocation $loc).Path
return $DiskPath
}



Function DISKSIZE()
{
$disksize = ""
$DriveName1 = @{name=”DriveName”;Expression={$_.DeviceID+””}}
$TotalSpace = @{name=”TotalSpace”;expression = {($_.size/1GB).ToString(“0")}}
$FreeSpace = @{name=”FreeSpace”;expression = {($_.FreeSpace/1GB).ToString(“0")}}
$disk=Get-WmiObject -Class Win32_logicalDisk -computername $vmName | Select $DriveName1, $TotalSpace, $FreeSpace
foreach ($eachdrive in $disk)
{
$diskname = $eachdrive.DriveName+"-"+$eachdrive.FreeSpace
$disksize = $diskname+","+$disksize
$disksize = $disksize.TrimEnd(",")
}
#$disk=(Get-WmiObject -Class Win32_logicalDisk -computername $global:vmName).DeviceID
return $disksize
}

Function GUESTOS()
{
filter Import-CimXml
{
	$CimXml = [Xml]$_
	$CimObj = New-Object -TypeName System.Object
	foreach ($CimProperty in $CimXml.SelectNodes("/INSTANCE/PROPERTY[@NAME='Name']")) 
      { 
         $CimObj | Add-Member -MemberType NoteProperty -Name $CimProperty.NAME -Value $CimProperty.VALUE 
      } 

   foreach ($CimProperty in $CimXml.SelectNodes("/INSTANCE/PROPERTY[@NAME='Data']")) 
      { 
         $CimObj | Add-Member -MemberType NoteProperty -Name $CimProperty.NAME -Value $CimProperty.VALUE 
      } 
        $CimObj
}
try
{
 
$VMConf = Get-WmiObject -ComputerName $global:Server -Namespace "root\virtualization\v2" -Query "SELECT * FROM Msvm_ComputerSystem WHERE ElementName like '$global:vmName' AND caption like 'Virtual%' "
$KVPData = Get-WmiObject -ComputerName $global:Server -Namespace "root\virtualization\v2" -Query "Associators of {$VMConf} Where AssocClass=Msvm_SystemDevice ResultClass=Msvm_KvpExchangeComponent"
$KVPExport = $KVPData.GuestIntrinsicExchangeItems
}
catch
{
$VMConf = Get-WmiObject -ComputerName $Server -Namespace "root\virtualization" -Query "SELECT * FROM Msvm_ComputerSystem WHERE ElementName like '$global:vmName' AND caption like 'Virtual%' "
$KVPData = Get-WmiObject -ComputerName $Server -Namespace "root\virtualization" -Query "Associators of {$VMConf} Where AssocClass=Msvm_SystemDevice ResultClass=Msvm_KvpExchangeComponent"
$KVPExport = $KVPData.GuestIntrinsicExchangeItems
}

 
if ($KVPExport)
{
	# Get KVP Data
	$KVPExport = $KVPExport | Import-CimXml
 
	# Get Guest Information
	$VMOSName = ($KVPExport | where {$_.Name -eq "OSName"}).Data
}
else
{
	$VMOSName = "Unknown"
}
 
if($VMOSName -like '*Win*' -or $VMOSName -imatch "Unknown" -or ([string]::IsNullOrEmpty($VMOSName)))
{
return "Windows"
}
else
{
return "Unix"
}
}


Function Nic()
{
$niccount = 0
$hnics =  (Get-VMNetworkAdapter -VMName $global:vmName -ComputerName $global:Server).SwitchName
foreach($hnic in $hnics)
{
$niccount = $niccount+1
}
return $hnics,$niccount
}

 Function Memory()
{
$FreeMemory  = @{Name="TotalPhysicalMemory";e={[math]::truncate($_.TotalPhysicalMemory /1GB)}}
$mem= (Get-WmiObject -Class win32_computersystem -computername $global:vmName) | select $FreeMemory
#$mem = (Get-VMMemory -VMName $global:vmName).startup
return $mem.TotalPhysicalMemory
}

Function cpunum()
{
$cpunum = (Get-VMProcessor -VMName $global:vmName -ComputerName $global:Server).count
return $cpunum
}

Function GUID()
{
$guid=$global:vm.name
return $guid
}

Function CPU()
{
$usage = Get-WmiObject win32_processor -computername $global:vmName | select LoadPercentage
return $usage.LoadPercentage
}

Function DiskPath()
{
$VMInfo = Get-VM -ComputerName $global:Server -Name $global:vmName

 $VHDs = ($VMInfo).harddrives.path
 
 $VHDString = ""
 $CheckChain = $true

 foreach ($VHD in $VHDs)
{
$ListDisk = New-Object System.Collections.Generic.List[string]
$CheckChain = $true
$VhdChain = $VHD
$dict = @{}

while($CheckChain)
{
$VHDInfo = $VhdChain | Get-VHD -ComputerName hyperv2kr2idc 

if([string]::IsNullOrEmpty($VHDInfo.ParentPath))
{
if([string]::IsNullOrEmpty($ListDisk))
{
$dict.Add($VHD,"None")
}
else
{
$dict.Add($VHD,$ListDisk)
}
$CheckChain = $false
}
else
{

$VhdChain = $VHDInfo.ParentPath
$ListDisk.Add($VHDInfo.ParentPath)
}
}
$str = $dict.GetEnumerator()  | % { "$($_.Name)::$($_.Value)" }
$str = $str +","
$VHDString = $VHDString + $str
}
$VHDString = $VHDString.TrimEnd(",")
return $VHDString
}


Function POWERSTATUS()
{
if($global:vm.EnabledState -eq 2 )
{
return "running"
}
else
{
return "off"
}
}

Function ON()
{
Start-VM $global:vmName
sleep(20)
$op = Get-VM $global:vm -ComputerName $global:Server
return $op.State
}

Function OFF()
{
Start-VM $global:vmName -ComputerName $global:Server
sleep(20)
$op = Get-VM $global:vm
return $op.State
}

Function DeleteVM()
{
Get-VM $global:vmName -ComputerName $global:Server | %{ Stop-VM -VM $_ -Force; Remove-VM -vm $_ -Force ; Remove-Item -Path $_.Path -Recurse -Force}
}

Function Version()
{
$version = (Get-VM -Name $global:vmName -ComputerName $global:Server).IntegrationServicesVersion.major
return $version
}

Function IP()
{ 
$hvip = (Get-WmiObject win32_networkadapterconfiguration -computerName $global:vm -Namespace $NameSpace -filter 'DHCPEnabled = "true"').IPAddress |where {$_-match"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"} 
$HostName=([system.net.dns]::GetHostByAddress($hvip)).hostname
$HostName=$HostName.Hostname
#write-host "hostname:"$HostName
#write-host "IPadddress:" $hvip
return $hvip
}

Function GetVMFilesPath()
{
if($global:OsVersion -imatch "2008")
{
$GlobalValue = Get-WMIObject -class Msvm_VirtualSystemGlobalSettingData -namespace "root/virtualization" | where {$_.ElementName -eq $global:vmName}
return $GlobalValue.ExternalDataRoot
}
else
{
return (Get-VM $global:vmName -ComputerName $global:Server).Path
}
}

Function GetAllVM()
{
$allVMs = gwmi -query "SELECT * FROM Msvm_ComputerSystem" -namespace $global:NameSpace -ComputerName $global:Server | where {$_.Caption -eq "Virtual Machine"}
$ListofVMs = New-Object System.Collections.Generic.List[string]
Foreach($eachVM in $allVMs){
    $ListofVMs.Add($eachVM.ElementName+",")
}
return $ListofVMs
}


$WarningPreference = "SilentlyContinue"
$protocol = "https"
$global:NameSpace =  "root\virtualization\v2"
$global:OsVersion = (Get-WmiObject -class Win32_OperatingSystem -computername $global:Server).caption

if($global:OsVersion -imatch "2008")
{
$global:NameSpace =  "root\virtualization"
}

$vms = Get-WmiObject -Class Msvm_ComputerSystem -Namespace $NameSpace -ComputerName $global:Server


if($vmName -ne ""){

$global:vm = $vms | where-object {$_.elementname -eq $global:vmName}

}

if($Property -eq "All")
{
$var1 = NOOFDISKS 
$var2 = POWERSTATUS 
$var3,$var11 = Nic 
$var4 = Memory 
$var5 = cpunum 
$var6 = DISKSIZE 
$var7 = GUID 
$var8 = GUESTOS 
$var9 = IP 
$var12 = DiskPath 
$var13 = Version
$var14 = GetVMFilesPath 

write-host "Diskcount="$var1";PowerState="$var2";NicName="$var3";Memory="$var4";NoofCPU="$var5";disksize="$var6";GUID="$var7";GuestOS="$var8";IP="$var9";NIC="$var11";DiskPath="$var12";Version="$var13";VMFilesPath="$var14
}

elseif($Property -eq "Basic")
{
$var1 = GUID
$var2 = POWERSTATUS
$var3 = GUESTOS

write-host "GUID="$var1";PowerState="$var2";GuestOS="$var3
}

else
{
if($property -ieq "DiskType")
{
$type,$num,$location = $ExtraArgs.Split(",")
$var10 = &$Property $type $num $location
}
else
{
$var10 = &$Property 
}
write-host $Property"="$var10
}
