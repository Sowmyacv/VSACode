Function Main()
{
#initialize general varaibles
$global:Server = "##Automation--server_name--##"
$global:vmName = "##Automation--vm_name--##"
$global:property= "##Automation--property--##"
[string]$global:ExtraArgs = "##Automation--extra_args--##"
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

if($global:Property -eq "All")
{
$var1 = NOOFDISKS
$var2 = POWERSTATUS
$var3,$var11 = Nic
$var4 = Memory
$var5 = cpunum
$var7 = GUID
$var8 = GUESTOS
$var9 = IP
$var12 = DiskPath
$var13 = Version
$var14 = GetVMFilesPath

write-host "Diskcount="$var1";PowerState="$var2";NicName="$var3";Memory="$var4";NoofCPU="$var5";GUID="$var7";GuestOS="$var8";IP="$var9";NIC="$var11";DiskPath="$var12";Version="$var13";VMFilesPath="$var14
}

elseif($global:Property -eq "Basic")
{
$var1 = GUID
$var2 = POWERSTATUS
$var3 = GUESTOS

write-host "GUID="$var1";PowerState="$var2";GuestOS="$var3
}

else
{
if($global:property -ieq "DiskType")
{
$type,$num,$location = $global:ExtraArgs.Split(",")
$var10 = &$global:Property $type $num $location
}
else
{
$var10 = &$global:Property
}
write-host $global:Property"="$var10
}
}

function NOOFDISKS()
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

function DiskType($type,$num,$loc)
{
$DiskPath = (Get-VM -Name $global:vmName -ComputerName $global:Server | Get-VMHardDiskDrive -ControllerType $type -ControllerNumber $num -ControllerLocation $loc).Path
return $DiskPath
}


function GUESTOS()
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

if($VMOSName -like '*Win*' -or $VMOSName -imatch "Unknown")
{
return "Windows"
}
else
{
return "Unix"
}
}


Function DISKSIZE()
{
$disksize = ""
$disk=Get-WMIObject Win32_Logicaldisk -ComputerName $global:vmName |
Select @{Name="DriveName";Expression={$_.DeviceID}},
@{Name="FreeSpace";Expression={[math]::Round($_.Freespace/1GB,2)}}

foreach ($eachdrive in $disk)
{
$diskname = $eachdrive.DriveName+"-"+$eachdrive.FreeSpace
$disksize = $diskname+","+$disksize
$disksize = $disksize.TrimEnd(",")
}
#$disk=(Get-WmiObject -Class Win32_logicalDisk -computername $global:vmName).DeviceID
return $disksize
}

function Nic()
{
$niccount = 0
$hnics =  (Get-VMNetworkAdapter -VMName $global:vmName -ComputerName $global:Server).SwitchName
foreach($hnic in $hnics)
{
$niccount = $niccount+1
}
return $hnics,$niccount
}

 function Memory()
{
$tot = Get-VM $global:vmName
$total = [math]::Round(($tot.MemoryAssigned)/(1024*1024*1024))
return $total
}

function HostMemory()
{
$vmHost = Get-VMHost -ComputerName $global:Server
if($vmHost)
{
$total = 0
Get-VM -ComputerName $global:Server | Where-Object { $_.State -eq "Running" } | Select-Object Name, MemoryAssigned | ForEach-Object { $total = $total + $_.MemoryAssigned }
 
#Get available RAM via performance counters
$Bytes = Get-Counter -ComputerName $global:Server -Counter "\Memory\Available Bytes"
 
# Convert values to GB
$availGB = ($Bytes[0].CounterSamples.CookedValue / 1GB)

return $availGB
}
}

function cpunum()
{
$cpunum = (Get-VMProcessor -VMName $global:vmName -ComputerName $global:Server).count
return $cpunum
}

function GUID()
{
$guid=$global:vm.name
return $guid
}

function CPU()
{
$usage = Get-WmiObject win32_processor -computername $global:vmName | select LoadPercentage
return $usage.LoadPercentage
}

function DiskPath()
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
$VHDInfo = $VhdChain | Get-VHD -ComputerName $global:Server

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


function POWERSTATUS()
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

function ON()
{
Start-VM $global:vmName
sleep(20)
$op = Get-VM $global:vm -ComputerName $global:Server
return $op.State
}

function OFF()
{
Start-VM $global:vmName -ComputerName $global:Server
sleep(20)
$op = Get-VM $global:vm
return $op.State
}

function DeleteVM()
{
Get-VM $global:vmName -ComputerName $global:Server | %{ Stop-VM -VM $_ -Force; Remove-VM -vm $_ -Force ; Remove-Item -Path $_.Path -Recurse -Force}
}

function Version()
{
$version = (Get-VM -Name $global:vmName -ComputerName $global:Server).IntegrationServicesVersion.major
return $version
}

function IP()
{
$ip = (Get-VM -Name $global:vmName | Select -ExpandProperty NetworkAdapters).IPAddresses | where {$_ -match "^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"}
return $ip
}

function GetVMFilesPath()
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

function GetAllVM()
{
$allVMs = gwmi -query "SELECT * FROM Msvm_ComputerSystem" -namespace $global:NameSpace -ComputerName $global:Server | where {$_.Caption -eq "Virtual Machine"}
$ListofVMs = New-Object System.Collections.Generic.List[string]
Foreach($eachVM in $allVMs){
    $ListofVMs.Add($eachVM.ElementName+",")
}
return $ListofVMs
}


