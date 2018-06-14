from cvpysdk.commcell import Commcell

_cs_obj = Commcell("zeus.idcprodcert.loc", "admin", "")
_client_obj = _cs_obj.clients.get("HvAutoSource")
_agent_obj = _client_obj.agents.get('Virtual Server')
_instancekeys = next(iter(_agent_obj.instances._instances))
_instance_obj = _agent_obj.instances.get(_instancekeys)
# print(_instance_obj.server_name)
# _instance_obj.associated_clients = ['hvidc1','hvidc2']
_backupset_obj = _instance_obj.backupsets.get('defaultbackupset')
_sub_obj = _backupset_obj.subclients.get('AutomationCrash')
print(_sub_obj.content)
print(_sub_obj.storage_policy)

# """
_Restore_Job = _sub_obj.guest_file_restore("V11AutoLin", "/centos-root/FULL/TestData",
                                           destination_path="D:\\CVAutomationRestore")
print(_Restore_Job.job_id)
if not _Restore_Job.wait_for_completion():
    raise Exception(
        "Failed to run restore out of place job with error: " + str(_Restore_Job.delay_reason)
    )
"""
#"""
_Restore_Job = _sub_obj.disk_restore("RegularAuto12", "hvidc1", "D:\\CVAutomation")
print(_Restore_Job.job_id)
if not _Restore_Job.wait_for_completion():
    raise Exception(
        "Failed to run restore out of place job with error: " + str(_Restore_Job.delay_reason)
    )

"""
#"""
_Restore_Job = _sub_obj.full_vm_restore_out_of_place(destination_client="HvAutoSource",
                                                     destination_path="D:\CVAutomationRestore")
print(_Restore_Job.job_id)
if not _Restore_Job.wait_for_completion():
    raise Exception(
        "Failed to run restore out of place job with error: " + str(_Restore_Job.delay_reason)
    )
"""
"""
_Restore_Job = _sub_obj.full_vm_restore_in_place()
print(_Restore_Job.job_id)
if not _Restore_Job.wait_for_completion():
    raise Exception(
        "Failed to run restore out of place job with error: " + str(_Restore_Job.delay_reason)
    )

    # """