
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
$global:vmUser = "##Automation--vm_user--##"
$global:vmPass = "##Automation--vm_pass--##"
$global:property= "##Automation--property--##"
[string]$global:ExtraArgs = "##Automation--extra_args--##"

Connect-VIServer -Server $Server -User $user -Password $pwd -Protocol $protocol | Out-Null

$var = &$global:property 
write-host $global:property[0]"="$var
}



function COPYDATA()
{
  try {
        $_path=$global:ExtraArgs -split "@"
        $_path[0] = $_path[0] + "\*"
        Copy-VMGuestFile -LocalToGuest -Force -VM $global:vmName -Source $_path[0] -Destination $_path[1] -GuestUser $global:vmUser -GuestPassword $global:vmPass
        return "Sucess"
    }
    catch
    {
        return "Error"

}}