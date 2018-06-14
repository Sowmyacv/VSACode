filter Import-CimXml
  {
   $CimXml = [Xml]$_
  $osNameNode = $CimXml.SelectSingleNode("/INSTANCE/PROPERTY[@NAME='Name']/VALUE[child::text() = 'OSName']")
if ($osNameNode -ne $null)
     {
     return $osNameNode.SelectSingleNode("/INSTANCE/PROPERTY[@NAME='Data']/VALUE/child::text()").Value
} 
}

 $vmObj = Get-WmiObject -Namespace root\virtualization\v2 -Query "Select * From Msvm_ComputerSystem Where ElementName='V11AutoLin'"
 $Kvp = $vmObj.GetRelated("Msvm_KvpExchangeComponent")
$CimData = $Kvp.GuestIntrinsicExchangeItems
 
 if ($CimData -ne $null) #only for running vm
 {
  $osName = ($CimData | Import-CimXml)
  if ($osName -ne $null) # os like linux or something not supported KVPExchange
    {
    if ($osName.Contains("Window"))
     {
      Write-Host "Done"
     }
   }
} 