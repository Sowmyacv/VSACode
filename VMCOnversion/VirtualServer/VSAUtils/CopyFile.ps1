Function Main()
{
#initialize general variables
$vmname = ##Automation--vm_name--##
$sourcepath = ##Automation--source_path--##
$destpath = ##Automation--dest_path--##

$paramHash = @{
 Name = $vmname
 SourcePath = $sourcepath
 DestinationPath = $destpath
 CreateFullPath = $True
 FileSource = 'Host'
 Force = $True
 Verbose = $True
}

$out = copyfile $paramHash
write-Host $out
}

function copyfile($paramHash)
{
try
{
dir $sourcepath| foreach {

 $paramHash.SourcePath = $_.fullname
 Copy-VMFile @paramHash
 write-Host "Success"
}
}
catch
{
write-Host "Error"
return 1
}
}

