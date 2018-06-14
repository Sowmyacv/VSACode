
#Purpose:  TO Get all VMs and some properties of the vm from given HOst or vCenter


Function Main()
{
import-Module VMware.VimAutomation.Core
$WarningPreference = "SilentlyContinue"
$protocol = "https"

#initialize general varaibles
$global:Server = "##Automation--server_name--##"
$global:user = "##Automation--user--##"
$global:pwd = "##Automation--pwd--##"
$global:vmName = "##Automation--vm_name--##"
$global:property= "##Automation--property--##"
[string]$global:ExtraArgs = "##Automation--extra_args--##"


Connect-VIServer -Server $Server -User $user -Password $pwd -Protocol $protocol | Out-Null
if($property -eq "All")
{
$var1 = GUID
$var2 = PowerState
$var3 = GuestOS
$var4 = ESX
$var5 = CPUNum 
$var6 = NoOfDisks
$var7 = IP
$var8 = NIC
$var9 = Memory
$var10 = Datastore
$var11 = ResourcePool
$var12 = DataCenter
$var13 = HostName
$var14 = Tools
$var15 = SnapExists
$var16 = VMSpace

write-host "GUID="$var1";PowerState="$var2";GuestOS="$var3";Memory="$var9";NoofCPU="$var5";Diskcount="$var6";IP="$var7";NIC="$var8";ESXHost="$var4";Datastore="$var10";ResourcePool="$var11";DataCenter="$var12";Hostname="$var13";ToolsStatus="$var14";snapExists="$var15";VMSpace="$var16 
}
elseif($global:property -eq "Basic")
{
$var1 = GUID
$var2 = POWERSTATE
$var3 = GUESTOS

write-host "GUID="$var1";PowerState="$var2";GuestOS="$var3
}
else
{
$var10 = &$global:property 
write-host $global:property "=" $var10
}
}



function GetAllVM()
{
  $getallVM=Get-VM
  return $getallVM.name
}

function GetVcenterVersion()
{
  return $global:DefaultVIServer.ExtensionData.Content.About.Version
}

function getNicDetail()
{
&{foreach($esx in Get-VMHost){
    $vNicTab = @{}
    $esx.ExtensionData.Config.Network.Vnic | %{
        $vNicTab.Add($_.Portgroup,$_)
    }
    foreach($vsw in (Get-VirtualSwitch -VMHost $esx)){
        foreach($pg in (Get-VirtualPortGroup -VirtualSwitch $vsw)){
            Select -InputObject $pg -Property @{N="ESX";E={$esx.name}},
                @{N="Portgroup";E={$pg.Name}}
        }
    }
}}
return $vNicTab
}


function GetESXDetail()
{
  #$esx = get-vmhost | where {$_.state -eq "Connected"}
  #$esx_detail = $esx | select Name, id, Numcpu, MemoryUsageGB, MemoryTotalGB
  #return $esx_detail
  $esx = get-vmhost | where {$_.state -eq "Connected"}
    $esx_detail =$esx | Select Name,id,Numcpu,
    @{N='CPUGHzCapacity';E={[math]::Round($_.CpuTotalMhz/1000,2)}},
    @{N='CPUGHzUsed';E={[math]::Round($_.CpuUsageMhz/1000,2)}},
    @{N='CPUGHzFree';E={[math]::Round(($_.CpuTotalMhz - $_.CpuUsageMhz)/1000,2)}},
    @{N='MemoryTotalGB';E={[math]::Round($_.MemoryTotalGB,2)}},
    @{N='MemoryUsedGB';E={[math]::Round($_.MemoryUsageGB,2)}},
    @{N='MemoryFreeGB';E={[math]::Round(($_.MemoryTotalGB - $_.MemoryUsageGB),2)}}
return $esx_detail
}


Function GUID()
{
 $vm = get-view -viewtype VirtualMachine -filter @{"name" = "^($global:vmName)$"}
 $vm_guid = $vm.Summary.config.InstanceUuid
 return $vm_guid
}

Function PowerState()
{
 $temp=Get-VM ($global:vmName)|Select PowerState
 return $temp.PowerState
}

Function GuestOS()
{
$vm = get-view -viewtype VirtualMachine -filter @{"name" = "^($global:vmName)$"}
$vm_guid = $vm.Summary.config.GuestFullName
if($vm_guid -like '*Win*')
{
    return "Windows"
    }
else
{
    return "unix"
    }
}

Function DiskSize(){
 $HardDiskSize=(get-vm -Name $global:vmName | Get-HardDisk | measure-Object CapacityGB -Sum).sum
 return $HardDiskSize
}

Function CPUNum()
{
 $vm = get-view -viewtype VirtualMachine -filter @{"name" = "^($global:vmName)$"}
$cpunum= $vm.summary.config.NumCpu
return $cpunum
}

Function NoOfDisks()
{
 $NoOfDisks= get-Harddisk -VM $global:vmName
 return $NoOfDisks.count
}

Function IP()
{
 return (get-VM -Name $global:vmName).Guest.IPAddress
}

Function NIC()
{
 $nic = ((Get-NetworkAdapter -VM ($global:vmName) | Measure).Count)
 return $nic
}

Function Memory()
{
  $vm = get-view -viewtype VirtualMachine -filter @{"name" = "^($global:vmName)$"}
  $vm_ram = $vm.Summary.Config.MemorySizeMB
  $vm_ram = $vm_ram/1024
  return $vm_ram
}

Function Datastore()
{
 $VMn = get-VM ($global:vmName)
 $s = ""
 $DS = Get-Datastore -VM $VMn |Select Name
 ForEach ($d in $DS){
 $s = $s + $d.Name + ","
 }
 return $s
}

 
Function DataCenter()
{
 $ds = Get-DataCenter -VM ($global:vmName)
 return $ds.Name
}
 
Function SnapExists()
{
 $s=Get-Snapshot -VM (get-VM ($global:vmName))
 if ($s -eq $null)
  {
   return $false
  }
 else
  {
   return $true
  }
}
 
Function HostName()
{
 $Hostdetails = (Get-VM ($global:vmName))
 return $Hostdetails.Guest.HostName
}

Function Tools()
{
 return ($global:VM).Guest.ToolsStatus
}

Function ESX()
{
 $esx = Get-VMHost -VM ($global:vmName)
 return $esx.Name
}
 
function Get-Path{
    param($Object)
    
    $path = $object.Name
    $parent = Get-View $Object.ExtensionData.ResourcePool
    while($parent){
        $path = $parent.Name + "/" + $path
        if($parent.Parent){
            $parent = Get-View $parent.Parent
        }
        else{$parent = $null}
    }
    $path
}


function ResourcePool()
{
$rp = Get-ResourcePool -VM $global:vmName
return $rp.Name
}

function GetStructureTree()
{
  $ds = get-view -viewtype Datastore -filter @{"name" =$global:ExtraArgs}
  $esx = get-view -viewtype HostSystem | where {$_.Datastore -contains $ds[0].MoRef}
  $cluster = get-view -viewtype ComputeResource | where {$_.host -contains $esx.MoRef}
  $dc = Get-view -ViewType Datacenter | where {$_.hostfolder -contains $cluster.parent}
  $tree_detail =New-Object string[] 3
  $tree_detail[0] = -join ("ESX=",$esx.Name )
  $tree_detail[1] = -join ("Cluster=",$cluster.Name )
  $tree_detail[2] = -join ("Datacenter=",$dc.Name)
  return $tree_detail 
}


Function VMSpace()
{
  $vm_space = ((get-vm | Where-object{$_.Name -eq $global:vmName }).UsedSpaceGB | Measure-Object -Sum).Sum
  $vm_space = [math]::Round($vm_space,2)
  return $vm_space
}



function GetDatastoreDetail()
{
  $DS = get-datastore | where {$_.type -eq "VMFS"}
  $DS_detail=$DS | Select Name, id, @{N="FreeSpaceGB";E={[math]::Round($_.FreeSpaceMB /1024,2)}} , @{N="CapacityGB";E={$_.CapacityMB /1024}}
  return $DS_detail
  }