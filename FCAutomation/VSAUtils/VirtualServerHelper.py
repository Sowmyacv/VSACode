# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that act as wrapper for testcase and SDK

classes defined:
    Auto_VSA_Commcell   - wrapper for commcell operations
    Auto_VSA_VSClient   - wrapper for VSA Client operations
    Auto_VSA_VSInstance - wrapper for VSA Instance operation
    Auto_VSA_Backupset  - wrapper for VSA Backupset Operations
    Auto_VSA_Subclient  - wrapper for VSA Subclient operations

"""

import os
import re
import socket
import time
import math
from AutomationUtils.machine import Machine
from .HypervisorHelper import Hypervisor
from . import VirtualServerConstants
from . import VirtualServerUtils
from cvpysdk.job import Job
from AutomationUtils import cvhelper
from AutomationUtils import logger


class AutoVSACommcell(object):
    """
    class that act as wrapper for SDK and Testcase

    Methods:
            get_client_id()             - gets the client ID of given client name

            get_hostname_for_client()   - get the Host name for the given client

            get_base_dir()              - get the base directory of client given
                                        (default: Commserv client)

            get_client_os_type()           - get the os info of the client

            _check_backup_job_type_expected()   - check the passed job id type and
                                                    passed job type is expeted

            _client_exist_in_cs()       - check if the client exist in CS

            get_job_duration()          - get the job duration of the job passed

            get_job_results_dir()                   - get the job results directory of the client
                                        (default: commserv client)

    """

    def __init__(self, commcell, csdb):
        """
        Initialize the  SDK objects

        Args:
            commcell    (obj)   - Commcell object of SDK Commcell class

            csdb        (obj)   - CS Database object from testcase

        """

        self.log = logger.get_log()
        self.commcell = commcell
        self.csdb = csdb
        self.commserv_name = self.commcell.commserv_name
        self.base_dir = self.get_base_dir()

    def get_client_id(self, client_name):
        """
        Get the client ID for the given client

        Args:
                client_name     (str)   - Client name for whihc client Id
                                                                                need to be fetched

        Return:
                client_id   (int)       - Id of the client name given

        Exception:
                if client does not exists in CS

        """
        try:
            self.log.info("Getting the client ID for {0} ".format(client_name))
            _client_obj = self.commcell.clients.get(client_name)
            return _client_obj.client_id

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the client ID {0}".format(err))
            raise err

    def get_hostname_for_client(self, client_name=None):
        """
        Get the Host name for the given HostName

        Args:
                client_name     (str)   - Client name for which client Id
                                                                                need to be fetched
                                             default value is  commsev_name

        Return:
                host_name   (int)       - Hostname of the client name given

        Exception:
                if client does not exists in CS

        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            self.log.info("Getting HostName for Client for %s " % client_name)
            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.client_hostname

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the client ID %s" % err)
            raise err

    def get_instanceno_for_client(self, client_name=None):
        """
        Get the instance number for the given HostName

        Args:
                client_name     (str)   - Client name for which client Id
                                                                                need to be fetched
                                             default value is  commsev_name

        Return:
                instance  (str)       - Instance number of the client name given

        Exception:
                if client does not exists in CS

        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            self.log.info("Getting HostName for Client for %s " % client_name)
            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.instance

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the instance number %s" % err)
            raise err

    def get_client_name_from_hostname(self, host_name):
        """
        Get the Host name for the given HostName

        Args:
                host_name     (str)   - host name  for which client name
                                                                                need to be fetched

        Return:
                client_name   (int)       -client name of the client from the given hostname

        Exception:
                if client does not exists in CS

        """
        try:

            self.log.info("Getting client name for Client for %s " % host_name)
            _query = "select name from APP_Client where net_hostname = '%s'" % host_name

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            return _results[0]

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the client ID %s" % err)
            raise err

    def get_base_dir(self, client_name=None):
        """
        Get the base directory for the commvault installation

        Args:
                client_name     (str)   - Client name for which client Id
                                                                        need to be fetched
                                            default value is    (str)   commsev_name

        Return:
                base_dir    (int)       - installtion base dir of simpana in that client

        Exception:
                if client does not exists in CS
        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            _base_dir = os.path.join(_client_obj.install_directory, "Base")
            return _base_dir

        except Exception as err:
            self.log.exception("Error in getting the base directory %s" % err)
            raise err

    def get_client_os_type(self, client_name=None):
        """
        Gets the OS type [Windows / Unix] of the client

        Args:
                client_name     (str)   - Client name for which os info
                                                                        need to be fetched
                                            default value is    commsev_name
        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.os_info

        except Exception as errrr:
            self.log.exception(
                "An error occured in getting the OS version of the client")
            raise errrr

    def _check_backup_job_type_expected(self, job_id, job_type):
        """
        check if the Job Type is expected

        Args:
                job_id      (int)   - job id whohc needs to be checked

                job_type    (str)   - the jpb type which the job id provided
                                                                        dhoulf be verified with

        Exception:
                if the job type is not expected

                if the job does not exist

        """
        try:
            _job_info = Job(self.commcell, job_id)
            _job_type_from_cs = _job_info.backup_level
            if (_job_type_from_cs.lower()) == (job_type.lower()):
                self.log.info("Ok.The job was %s" % job_type)
            else:
                raise Exception("Job type was for the jobid %s is %s which is not expected" % (
                    job_id, job_type))

        except Exception as errrr:
            self.log.exception(
                "An exception occurred in CheckJobTypeIsExpected")
            raise errrr

    def _client_exist_in_cs(self, client_name):
        """
        check particular client exist in CS

        Args:
                client_name (str)   - client which has to be chacked that it exist in CS

        Return:
                True - If exists

                False- if does not exist
        """
        try:
            return self.commcell.clients.has_client(client_name)

        except Exception:
            return False

    def get_job_duration(self, job_id):
        """
        get the Duration of the particular Job

        Args:
                job_id (int)   -- job id for which duratiuon has to be fetched

        Exception:
                if job does not exist
        """
        try:
            _job_info = Job(self.commcell, job_id)
            _job_duration = (_job_info.end_time - _job_info.start_time)
            return _job_duration

        except Exception as errrr:
            self.log.exception("An exception occurred in GetJobDuration")
            raise errrr

    def get_job_results_dir(self, client_name=None):
        """
        Get the Job Results Directory

        Args:
                client_name (str)   -- client name for which simapana isntalled
                                            Job results directory has to be fetched
                                default value is     - commserv_name

        Exception:
                if client does not exist in cs
        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.job_results_directory

        except Exception as err:
            self.log.info("Failed to compute Job results Directory")
            raise err

    def find_primary_copy_id(self, sp_id):
        """
        find the primary copy id of the specified storage policy

        Args:
                sp_id   (int)   : storage policy id

        Return:
                primary copy id of that storage policy
        """

        try:
            _query = "select copy from archgroup AG,archGroupCopy AGC where AGC.type = 1 and \
            AGC.isSnapCopy = 0 and  ag.id = AGC.archGroupId and AGC.archGroupId = '%s'" % sp_id

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred getting Sp details details")

            return _results[0]

        except Exception as err:
            self.log.exception("An Aerror occurred in find_primary_copy_id ")
            raise err

    def execute(self, query):
        """
        Executes the query passed and return the first row of value
        :param query: Query to be executed against CSDB
        :return:
            value : first row of query executed
        """

        try:
            self.csdb.execute(query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception {0} occurred in executing the query {0}".format(_results, query))

            return _results[0]

        except Exception as err:
            self.log.exception("An Aerror occurred in executing the db statements ")
            raise err

    def find_snap_copy_id(self, sp_id: object) -> object:
        """
        find the snap copy id of the specified storage policy

        Args:
                sp_id   (int)   : storage policy id

        Return:
                snap copy id of that storage policy
        """

        _query = "select copy from archgroup AG,archGroupCopy AGC where AGC.isSnapCopy = 1 and \
                                    ag.id = AGC.archGroupId and AGC.archGroupId = '%s'" % sp_id

        return self.execute(_query)

    def find_aux_copy_id(self, sp_id):
        """
        find the aux copy id of the specified storage policy

        Args:
                sp_id   (int)   : storage policy id

        Return:
                aux copy id of that storage policy
        """

        _query = "select copy from archgroup AG,archGroupCopy AGC where \
                            ag.id = AGC.archGroupId and AGC.archGroupId = '%s'" % sp_id

        return self.execute(_query)

    def find_app_aware_jobs(self, vsa_backup_job):
        """
        Get the workflow Job and IDA backup job id provided the VSA backup job
        :param vsa_backup_job:  VSA Backup Job ID
        :return:
            workflow_job : Work flow job ID for the VSA backup Job
            IDA_job      : IDA Job id for VSA backup job
        """

        try:
            _query = "select childjobId  from jmVSAAppJobLink \
                            where Parentjobid = %s" % vsa_backup_job
            ida_job_id = self.execute(_query)

            _query1 = "select workFlowjobId  from jmVSAAppJobLink\
                            where Parentjobid = %s" % vsa_backup_job
            workflow_job = self.execute(_query1)

            return ida_job_id, workflow_job

        except Exception as err:
            self.log.exception(
                "An Aerror {0} occurred in find_aux_copy_id ".format(err))
            raise err

    def check_for_BackupCopy_Job(self, subclient_id):
        """
        check for the backup copy jobs for the particular subclient
        :return:
            backupcopy_job_id : backup copy job id for the particualr subclient
        """

        try:

            _query = "select jobid from JMBkpJobInfo \
            where applicationId = {0}".format(subclient_id)
            backupcopy_job_id = self.execute(_query)

            return backupcopy_job_id

        except Exception as err:
            self.log.exception(
                "An Aerror {0} occurred in finding backup copy job id  ".format(err))
            raise err

    def check_cbt_status(self, backup_type, subclient_obj, job_id=None):
        """
        Check CBT status for the backed up VMs according to backup type

        Args:
                backup_type    (string) - FULL/INCR/DIFF/SYNTH_FULL
                subclient_obj   (obj) - Subclient sdk object
                job_id         (int) - Job ID for which CBT status is needed
                                         else last jobID is used
        Raise Exception:
                If CBt status for given VM for given backup type is unexpected
        """
        try:
            if job_id is None:
                job_id = subclient_obj.find_latest_job(include_active=False)
            if backup_type is "FULL":
                cbt_status = r'Enabled'
            else:
                cbt_status = r'Used'
            _query = "SELECT attrVal from APP_VMProp where attrName = 'vmCBTStatus' " \
                     " and jobId ={0}".format(job_id._job_id)
            self.csdb.execute(_query)

            _results = self.csdb.fetch_all_rows()

            for result in _results:
                if result[0] != cbt_status:
                    raise Exception("cbt_status for the VM is not {0}, it is {1}".format(result[0], cbt_status))

            self.log.info("The CBT status for all the VMs is {0} ".format(cbt_status))

        except Exception as err:
            self.log.exception(
                "Exception while checking the CBT status on the recent backuped VMs:" + str(err))
            raise err

    def find_job_transport_mode(self, vsa_backup_job):
        """
        Find and return the Transport mode for the job
        Args:
            vsa_backup_job:         (string)    Job id

        Returns:
            transport_mode          (string)    Transport mode of the job
        """
        try:
            _query = " select attrVal from APP_VMProp where attrName like 'vmTransportMode' and " \
                     "jobid = %s" % vsa_backup_job
            transport_mode = self.execute(_query)
            return transport_mode
        except Exception as err:
            self.log.exception(
                "Exception while getting transport mode for the job " + str(err))
            raise err

    def live_browse_get_ds_info(self, vsa_backup_job):
        """
        To get the list of DS currently mounted
        Args:
            vsa_backup_job:         (string)    Job id

        Returns:
            ds_list:                (list)      List of DS currently mounted
        """
        try:
            _query = "select MountDevice from SMVolume where SMVolumeId in " \
                     "(select SMVolumeId from SMSnapResource) and JobId=%s" % vsa_backup_job
            ds_list = self.execute(_query)
            return ds_list[0]
        except Exception as err:
            self.log.exception(
                "Exception while getting transport mode for the job " + str(err))
            raise err


class AutoVSAVSClient(object):
    """
    Main class for performing all VSClient operations

    Methods:
       enable_snap_on_client - Enable intellisnap on client

    """

    def __init__(self, commcell_obj, client):
        """
        Initialize all the class properties of AutoVSAVSClient class

        Args:
            commcell_obj    (obj)   - object of AutovsaCommcell class of VS Helper

            client  (obj)   - object for Client Class in SDK
        """
        self.log = logger.get_log()
        self.auto_commcell = commcell_obj
        self.csdb = commcell_obj.csdb
        self.vsa_client = client
        self.vsa_client_id = self.vsa_client.client_id
        self.vsa_client_name = self.vsa_client.client_name

    def enable_snap_on_client(self):
        """
        enable intellisnap on agent level

        Exception:
                If failed to update the property
        """
        try:
            self.vsa_client.enable_intelli_snap()
            self.log.info(
                "Success - enabled snap on client: [%s]", self.vsa_client_name)

        except Exception as err:
            self.log.error("Failed Enable Snap on client")
            raise Exception("Exception in EnableSnapOnClient:" + str(err))

    def live_mount_validation(
            self,
            vmpolicy,
            hvobj,
            live_mount_job,
            source_vm_name,
            mounted_network_name=None):
        """Live Mount the client for the specified vm policy name

            Args:
                vmpolicy                (obj)    --  SDK object to LiveMountPolicy class

                hvobj                   (obj)    --  HypervisorHelper object

                live_mount_job          (obj)    --  SDK object of Job class

                source_vm_name          (str)    --  source VM name for Live Mount

                mounted_network_name    (str)    --  optional network if provided

            Exception:
                if it fails to live mount the vm
        """
        try:
            # starting time to track expiration period
            start_time = time.time()
            vms_in_hypervisor = hvobj.get_all_vms_in_hypervisor()

            mounted_vm_name = vmpolicy.live_mounted_vm_name

            # check if vm is in vcenter
            if mounted_vm_name in vms_in_hypervisor:
                self.log.info(
                    "-" * 5 + ' Live Mounted VM: "{0}" found on vcenter: "{1}"'.
                    format(mounted_vm_name, hvobj.server_host_name) + "-" * 5)
                self.log.info("-" * 25 + " Validations while vm is mounted. " + "-" * 25)
                # 1. check if specified network is being used (before expiry time)
                self.log.info("-" * 15 + " Checking if specified network is being used " +
                              "-" * 15)
                # creating VMHelper object for source and client vm
                self.log.info("Creating VMHelper object for source and mounted VM.")
                hvobj.VMs = source_vm_name  # self.vsa_client_name
                hvobj.VMs = mounted_vm_name

                source_machine_vmhelper = hvobj.VMs[source_vm_name]  # self.vsa_client_name]
                mounted_machine_vmhelper = hvobj.VMs[mounted_vm_name]

                self.log.info("Updating VMHelper object for source and live mounted VM.")
                source_machine_vmhelper.update_vm_info(prop='All')
                mounted_machine_vmhelper.update_vm_info(prop='All')

                if not mounted_network_name:
                    mounted_network_name = source_machine_vmhelper.NetworkName

                if mounted_network_name != mounted_machine_vmhelper.NetworkName:
                    self.log.error(
                        'Live Mounted VM "{0}" NOT FOUND in the specified network "{1}".'
                            .format(mounted_vm_name, mounted_network_name))
                    raise Exception

                # else found in specified network
                self.log.info(
                    'Success - Live Mounted VM "{0}" found in the specified network: "{1}".'
                        .format(mounted_vm_name, mounted_network_name))
                # 2. validate test data in live mounted vm (before expiry time)

                # validating data in source vm and mounted vm
                self.log.info("-" * 15 + " Validating test data between source VM and mounted VM. "
                                         "-" * 15)
                self.log.info("Creating Machine objects for live mounted VM.")

                # checking if test data has been successfully written on mounted vm
                mounted_machine = mounted_machine_vmhelper.machine

                self.log.info("Fetching testdata path in source machine.")

                source_testdata_path = VirtualServerUtils.get_testdata_path(hvobj.machine)

                self.log.info("Starting testdata validation.")
                for _driveletter, _drive in mounted_machine_vmhelper.drive_list.items():
                    dest_testdata_path = VirtualServerConstants.get_folder_to_be_compared(
                        folder_name='FULL', _driveletter=_drive)
                    self.log.info(
                        'Validating test data in "{0}" drive.'.format(_drive))
                    self.fs_testdata_validation(dest_client=mounted_machine,
                                                source_location=source_testdata_path,
                                                dest_location=dest_testdata_path)
                    self.log.info(
                        'Test data in "{0}" drive has been validated.'.format(_drive))

                self.log.info("Test data validation completed successfully.")

                # 2.5 Make sure expiry time is over before proceeding to further validation
                days = int(vmpolicy.properties()['daysRetainUntil'])
                hours = int(vmpolicy.properties()['minutesRetainUntil'])
                expiration_time = hours * 60 * 60  # converting to seconds
                if days > 0:
                    expiration_time += days * 24 * 60 * 60  # converting to seconds
                expiration_time += (15 * 60)  # adding 15 mins extra before checking for unmount

                time_passed = time.time() - start_time

                self.log.info("-" * 25 + " Waiting for expiry time to finish " + "-" * 25)

                while time_passed < expiration_time:
                    diff_in_seconds = expiration_time - time_passed
                    diff_in_mins = math.ceil(diff_in_seconds / 60)
                    self.log.info("Time left for unmount: {0} minutes.".format(str(diff_in_mins)))
                    # sleeping for remaining time
                    self.log.info("Sleeping for {0} minutes.".format(diff_in_mins))
                    time.sleep(diff_in_seconds)
                    time_passed = time.time() - start_time
            else:
                self.log.error('Live Mounted VM "{0}" not found in vcenter "{1}".'.format(
                    mounted_vm_name, hvobj.server_host_name))
                raise Exception

            self.log.info("-" * 25 + " Expiration period is over " + "-" * 25)
            # ############ validations after vm is unmounted #################################
            # refreshing vm list in hypervisor
            vms_in_hypervisor = hvobj.get_all_vms_in_hypervisor()
            self.log.info("-" * 25 + " Validations after expiration period is over " + "-" * 25)
            self.log.info("-" * 25 + " Checking if VM is unmounted " + "-" * 25)
            # 3. check if vm unmounted (after expiry time)
            if mounted_vm_name not in vms_in_hypervisor:
                self.log.info("VM successfully unmounted from hypervisor {0}.".format(
                    hvobj.server_host_name))
                from cvpysdk.client import Client
                media_agent_name = vmpolicy.properties()['mediaAgent']['clientName']
                self.log.info("Creating Client object for media agent.")
                media_agent_client = Client(commcell_object=self.auto_commcell.commcell,
                                            client_name=media_agent_name)

                self.log.info("Creating Machine object for media agent.")
                media_agent_machine = Machine(machine_name=media_agent_name,
                                              commcell_object=self.auto_commcell.commcell)

                xml_file_path = media_agent_client.job_results_directory + '\\3dfs\\Exports.xml'
                xml_file_str = media_agent_machine.read_file(xml_file_path)
                xml_file_each_line = xml_file_str.split('\n')
                active_job_ids = []
                self.log.info("-" * 15 + " Checking Exports.xml in Job Results directory of Media "
                                         "Agent " + "-" * 15)
                for line in xml_file_each_line:
                    if "jobId" in line:
                        match = re.search('[\"]+\d+[\"]', line)
                        if match:
                            active_job_ids.append(match.group().strip('\"'))

                # check for active mounts in exports.xml of media agent
                active_mounts = False
                if active_job_ids:
                    active_mounts = True
                    self.log.info("Active mounts found on Media Agent.")
                else:
                    self.log.info("No active mounts found on Media Agent.")

                # check for job id in active job mounts
                if active_mounts and live_mount_job.job_id in active_job_ids:
                    self.log.info("Checking for existing mount on Media Agent.")
                    self.log.error(
                        'Job Id {0} still exists in Exports.xml of Media Agent {1}.'.
                            format(live_mount_job.job_id, media_agent_name))
                    raise Exception
                else:
                    self.log.info("Existing mount not found on Media Agent.")

                # 4. check if data store is unmounted (if no active mounts are present)
                self.log.info("-" * 25 + " Checking associated datastore " + "-" * 25)
                policy_datastore = vmpolicy.properties()['dataCenter']['dataCenterName']
                mounted_vm_datastore = (
                        policy_datastore + '_GX_BACKUP_0_' + media_agent_name + '_' +
                        mounted_machine_vmhelper.ESXHost)
                if not active_mounts:
                    self.log.info("Checking whether datastore is unmounted since there are no "
                                  "other active mounts.")
                    if mounted_vm_datastore in hvobj._get_datastore_dict()['Name']:
                        self.log.error(
                            'Datastore "{0}" not unmounted despite media agent "{1}" having no '
                            'active mounts.'.format(mounted_vm_datastore, media_agent_name))
                        raise Exception
                    else:
                        self.log.info("Datastore successfully unmounted.")
                else:
                    self.log.info("Since there are other active mounts, datastore is "
                                  "still mounted.")
            else:
                self.log.error('Live Mounted VM {0} not unmounted after expiration time from '
                               'hypervisor {1}.'.format(mounted_vm_name, hvobj.server_host_name))
                raise Exception
            # success message after validation is complete
            self.log.info("Success. Live Mount validation completed with no issues.")
        except Exception as err:
            self.log.error("Failed to Live Mount client: {0}.".format(source_vm_name))
            self.log.error("Exception in LiveMount: " + str(err))
            raise Exception

    def fs_testdata_validation(self, dest_client, source_location, dest_location):
        """
        Does Validation of live mounted vm comparing testdata in source client

        Args:
            source_client     (obj)   --  Machine class object of source client

            source_location   (str)   --  testdata path for source vm

            dest_client       (obj)   --  Machine class object of destination client

            source_location   (str)   --  testdata path for source vm

            dest_location     (str)   --  testdata path for live mounted vm

        Exception
                if folder comparison fails
        """
        try:
            self.log.info("Validating the testdata")

            controller_machine = Machine(socket.gethostname(), self.auto_commcell.commcell)

            difference = controller_machine.compare_folders(dest_client, source_location,
                                                            dest_location)

            if difference:
                self.log.info("checksum mismatched for files {0}".format(difference))

                raise Exception(
                    "Folder Comparison Failed for Source: {0} and destination: {0}".format(
                        source_location, dest_location))

            self.log.info("Validation completed successfully")

        except Exception as err:
            self.log.exception("Exception in FSTestdataValidation")
            raise err


class AutoVSAVSInstance(object):
    """
    Class for perfoming Instance operations. Act as wrapper for SDK and testcases

    Methods:
            get_instance_name()     - gets the isntnace name for the agent

            get_instance_id()       - get the instance id of the associated isntance

            get_proxy_list()        - gets the list of proxies associated with isntance

            _create_hyperviosr_object- Initialize objects for hypervisor helper

            _compute_credentials()   - computes the credentials for hyperviors

    """

    def __init__(self, auto_client, agent, instance):
        """
        Initialize all the class properties of AutoVSAVSInstance class

        Args:
                agent   (obj)   - object of Agent class in SDK

                instance(obj)   - object for Instance class in SDK
        """
        self.auto_vsaclient = auto_client
        self.csdb = auto_client.csdb
        self.auto_commcell = auto_client.auto_commcell
        self.vsa_agent = agent
        self.vsa_instance = instance
        self.vsa_instance_name = self.vsa_instance.instance_name
        self.vsa_instance_id = self.vsa_instance._instance_id
        self.log = self.auto_vsaclient.log
        self.sc_proxy_esx_host = None
        self.vsa_co_ordinator = None
        self.host_name = None
        self.vsa_proxy_list = self.get_proxy_list()
        self.hvobj = self._create_hypervisor_object()

    @property
    def proxy_list(self):
        """Returns Proxy list assocaited with that VSInstance . Read only attribute"""
        return self.vsa_proxy_list

    @proxy_list.setter
    def proxy_list(self, value):
        """
        set the list of Proxies as Proxy list in Instance level

        Args:
            value     (list) -list of proxies need to be set at instance level
        """
        try:
            self.vsa_instance.associated_clients = value

        except Exception as err:
            self.log.exception("An exception {0} has occurred \
                                while setting coordinator client ".format(err))

    @property
    def co_ordinator(self):
        """Retuens Proxy list assocaited witht hat VSInstance . Read only attribute"""
        if self.vsa_co_ordinator is None:
            self.vsa_co_ordinator = self.vsa_instance.co_ordinator

        return self.vsa_co_ordinator

    @co_ordinator.setter
    def co_ordinator(self, coordinator):
        """
        set the proxy given as coordinator

        Args:
            Coordinator - Proxy that needs to be set as coordinator
        """
        try:

            coordinator_client = self.auto_commcell.commcell.clients.get(coordinator)
            temp_vsa_proxy_list = [coordinator_client.client_name] + self.vsa_proxy_list
            self.vsa_proxy_list = list(set(temp_vsa_proxy_list))

            self.proxy_list = self.vsa_proxy_list

        except Exception as err:
            self.log.exception("An exception {0} has occurred \
                               while setting coordinator client ".format(err))

    @property
    def fbr_ma(self):
        """Returns FBRMA assocaited witht hat VSInstance . Read only attribute"""
        return self.vsa_instance.fbr_MA_Unix

    @fbr_ma.setter
    def fbr_ma(self, fbr_ma_name):
        """
        Set the Proxy as FBR Ma for that Instance

        Args:
            fbr_ma_name : Ma that needs to be set as FBR Ma
        """
        self.vsa_instance.fbr_MA_unix = fbr_ma_name

    @property
    def server_credentials(self):
        """Retuens Server Credentials assocaited witht hat VSInstance . Read only attribute"""
        return self.host_name, self.user_name

    def get_instance_name(self):
        """
        set Instance Id Provided Virtualization client name
        """
        try:
            return self.vsa_instance.instance_name

        except Exception as err:
            self.log.exception(
                "An Exception occurred in setting the Instance Type %s" % err)
            raise err

    def get_instance_id(self):
        """
        returns the Instance id of that instance

        Return:
            instnace_id - Instance id of Instance associated with VS isntance

        exception:
                If there is no Instance
        """
        try:
            return self.vsa_instance.instance_id

        except Exception as err:
            self.log.exception(
                "ERROR - exception while getting instance id Exception:" + str(err))
            raise err

    def get_proxy_list(self):
        """
        get the Proxy List for the instance

        returns
                v_proxy_list    (dict)-- dict with proxy name as key and its
                                                                        corresponding id as value

        Exception:
                if vsa_client does not exist in cs

                failed to get  Instance property
        """
        try:

            self.vsa_co_ordinator = self.vsa_instance.co_ordinator
            return self.vsa_instance.associated_clients

        except Exception as err:
            self.log.exception(
                "An Exception occurred in creating the Hypervisor object  %s" % err)
            raise err

    def _create_hypervisor_object(self, client_name=None):
        """
        Create Hypervisor Object

        Exception:
                if initialization fails in creating object
        """
        try:
            if client_name is None:
                client_name = self.auto_vsaclient.vsa_client_name
                instance = self.vsa_instance

            else:
                client = self.auto_commcell.commcell.clients.get(client_name)
                agent = client.agents.get('Virtual Server')
                instance_keys = next(iter(agent.instances._instances))
                instance = agent.instances.get(instance_keys)

            host_machine = instance.co_ordinator
            server_host_name = instance.server_host_name

            self._compute_credentials(client_name)
            hvobj = Hypervisor(server_host_name, host_machine, self.user_name,
                               self.password, self.vsa_instance_name, self.auto_commcell.commcell)

            return hvobj

        except Exception as err:
            self.log.exception(
                "An Exception occurred in creating the Hypervisor object  %s" % err)
            raise err

    def _compute_credentials(self, client_name):
        """Compute the credentials required to call the Vcenter"""

        try:
            _query = "Select attrval from APP_InstanceProp where attrname IN \
                      ('Virtual Server Password','Virtual Server User') and componentNameId = ( \
                      select TOP 1 instance  from APP_Application where clientId= ( \
                Select TOP 1 id from App_Client where name = '%s') and appTypeId = '106')" \
                     % client_name

            # """
            self.csdb.execute(_query)
            _results = self.csdb.fetch_all_rows()
            if not _results:
                raise Exception("An exception occurred getting server details")

            self.user_name = _results[0][0].strip()
            _password = _results[1][0].strip()
            # _password = _results[0][0].strip()
            # self.user_name = ".\\administrator"
            # self.password = "builder!12"
            self.password = cvhelper.format_string(self.auto_commcell.commcell, _password)
            # """
            # self.user_name = ".\\administrator"
            # self.password = "builder!12"

        except Exception as err:
            self.log.exception(
                "An Exception occurred in getting credentials for Compute Credentials  %s" % err)
            raise err

    def cbt_checks(self):
        try:
            host_dict = {}
            instanceno_dict = {}
            for each_proxy in self.proxy_list:
                host_name = self.auto_commcell.get_hostname_for_client(each_proxy)
                host_dict[each_proxy] = host_name
                instance_number = self.auto_commcell.get_instanceno_for_client(each_proxy)
                instanceno_dict[each_proxy] = instance_number
            self.hvobj.check_cbt_driver_running(self.proxy_list, host_dict)
            cbtstat_folder = self.hvobj.check_or_set_cbt_registry(self.proxy_list, host_dict, instanceno_dict)
            return cbtstat_folder
        except Exception as err:
            self.log.exception(
                "An Exception occurred in getting CBT driver status %s" % err)
            raise err


class AutoVSABackupset(object):
    """
    class for performing backupset operations. it acts as wrapper for Testcase and SDK
    """

    def __init__(self, instance_obj, backupset):
        """
        Initialize SDK objects

        Args:
            backupset   (obj)   - object for backupset class in SDK
        """
        self.auto_vsainstance = instance_obj
        self.auto_commcell = self.auto_vsainstance.auto_vsaclient.auto_commcell
        self.log = self.auto_vsainstance.log
        self.vsa_agent = self.auto_vsainstance.vsa_agent
        self.backupset = backupset
        self.backupset_name = self.backupset.backupset_name
        self.backupset_id = self.backupset.backupset_id


class AutoVSASubclient(object):
    """
    class for performing subclient operations. It act as wrapper for Testcase and SDK
    """

    def __init__(self, backupset_obj, subclient):
        """
        Initialize subclient SDK objects

        Args:
            subclient (obj) - object of subclient class of SDK
        """

        self.auto_vsa_backupset = backupset_obj
        self.log = self.auto_vsa_backupset.log
        self.auto_vsainstance = self.auto_vsa_backupset.auto_vsainstance
        self.auto_vsaclient = self.auto_vsainstance.auto_vsaclient
        self.vsa_agent = self.auto_vsainstance.vsa_agent
        self.auto_commcell = self.auto_vsainstance.auto_commcell
        self.csdb = self.auto_commcell.csdb
        self.hvobj = self.auto_vsainstance.hvobj
        self.subclient = subclient
        self.subclient_name = self.subclient.subclient_name
        self.subclient_id = self.subclient.subclient_id
        self._browse_ma_id = self.subclient.storage_ma_id
        self._browse_ma = self.subclient.storage_ma
        self.quiesce_file_system = True
        self._disk_filter = self.subclient.vm_diskfilter
        self._disk_filter_input = None
        self._vm_record = {}
        self.vm_filter = None
        self._vm_content = None
        self.vm_list = None
        self.backup_folder_name = None
        self.testdata_path = None
        self.disk_restore_dest = None
        self._is_live_browse = False
        self.ma_machine = None
        self.build_folder_path = None
        self._controller_machine = None
        self._is_windows_live_browse = False
        self.set_content_details()
        self.prepare_disk_filter_list()

    @property
    def pid(self):
        """
        :return: current running process id
        """
        #return str(os.getpid())
        return "2200"

    @property
    def controller_machine(self):
        """
        :return: Controller Machine machine class object
        """
        if not self._controller_machine:
            _controller_client_name = self.auto_commcell.get_client_name_from_hostname(socket.gethostname())
            self._controller_machine = Machine(_controller_client_name, self.auto_commcell.commcell)
        return self._controller_machine

    @property
    def storage_policy(self):
        """Returns storage policy associated with subclient.Read only attribute"""
        return self.subclient.storage_policy

    @storage_policy.setter
    def storage_policy(self, value):
        """
        Set the Specified Storage Policy

        Args:
            value - storage policy name

        Exception:
            if storage policy does not exist
        """
        self.subclient.storage_policy = value

    @property
    def storage_policy_id(self):
        """Returns storage policy id associated with subclient.Read only attribute"""
        sp_name = self.auto_commcell.commcell.storage_policies.get(
            self.storage_policy)
        return sp_name.storage_policy_id

    @property
    def vm_content(self):
        """
             Returns content  associated with subclient in the form of dict.Read only attribute

             Return:
                 content    (dict)  - with keys
                 {
                'allOrAnyChildren': True,
                'equalsOrNotEquals': True,
                'name': anme of the VM,
                'displayName': display name of the VM,
                'path': source path of the VM,
                'type': 9(VM),1(Host)
                        }

        """

        return self.subclient.content

    @vm_content.setter
    def vm_content(self, content):
        """
        set the specified content as content in subclient

        Args:
            content (str)   -   like [VM]=startswith=test*,test1
                                                        [VM] - represent type
                                                                        like [DNS],[HN]

                                                        startswith  represent equality in GUI
                                                                like endswith,equals

                                                        test* - include all VM starts with test
                                                               adding dyanamic contetn in GUI

                                                        , - to include multiple content

                                                        test1 -  non-dynamic content
        """
        self._vm_content = content
        self.set_content_details()

    @property
    def browse_ma(self):
        """
        Returns the browse MA from which the disk restore is perfomed
        It is read only attribute
        """
        return self._browse_ma, self._browse_ma_id

    def __deepcopy__(self, tempobj):
        """
        over ride deepcopy method to copy every attribute of an objevt to other
        """
        try:
            cls = tempobj.__class__
            result = cls.__new__(cls, tempobj, tempobj.vm_name)
            for k, v in tempobj.__dict__.items():
                setattr(result, k, v)
            return result

        except Exception as err:
            self.log.exception("Failed to deepcopy Exception:" + str(err))
            raise err

    def get_previous_full_backup(self, job_id):
        """
        Get the Previous full backup  for this subclient

        args:
                job_id  (int) - for which previous full has to be fetched

        Exception:
                if failed to get app id


        returns:
            job id  (int) - job id of the previous full backup of given current backup

        """
        try:
            _job_list = []
            _query = "Select id from APP_Application where instance = %s and \
                        backupSet = %s and subclientName = '%s'" % \
                     (self.auto_vsainstance.vsa_instance_id,
                      self.auto_vsa_backupset.backupset_id, self.subclient_name)

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred in getting previous full backup")

            _AppId = _results[0]

            _query1 = "Select jobId  from JMBkpStats where appId = %s and appType = %s \
                                    and bkpLevel = 1" % \
                      (_AppId, VirtualServerConstants.APP_TYPE)

            self.csdb.execute(_query1)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred in getting previous full backup")

            for each_result in _results:
                tempval = each_result[0]
                if tempval != job_id:
                    _job_list.append(tempval)

            _job_list.sort(reverse=True)

            return _job_list[0]

        except Exception as err:
            self.log.exception(
                "Failed to get Previous Full Job Exception:" + str(err))
            raise Exception("ERROR - exception while GetPreviousFULLBackup")

    def set_content_details(self):
        """
        Update the subclient details in subclient and prepares VM List

        Exception:
                if failed to update subclient
        """
        try:

            if self._vm_content is None:
                _vm_content_string = self._prepare_content_string_from_dict(
                    self.subclient.content)
                _vm_content_dict = self.subclient.content

            elif isinstance(self._vm_content, str):
                _vm_content_string = self._vm_content
                option, equality, pattern = self.split_content_string(
                    _vm_content_string)
                _vm_content_dict = self._prepare_content_dict_from_string(
                    option, pattern, equality)

            else:
                raise Exception("Failed in setting Subclient Content")

            # VM Filter string and dict
            _vm_filter_string, _vm_filter_dict = self.set_filter_details()

            # prepare VM List
            self.prepare_vm_list(_vm_content_string, _vm_filter_string)
            self.update_vsa_subclient_content(
                _vm_content_dict, _vm_filter_dict)

        except Exception as err:
            self.log.exception(
                "Failed to SetContentDetails Exception:" + str(err))
            raise err

    def set_filter_details(self):
        """
        Creates Filter string and dictionary can be with details for SDK API

        """
        try:

            _vm_filter_string = None
            _vm_filter_dict = {}

            if self.vm_filter is None:
                if self.subclient.vm_filter is not None:
                    _vm_filter_string = self._prepare_content_string_from_dict(
                        self.subclient.vm_filter)
                    _vm_filter_dict = self.subclient.vm_filter

            elif isinstance(self._vm_content, str):
                _vm_filter_string = self.vm_filter
                option, equality, pattern = self.split_content_string(
                    _vm_filter_string)
                _vm_filter_dict = self._prepare_content_dict_from_string(
                    option, pattern, equality)

            return _vm_filter_string, _vm_filter_dict

        except Exception as err:
            self.log.exception(
                "Failed to SetContentDetails Exception:" + str(err))
            raise err

    def _prepare_content_string_from_dict(self, content):
        """
        prepares string format of subclient content for preparing vm list

        Args:
                content (dict)  - with keys
                                         {
                                'equal_value': True,
                                'name': anme of the VM,
                                'display_name': display name of the VM,
                                'path': source path of the VM,
                                'type': Virtual Machine(VM),Host Name(Host)
                                        }

        returns:
                vm_content_string   -(str)  - [VM]=equals=test1
        """
        try:
            vm_content_string = ''
            for _each_vm in content:
                value = _each_vm["type"]
                _content_types = VirtualServerConstants.content_types
                _vm_display_name = _each_vm["display_name"]
                _option = _content_types[value]
                _pattern = _vm_display_name

                if _vm_display_name.startswith('*'):
                    _equality = "Ends with"
                    _pattern = _vm_display_name[1:]
                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + ","
                    vm_content_string = vm_content_string + _vm_content_string
                    continue

                elif _vm_display_name.endswith('*'):
                    _equality = "Starts with"
                    _pattern = _vm_display_name[:-1]
                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + ","
                    vm_content_string = vm_content_string + _vm_content_string
                    continue

                elif "*" in _vm_display_name:
                    if _each_vm["equal_value"]:
                        _equality = "Contains"
                    else:
                        _equality = "Does not Contains"

                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + ","
                    vm_content_string = vm_content_string + _vm_content_string
                    continue

                elif _each_vm["equal_value"]:
                    _equality = "Equals"
                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + ","
                    vm_content_string = vm_content_string + _vm_content_string
                    continue

                else:
                    _equality = "Does Not Equals"
                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + ","
                    vm_content_string = vm_content_string + _vm_content_string

            vm_content_string = vm_content_string[:-1]

            return vm_content_string

        except Exception as err:
            self.log.exception(
                "Failed to PrepareVMListfromSCContent Exception:" + str(err))
            raise err

    def get_maname_from_policy(self):
        """
        Get the MA Name from policy associated with subclient

        return:
                ma_name     (str)   - ma client name associated with SP

        Exception:
                if failed to get ma name
        """
        try:
            _query = "select DISTINCT AC.name  from MMDataPath MDP, APP_Client AC where \
                        MDP.HostClientId = AC.id AND MDP.CopyId in \
                    (select id from archGroupCopy where archGroupId = %s)" % self.storage_policy_id

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred in getting ma from policy")

            ma_name = _results[0]
            return ma_name

        except Exception as err:
            self.log.exception(
                "Failed to GetStoragePolicy Exception:" + str(err))
            raise err

    def update_vsa_subclient_content(self, vm_content_dict, vm_filter_dict):
        """
        Updates the VSA Subclient Content using SDK

        Args:
                vm_content_dict     (dict)  - dict in format to pass through SDK API

                vm_filter_dict      (dict)  - dict in format to pass through SDK API

        """

        try:

            # self.subclient.content = vm_content_dict

            # if vm_filter_dict != {}:
            # self.subclient.vm_filter = vm_filter_dict

            # if not(self._disk_filter == []):
            # self.PrepareDiskList()

            for each_vm in self.vm_list:
                if not hasattr(self.hvobj.VMs, each_vm):
                    self.hvobj.VMs = each_vm

                    # if not(self._disk_filter == []):
                    # self.PrepareDiskFilterList()

        except Exception as err:
            self.log.exception(
                "An Exception occurred in updating  the subclient %s" % err)
            raise err

    def get_vm_record_based_on_pattern(self, option, pattern, equality):
        """
        Get all the VM from hypervisor and  get the record of VM based on the pattern

        Args:
                option - [VM],[HN] -content is VM, Hostname etc..

                quality - startswith,equals etc.,

                pattern - pattern with wihich the option starts
        """
        try:

            if option == "[HN]":
                _hypervisor_vm_list = self.hvobj.get_all_vms_in_hypervisor(
                    pattern)

            elif (option == "[VM]") and (equality == "Equals"):
                _hypervisor_vm_list = [pattern]

            else:
                _hypervisor_vm_list = self.hvobj.get_all_vms_in_hypervisor()

            for _each_vm in _hypervisor_vm_list:
                if _each_vm not in self.hvobj.VMs.keys():
                    self.hvobj.VMs = _each_vm

        except Exception as err:
            self.log.exception(
                "An Exception occurred in getting VM record fpor all VMs in Hypervisor  %s" % err)
            raise err

    def _is_dyanamic_content(self, content):
        """
        Args:
                content     (str)   -- content in the form of [VM]=startswith=test*

        returns:
                non_dynamic_content_list    (list)  - returns the non dynamic content
                                                        like [VM]=equals=test1

                dynamic_content_list        (list)  - returns the dynamic content list
                                                        like [VM]=startswith-test1

        """
        try:
            dynamic_content_list = []
            non_dynamic_content_list = []
            _input_lists = content.split(":")
            for _input_list in _input_lists:
                _inputs = _input_list.split(",")
                for _input_string in _inputs:
                    # regex checek
                    _pattern_list = _input_string.split(
                        "=")  # individual items
                    if len(_pattern_list) != 3:
                        non_dynamic_content_list.append(_input_string)
                    else:
                        dynamic_content_list.append(_input_string)

            return non_dynamic_content_list, dynamic_content_list

        except Exception as err:
            self.log.exception(
                "Exception occurred in isDynamicContent.Error [%s]", str(err))
            raise err

    def _compute_vm_list_from_dynamic_content(self, content_list):
        """
    Phase I of dynamic content evaluation - Get all VM records in dictionary based on option given

        Args:
                content_list    (list)  - list of dynamic content string like [VM]=startswith=test*
        """
        try:

            for content in content_list:
                option, equality, pattern = self.split_content_string(content)
                self.get_vm_record_based_on_pattern(option, pattern, equality)
            if not self.hvobj.VMs:
                self.log.error("Error while retrieving VMs and their records")
                raise Exception("Error while retrieving VMs and their records")

            self.log.info("Records for all VMs are created successfully")

        except Exception as err:
            self.log.exception(
                "Exception in function ComputeVmListWithDynamicContent ")
            raise Exception(err)

    def _match_pattern_in_input(self, vm, equality, pattern):
        """
        It performs pattern matching. like the pattern is test* and
        if the Vm is test1 it returns True

        Args:
                vm -        (str)    - Name of the Vm against which mattern is need to be matched

                equality    (str)   - like equals, notequals

                pattern     (str)   -patterns which needs to bematched with the vm
                                                            like test*,test*1

        return:
                True        (bool)  - if the pattern matches the VM

                False       (bool)  -if the pattern does not matches for the VM

        """

        try:
            if (equality == "Equals") | (equality == "Does Not Equals"):
                match = re.search(pattern, vm, flags=re.I)
                if match:
                    return True
            elif (equality == "Contains") | (equality == "Does Not Contains"):
                pattern = ".*" + pattern + ".*"

            elif equality == "Starts with":
                pattern = pattern + ".*"

            elif equality == "Ends with":
                pattern = ".*" + pattern

            # pattern of the form ab*cd
            if (((pattern[len(pattern) - 1] != '*') & (pattern[len(pattern) - 1] != '+'))
                    & (pattern[0] != '.')):
                pattern = pattern + '$'
                match = re.match(pattern, vm, flags=re.I)

            elif pattern[0] != '.':  # pattern of the form abc*
                match = re.match(pattern, vm, flags=re.I)

            # pattern of the form *abc
            elif (pattern[len(pattern) - 1] != '*') & (pattern[len(pattern) - 1] != '+'):
                pattern = pattern + '$'
                match = re.search(pattern, vm, flags=re.I)

            else:  # pattern of the form *abc*
                match = re.search(pattern, vm, flags=re.I)

            if not match:
                self.log.info("Does not match")
                return False
            else:
                return True

        except Exception as err:
            self.log.exception("Exception while matching patterns. ")
            raise err

    def split_content_string(self, pattern_string):
        """
        split the content string to option equality pattern

        Args:
                pattern_string  (str)   - the input contetn string is [VM]=startswith=test*

        return:

                option = [VM] - represent the content is VM

                equality = startswith = the VM name shoudl starts with the test*

                pattern = test*

        """
        try:
            listvalue = pattern_string.split("=")
            if len(listvalue) == 3:
                option = (listvalue[0]).strip()
                equality = (listvalue[1]).strip()
                pattern = (listvalue[2]).strip()
                # commenting out filter string for now since its functionality
                # is done by MatchPatternforFilter
                # pattern = self.FetchPatterfromFilterString(equality, pattern)
                self.log.info("Input is evaluated successfully")
                return option, equality, pattern
            else:
                raise Exception("Input string id in not correct format")

        except Exception as err:
            self.log.exception("Exception while evaluating input. ")
            raise err

    def process_sc_input_for_vm_list(self, dynamic_content):
        """
        process the input contetn string and return the final set of Vms

        Args:
                dynamic_content (str)   - process the dynamic content [VM]=startswith=test*

        returns:
                qualified_list  (list)  - Qualified list of VMs like test1,test2,test3

        """
        try:
            _qualified_list = []
            _disqualified_list = []
            vm_list = self.hvobj.VMs.keys()

            def process_content(prop):
                for vm in vm_list:
                    _vm_prop_value = getattr(self.hvobj.VMs[vm], prop)
                    _retcode = self._match_pattern_in_input(
                        _vm_prop_value, equality, pattern)

                    if (((equality == "Does Not Equals") | (equality == "Does Not Contains"))
                            & (_retcode is True)):
                        _disqualified_list.append(vm)

                    elif _retcode:
                        _qualified_list.append(vm)

                return _qualified_list, _disqualified_list

            process_filter_dict = VirtualServerConstants.vm_pattern_names

            for content in dynamic_content:
                option, equality, pattern = self.split_content_string(content)
                _qualified_list, _disqualified_list = process_content(
                    process_filter_dict[option])

            self.log.info("Qualified list is made successfully.")

            _qualified_list = list(
                set(_qualified_list) - set(_disqualified_list))
            return _qualified_list

        except Exception as err:
            self.log.exception(
                "Exception while applying filters. Error [%s]", str(err))
            raise err

    def _process_vm_content(self, content):
        """
        process the VM content passed as input

        Args:
                content (str)   -   like [VM]=startswith=test*,test1
                                                        [VM] - represent type
                                                                        like [DNS],[HN]

                                                        startswith  represent equality in GUI
                                                                like endswith,equals

                                                        test* - include all VM starts with test
                                                               adding dyanamic contetn in GUI

                                                        , - to include multiple content

                                                        test1 -  non-dynamic content

                Return:
                        non_dynamic_content -   (list)  - list of Vms from non dynamic content

                        dynamic_list        -   (list)  - list of Vms from dynamic content


        """
        self.log.info("Processing VM content is %s" % content)
        try:
            self.log.info("getting VMs using GetVMlist()")
            non_dynamic_content = []

            non_dynamic_list, dynamic_content = self._is_dyanamic_content(content)

            if non_dynamic_list:
                for _each_content in non_dynamic_list:
                    _pattern_list = _each_content.split("=")
                    non_dynamic_content.append(_pattern_list[1])

            if len(dynamic_content) == 0:
                for _each_vm in non_dynamic_content:
                    if _each_vm not in self.hvobj.VMs.keys():
                        self.hvobj.VMs = _each_vm

                return non_dynamic_content, dynamic_content

            else:
                self._compute_vm_list_from_dynamic_content(dynamic_content)
                dynamic_list = self.process_sc_input_for_vm_list(
                    dynamic_content)

            return non_dynamic_content, dynamic_list

        except Exception as err:
            self.log.exception(
                "ERROR - VMList could be empty, please check the config file %s", str(err))
            raise err

    def prepare_vm_list(self, content_string=None, filter_string=None):
        """
        prepare the final set of VM list including filters

        Args:
                content_string  (str)   - content string given by user or fetched from
                                                            subclient (format: [VM]=equals=test1)

                filter_string   (str)   -filter string given by user or fetched from
                                                            subclient (format: [VM]=equals=test1)

        """
        try:
            if content_string is None:
                content_string = self._vm_content

            if filter_string is None:
                filter_string = self.vm_filter

            non_dynamic_content_list, dynamic_content_list = self._process_vm_content(
                content_string)

            if not ((filter_string == "") or (filter_string is None)):
                non_dynamic_filter_list, dynamic_filter_list = self._process_vm_content(
                    filter_string)
            else:
                non_dynamic_filter_list = []
                dynamic_filter_list = []

            _filter_list = list(non_dynamic_filter_list) + \
                           list(dynamic_filter_list)
            _final_dynamic_content_list = set(
                dynamic_content_list) - set(_filter_list)
            _vm_list = list(_final_dynamic_content_list) + \
                       list(non_dynamic_content_list)
            self.vm_list = list(set(_vm_list))

        except Exception as err:
            self.log.exception(
                "An exception occurred in Updating the Subclient Property")
            raise Exception(err)

    def _prepare_content_dict_from_string(self, option, pattern, equality=None, is_dynamic=False):
        """
        Create content in the for SDK API

        Args:
                option      - [VM],[HN] - Vms , HostNames

                equality    - like equals or not equals

                pattern     -  pattern like test1,test*

                is_dynamic  -   if it is dynamic or non dynamic content

        Return:
                vm content dict
                        content (dict)  - with keys
                                         {
                                'allOrAnyChildren': True,
                                'equalsOrNotEquals': True,
                                'name': anme of the VM,
                                'displayName': display name of the VM,
                                'path': source path of the VM,
                                'type': 9(VM),1(Host)
                                        }

        """
        try:
            # Add Name as pattern
            _vm_content_dict = {pattern: {}}
            _vm_content_dict[pattern]["name"] = pattern
            _vm_content_dict[pattern]["displayName"] = pattern
            _vm_content_dict[pattern]["path"] = ""

            if equality is not None:
                if (equality == "Does Not Equals") or (equality == "Does Not Contains"):
                    _vm_content_dict[pattern]["equalsOrNotEquals"] = False
                else:
                    _vm_content_dict[pattern]["equalsOrNotEquals"] = True

            else:
                _vm_content_dict[pattern]["equalsOrNotEquals"] = True

            if option == "[VM]":
                if is_dynamic:
                    _vm_content_dict[pattern]["type"] = "Virtual Machine"
                else:
                    _vm_content_dict[pattern]["type"] = "Virtual Machine"
                    _vm_content_dict[pattern]["path"] = self.hvobj.VMs[pattern].GUID

            else:
                con_type = [_key for _key, _value in VirtualServerConstants.content_types.items(
                ) if _value == option][0]
                _vm_content_dict[pattern]["type"] = "%s" % con_type

            return _vm_content_dict

        except Exception as err:
            self.log.exception(
                "An exception occurred in  CreateContentinSCFormat %s" % err)
            raise err

    def _process_disk_filter_string(self, controller_string):
        """
        proces the filter string to split it into controller , type number

        controller_string: Filter string that is from CS DB
        :return:
            controller_type (str) : it is scsi or ide
            number  (int)          : ilocation of scsi or ide

        """
        try:
            self.log.info("The Controller string is %s" % controller_string)
            controller_string = controller_string.strip()
            _controller_type = (controller_string.split("(")[0]).strip()
            _temp = (controller_string.split("(")[1]).strip()
            _controller_location_string = _temp.split(")")[0]
            _number, _location = _controller_location_string.split(":")
            return _controller_type, _number, _location

        except Exception as err:
            self.log.exception(
                "An exception occurred in  process_diks_filter_string %s" % err)
            raise err

    def prepare_disk_filter_list(self):
        """
        Prepares teh disk filter list by processing the pattern
        """
        try:

            disk_filter_list = []

            def process_control_filters(_VM, controller_type):
                controller_type, number, location = self._process_disk_filter_string(
                    controller_type)
                disk_path = self.hvobj.VMs[_VM]._get_disk_in_controller(controller_type, number, location)

                return disk_path

            def process_disk_path_filters(_VM, disk_path):
                disk_path = self.hvobj.VMs[_VM]._get_disk_path_from_pattern(disk_path)

                return disk_path

            diks_filter_process = {"3": process_control_filters, "2": process_disk_path_filters}
            for each_vm in self.vm_list:
                for each_filter in self._disk_filter:
                    disk_path = diks_filter_process[(each_filter['filterTypeId'])](each_vm, each_filter['filter'])
                    if disk_path is None or disk_path == "":
                        self.log.info(
                            "the criteria filter %s does not match this VM %s" % (each_filter['filter'], each_vm))
                    else:
                        disk_filter_list.append(disk_path)

            for each_vm in self.vm_list:
                for each_disk in disk_filter_list:
                    del self.hvobj.VMs[each_vm].disk_dict[each_disk]

            self.hvobj.VMs[each_vm].Diskcount = len(self.hvobj.VMs[each_vm].disk_list)

        except Exception as err:
            self.log.exception("Failed to PrepareDiskFilterListContent Exception:" + str(err))
            raise Exception("ERROR - exception while PrepareDiskFilterListContent")

    def _check_if_windows_live_browse(self, os_name, metadata_collected):
        """
        Decides Live browse validation need to be perfomred or not.

        Args:
                os_name             (str)   - os name of  backups VM

                metdata_collected   (bool)  - True on metadata collected , false on not collected

        return:
                True    - If live browse validation needs to be performed
                False   - if live browse validation need notto be performed

        """
        try:
            if (os_name == "Windows") and (not metadata_collected):
                return True

            else:
                return False

        except:
            self.log.exception(
                "An exception occurred in checking live browse validation neeeded")
            return False

    def vsa_discovery(self):
        """
        Creates testdata path and generate testdata and copy the test data to each drive in VM .
        """
        try:
            self.log.info("TesdataPath provided is %s" % self.testdata_path)
            self.log.info("creating test data directory %s" % self.testdata_path)
            self.log.info("Generating Test data folders")

            """
            generate = self.controller_machine.generate_test_data(self.testdata_path)
            if not generate:
                raise Exception(generate)
            # """
            for _vm in self.vm_list:
                self.hvobj.VMs[_vm].update_vm_info('All', True)
                for _label, _drive in self.hvobj.VMs[_vm].drive_list.items():
                    self.log.info("Copying Testdata to Drive %s" % _drive)
                    #self.hvobj.copy_test_data_to_each_volume(
                        #_vm, _drive, self.backup_folder_name, self.testdata_path)

        except Exception as err:
            self.log.exception(
                "Exception while doing VSA Discovery  :" + str(err))
            raise err

    def cleanup_testdata(self, backup_option):
        """
        Cleans up testdata that is copied from each vm in the subclient

        Args:
                backup_option   (obj)   -  object of Backup Options class in options
                                          helper contains all backup options
        """
        try:
            self.log.info("Testdata cleanup from subclient started")
            if not self.backup_folder_name:
                self.backup_folder_name = backup_option.backup_type
            for _vm in self.vm_list:
                self.log.info("VM selected is %s" % _vm)
                self.hvobj.VMs[_vm].update_vm_info('All', True)
                for _drive in self.hvobj.VMs[_vm].drive_list.values():
                    _testdata_path = os.path.join(_drive,
                                                  "\\" + self.backup_folder_name)
                    self.log.info("Cleaning up %s" % _testdata_path)
                    self.hvobj.VMs[_vm].machine.remove_directory(_testdata_path)
            self.log.info("clearing Testdata in controller")
            self.controller_machine.remove_directory(self.testdata_path)
        except Exception as err:
            self.log.exception(
                "Exception while doing cleaning up testdata Discovery  :" + str(err))
            raise err

    def backup(self, backup_option):
        """
        Submit VSA backup job

        Args:
                backup_option   (obj)   - object of Backup Options class in options
                                                    helper containes all backup options

        Raise Exception:
                if job does not complete successfully

        """
        try:
            self.backup_folder_name = backup_option.backup_type
            self.testdata_path = backup_option.testdata_path

            if not self.testdata_path:
                self.testdata_path = VirtualServerUtils.get_testdata_path(
                    self.hvobj.machine)

            self.vsa_discovery()

            """

            self.log.info("Starting Backup Job")

            _backup_job = self.subclient.backup(backup_option.backup_type,
                                                backup_option.run_incr_before_synth,
                                                backup_option.incr_level,
                                                backup_option.collect_metadata,
                                                backup_option.advance_options)

            if not _backup_job.wait_for_completion():
                raise Exception(
                    "Failed to run backup with error: " +
                    str(_backup_job.delay_reason)
                )
            self.backup_job_id = _backup_job.job_id
            self.log.info("Backup Job {0} completed successfully".format(
                self.backup_job_id))
            self.log.info("Backup Job got complete")
            self.log.info(
                "Checking if Job type is Expected for job ID {0}".format(self.backup_job_id))
            self.auto_commcell._check_backup_job_type_expected(
                self.backup_job_id, backup_option.backup_type)

            if hasattr(backup_option, "Application_aware") and backup_option.Application_aware:
                self.log.info("It is application Aware backup so checking for other jobs")
                ida_job_id, workflow_job_id = self.auto_commcell.find_app_aware_jobs(self.backup_job_id)
                ida_job = Job(self.auto_commcell.commcell, ida_job_id)
                workflow_job = Job(self.auto_commcell.commcell, workflow_job_id)

                if "Completed" not in (ida_job.status and workflow_job.status):
                    raise Exception(
                        "Ida job {0} or Workflow Job {0} failed , please check the logs".format(ida_job, workflow_job))

            if backup_option.backup_method == "SNAP":
                self.backupcopy_job_id = self.auto_commcell.check_for_BackupCopy_Job(self.subclient_id)
                backupcopy_job = Job(self.auto_commcell.commcell, self.backupcopy_job_id)
                if not backupcopy_job.wait_for_completion():
                    raise Exception(
                        "Failed to run backup copy job with error: " +
                        str(backupcopy_job.delay_reason)
                    )
            #"""

        except Exception as err:
            self.log.exception(
                "Exception while submitting Backup job:" + str(err))
            raise err

    def guest_file_restore(self, fs_restore_options):
        """

        perform Guest file restore for specific subclinet

        Args:
                fs_restore_options  -options that need to be set while performing guest fiel restore

        Exception:
                        if job fails
                        if validation fails

        """

        try:
            disk_count_before_restore = 0

            for _vm in self.vm_list:
                for label, _drive in self.hvobj.VMs[_vm].drive_list.items():

                    if "root" in _drive:
                        _preserve_level = int(fs_restore_options.preserve_level) + \
                                          self.hvobj.VMs[_vm].preserve_level
                    else:
                        _preserve_level = fs_restore_options.preserve_level

                    self.log.info("Restore dest path " +
                                  fs_restore_options.restore_path)
                    pid = str(os.getpid())
                    controller_machine = Machine(socket.gethostname(), self.auto_commcell.commcell)
                    if fs_restore_options.browse_from_snap:
                        _temp_vm, _temp_vmid = self.subclient._get_vm_ids_and_names_dict_from_browse()
                        _browse_request = self.subclient.guest_files_browse(_temp_vmid[_temp_vm[0]])
                        _path = self.find_snap_guest_file_path(_browse_request[1], _drive)
                        _fs_path_to_browse = self.controller_machine.join_path(_path, self.backup_folder_name,
                                                                               "TestData", self.pid)
                    else:
                        _fs_path_to_browse = self.controller_machine.join_path(_drive, self.backup_folder_name,
                                                                               "TestData", self.pid)
                    self.fs_restore_dest = self.controller_machine.join_path(fs_restore_options.restore_path,
                                                                             self.backup_folder_name,
                                                                             _vm, _drive.split(":")[0])

                    # """
                    self._is_windows_live_browse = self._check_if_windows_live_browse(
                        self.hvobj.VMs[_vm].GuestOS,
                        fs_restore_options.metadata_collected)

                    if not fs_restore_options.metadata_collected:
                        self.log.info("Getting the count of disk of Ma {0} before "
                                      "Guest file restore for live browse".
                                      format(fs_restore_options._browse_ma_client_name))

                        if self._is_windows_live_browse:
                            self.ma_machine = Machine(fs_restore_options._browse_ma_client_name,
                                                      self.auto_commcell.commcell)
                            self.ma_client_name = self.auto_commcell.commcell.clients.get(
                                fs_restore_options._browse_ma_client_name)
                        else:
                            self.ma_machine = Machine(fs_restore_options.fbr_ma,
                                                      self.auto_commcell.commcell)
                            self.ma_client_name = self.auto_commcell.commcell.clients.get(
                                fs_restore_options.fbr_ma)

                        disk_count_before_restore = self.ma_machine.get_disk_count()

                    fs_restore_job = self.subclient.guest_file_restore(_vm,
                                                                       _fs_path_to_browse,
                                                                       fs_restore_options.destination_client,
                                                                       self.fs_restore_dest,
                                                                       fs_restore_options.copy_precedence,
                                                                       _preserve_level,
                                                                       fs_restore_options.unconditional_overwrite,
                                                                       fbr_ma=fs_restore_options.fbr_ma)

                    if not fs_restore_job.wait_for_completion():
                        raise Exception(
                            "Failed to run file level restore  job with error: " +
                            str(fs_restore_job.delay_reason)
                        )

                    self.log.info("file level restore  Job got complete JOb Id:{0}".format(
                        fs_restore_job.job_id))

                    # """

                    # File level Validation
                    dest_client = Machine(fs_restore_options.destination_client,
                                          self.auto_commcell.commcell)
                    self.fs_testdata_validation(
                        dest_client, dest_client.join_path(self.fs_restore_dest,
                                                           "TestData", self.pid
                                                           ))

                    # """
                    if not fs_restore_options.metadata_collected and not fs_restore_options.browse_from_snap:
                        self.block_level_validation(disk_count_before_restore, _vm,
                                                    fs_restore_options._browse_ma_client_name)

                    # vmware live file cleanup validation
                    if self.hvobj.instance_type == "vmware" and fs_restore_options.browse_from_snap:
                        self.vmware_live_browse_validation(_vm, disk_count_before_restore, self.backup_job_id,
                                                           self.backupcopy_job_id)

            self.log.info(
                "Ran file level restore from all the VMs and its drives")

        except Exception as err:
            self.log.exception(
                "Exception at restore job please check logs for more details %s", str(err))
            self.log.info("Restore: FAIL - File level files Restore Failed")
            raise err

    def get_extent_count(self, db_path, db_name):
        """
        Get the extent number of extetnts in live browse DB
        :param db_path: db path of the livebrowse db
        :return:
            extent_count    (int)   - Number of extents in DB currently
        """

        try:

            utils_path = VirtualServerUtils.UTILS_PATH

            if not self.build_folder_path:
                extent_count_file = os.path.join(utils_path, "Extentcount.py")

                extent_setup_file = os.path.join(utils_path, "setup.py")

                db_file_path = os.path.join(db_path, db_name)
                with open(extent_count_file, 'r') as f_obj:
                    _script = f_obj.read()
                    _script = _script.replace('\xef\xbb\xbf', '')

                db_argument_list = re.findall(r'##Automation--([\w_]*)--##', _script)

                for argument in db_argument_list:
                    value = "{0}".format(db_file_path.strip())
                    _script = _script.replace('##Automation--{0}--##'.format(argument), value)

                extent_count_temp_file = os.path.join(utils_path, "Extentcounttemp.py")
                with open(extent_count_temp_file, 'w') as f_obj:
                    f_obj.write(_script)
                    f_obj.close()

                exe_command = "python \"" + extent_setup_file + "\"" + " build"
                output = self.controller_machine.execute_command(exe_command)

                build_path = os.path.join(utils_path, "build")
                if not os.path.exists(build_path):
                    raise Exception(output)
                self.ma_client_name.upload_folder(build_path, db_path)
                self.controller_machine.remove_directory(build_path)

                _build_folder = os.path.join(db_path, "build")
                if self.ma_machine.check_directory_exists(_build_folder):
                    self.build_folder_path = _build_folder

                else:
                    raise Exception("Failed to copy the extent exe folder")

            extent_count_exe_path = os.path.join(self.build_folder_path,
                                                 "Extentcounttemp.exe")
            cmd = "iex " + "\"" + "& " + "\'" + extent_count_exe_path + "\'\""
            output = self.ma_machine.execute_command(cmd)
            return int(output.formatted_output.strip())


        except Exception as e:
            self.log.exception("An exception occurred in getting extent count {0}".format(e))
            raise e

    def block_level_validation(self, disk_count_before_restore, _vm, browse_ma):
        """
        Perfoms Windows Block level validation
        :param disk_count_before_restore: disk count of Ma before performing guest file restore
        :param _vm: backup Vm for which guest level restore is performed
        :param browse_ma: Ma used for guest file restore browse
        Raise:
            Exception:
                when unmount fails
        """

        try:

            wait_time = 0
            error_count = 0
            pre_extent_count = 0

            print(self.hvobj.VMs[_vm].GuestOS)
            self.log.info("performing pruning validation on Browse MA {0}".format(browse_ma))
            _browse_ma_jr_dir = self.auto_commcell.get_job_results_dir(browse_ma)

            if self.hvobj.VMs[_vm].GuestOS == "Windows":
                while wait_time <= 500:
                    db_path = VirtualServerConstants.get_live_browse_db_path(_browse_ma_jr_dir)
                    db_name = VirtualServerUtils.find_live_browse_db_file(self.ma_machine, db_path)
                    current_extent_count = self.get_extent_count(db_path, db_name)

                    if current_extent_count > pre_extent_count:
                        self.log.info("Extentshould have reduced butincreasedwill waitfor 3 error")
                        error_count = error_count + 1
                        if error_count > 4:
                            raise Exception("pruning is not happening , please check logs")

                    pre_extent_count = current_extent_count
                    self.log.info("Waiting for 2 mins for next check")
                    time.sleep(120)
                    wait_time = wait_time + 120

                time.sleep(200)
            else:
                time.sleep(700)

            self.log.info("performing Post un-mount validation")
            # disk Un-mount validation
            self.disk_count_validation(disk_count_before_restore)
            # Path CleanUp Validation
            live_browse_mount_path = VirtualServerConstants.get_live_browse_mount_path(
                _browse_ma_jr_dir,
                self.hvobj.VMs[_vm].GUID,
                self.hvobj.VMs[_vm].GuestOS)
            files_in_path = self.ma_machine.get_files_in_path(live_browse_mount_path)
            if files_in_path:
                self.log.info("Not files are cleaned after Live browse, please check the folder %s"
                              % live_browse_mount_path)
                raise Exception("Staging Path CleanUp Failed")
            else:
                self.log.info("Staging Path %s was cleaned successfully" % live_browse_mount_path)

        except Exception as err:
            self.log.exception("Failed in performing Block Level Validation")
            raise err

    def fs_testdata_validation(self, dest_client, dest_location):
        """
        Does Validation of Backed up and data restored from file level

        Args:
                dest_client     (obj)   -   Machine class object of Destination client

                dest_location   (str)   - destination location of file level restore job


        Exception
                if folder comparison fails


        """
        self.auto_vsaclient.fs_testdata_validation(dest_client=dest_client,
                                                   source_location=self.testdata_path,
                                                   dest_location=dest_location)

    def disk_restore(self, disk_restore_options):
        """

        perform Disk restore for specific subclinet

        Args:
                disk_restore_options  (obj)  - represent options that need to be set
                                                    while performing disk  restore

        Exception:
                        if job fails
                        if validation fails

        """
        try:
            for _vm in self.vm_list:

                self.disk_restore_dest = os.path.join(
                    disk_restore_options.restore_path, self.backup_folder_name, _vm)

                # """
                disk_restore_job = self.subclient.disk_restore(
                    _vm, proxy_client=disk_restore_options.destination_client,
                    destination_path=self.disk_restore_dest,
                    copy_precedence=disk_restore_options.copy_precedence)

                if not disk_restore_job.wait_for_completion():
                    raise Exception(
                        "Failed to run disk  level restore  job with error: " +
                        str(disk_restore_job.delay_reason)
                    )
                self.log.info("Disk restore job completed successfully with job id {0}".format(disk_restore_job.job_id))
                # """
                if self.hvobj.VMs[_vm].GuestOS == "Windows":
                    # Commenting out validation for vmware disk level restore for now
                    if not self.hvobj.instance_type == "vmware":
                        self.disk_validation(
                            self.hvobj.VMs[_vm],
                            disk_restore_options._destination_pseudo_client,
                            self.disk_restore_dest,
                            disk_restore_options.client_machine)

                dest_client_hypervisor = self.auto_vsainstance._create_hypervisor_object(
                    disk_restore_options._destination_pseudo_client)
                dest_client_hypervisor.machine.remove_directory(self.disk_restore_dest)

        except Exception as err:
            self.log.exception("Exception occurred please check logs")
            raise Exception("Disk Restore Job failed, please check agent logs {0}".format(err))

    def disk_validation(self, vm_obj, destination_client_name, disk_restore_destination, dest_machine):
        """
        Performs Disk Validation by mounting the restored disk on the Host

        Args:

        _vm                     (str)   - object of VMHelper class

        destination_client_name    (str)   - Pseudo  client name of the destination client

        disk_restore_destination    (str)   - restore path of all the disk

        dest_machine    (obj) - destimation client where disk restores are performed

        Exception:
                        if job fails
                        if validation fails

        """
        try:

            self.log.info("Performed Restore in client %s" %
                          destination_client_name)
            dest_client_hypervisor = self.auto_vsainstance._create_hypervisor_object(
                destination_client_name)

            _list_of_disks = dest_client_hypervisor.get_disk_in_the_path(disk_restore_destination)

            _vm_disk_list = vm_obj.disk_list
            if not _vm_disk_list:
                self.log.info(
                    "Cannot validate the Disk as we cannot find the disk attached to the VM")
                return False

            if not ((_list_of_disks is None) or (_list_of_disks == [])):
                _final_mount_disk_list = []
                for each_disk in _vm_disk_list:
                    each_disk_name = os.path.basename(each_disk).split(".")[0]
                    for disk_path in _list_of_disks:
                        if each_disk_name in disk_path:
                            _final_mount_disk_list.append(disk_path)

            else:
                self.log.info(
                    "the Disk cannot be validated as we cannot find disk with Hypervisor extension,\
                                                                could be converted disk")
                return False

            if not _final_mount_disk_list:
                _final_mount_disk_list = _list_of_disks

            for _file in _final_mount_disk_list:

                _file = disk_restore_destination + "\\" + _file
                self.log.info("Validation Started For Disk :[%s]" % _file)
                _drive_letter = dest_client_hypervisor.mount_disk(vm_obj, _file, dest_machine)
                if _drive_letter != -1:
                    for each_drive in _drive_letter:
                        dest_folder_path = VirtualServerConstants.get_folder_to_be_compared(
                            self.backup_folder_name, each_drive)
                        self.log.info("Folder comparison started...")
                        time.sleep(5)
                        self.fs_testdata_validation(
                            dest_machine, dest_folder_path)
                else:
                    self.log.error("ERROR - Error mounting VMDK " + _file)
                    raise Exception("Exception at Mounting Disk ")

                dest_client_hypervisor.un_mount_disk(vm_obj, _file)

        except Exception as err:
            self.log.exception("Exception occurred please check logs")
            dest_client_hypervisor.un_mount_disk(vm_obj, _file)
            raise err

    def virtual_machine_restore(self, vm_restore_options):
        """
        perform Full VM restore for specific subclient

        Args:
                vm_restore_options  -options that need to be set while performing vm  restore

        Exception:
                        if job fails
                        if validation fails

        """
        try:

            #"""
            if vm_restore_options.in_place_overwrite:
                def hyperv():
                    vm_restore_job = self.subclient.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence,
                        add_to_failover=vm_restore_options.register_with_failover)
                    return vm_restore_job

                def vmware():
                    vm_restore_job = self.subclient.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def azureRM():
                    vm_restore_job = self.subclient.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def fusion_compute():
                    vm_restore_job = self.subclient.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                hv_dict = {"hyper-v": hyperv, "vmware": vmware, "azure resource manager": azureRM,
                           "fusioncompute": fusion_compute}
                vm_restore_job = (hv_dict[vm_restore_options.dest_auto_vsa_instance.vsa_instance_name.lower()])()

            else:
                def hyperv():
                    if self.backup_folder_name:
                        vm_restore_dest = os.path.join(vm_restore_options.destination_path,
                                                       self.backup_folder_name)
                    else:
                        vm_restore_dest = vm_restore_options.destination_path
                    vm_restore_options.destination_path = vm_restore_dest
                    vm_restore_job = self.subclient.full_vm_restore_out_of_place(
                        destination_client=vm_restore_options._destination_pseudo_client,
                        proxy_client=vm_restore_options.proxy_client,
                        destination_path=vm_restore_options.destination_path,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence,
                        add_to_failover=vm_restore_options.register_with_failover,
                        restore_option=vm_restore_options.advanced_restore_options)
                    return vm_restore_job

                def fusion_compute():
                    vm_restore_job = self.subclient.full_vm_restore_out_of_place(
                        destination_client=vm_restore_options._destination_pseudo_client,
                        proxy_client=vm_restore_options.proxy_client,
                        datastore=vm_restore_options.datastore,
                        host=vm_restore_options.host,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def vmware():
                    vm_restore_job = self.subclient.full_vm_restore_out_of_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        vcenter_client=vm_restore_options._dest_client_name,
                        datastore=vm_restore_options._datastore,
                        esx_host=vm_restore_options._host[0]
                    )
                    return vm_restore_job

                def azure():
                    vm_restore_job = self.subclient.full_vm_restore_out_of_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence,
                        resource_group=vm_restore_options.Resource_Group,
                        storage_account=vm_restore_options.Storage_account,
                        restore_option=vm_restore_options.advanced_restore_options)

                def oraclevm():
                    vm_restore_job = self.subclient.full_vm_restore_out_of_place(
                        virtualization_client=vm_restore_options._destination_pseudo_client,
                        destination_client=vm_restore_options.proxy_client,
                        repository=vm_restore_options.datastore,
                        server=vm_restore_options.host,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                hv_dict = {"hyper-v": hyperv, "fusioncompute": fusion_compute,
                           "vmware": vmware, "oraclevm": oraclevm, "azure resource manager": azure}
                vm_restore_job = (hv_dict[vm_restore_options.dest_auto_vsa_instance.vsa_instance_name.lower()])()

            if not vm_restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run VM  restore  job with error: " +
                    str(vm_restore_job.delay_reason)
                )

            # """

            for vm in self.vm_list:
                if vm_restore_options.in_place_overwrite:
                    restore_vm_name = vm
                else:
                    restore_vm_name = "Delete" + vm
                if vm_restore_options.restore_backup_job is not None:
                    self.vm_restore_validation(vm, restore_vm_name, vm_restore_options, 'Basic')
                else:
                    self.vm_restore_validation(vm, restore_vm_name, vm_restore_options)

        except Exception as err:
            self.log.error("Exception while submitting Restore job:" + str(err))
            raise err

    def vm_restore_validation(self, vm, restore_vm, vm_restore_options, prop='Advanced'):
        """
        Param:
             vm:                     -  Source Vm name
             restore_vm:             -  Restored VM Name
             vm_restore_options      -  options of VM restore options class
             prop                    -  only validate basic or advanced properties
        Exception:
            if validation fails

        """
        try:
            # self.hvobj.VMs[vm].update_vm_info('All')
            time.sleep(100)
            vm_restore_options.dest_client_hypervisor.update_hosts()
            if vm_restore_options.in_place_overwrite:
                self.log.info("it is Inplace restore")
                self.source_obj = self.__deepcopy__((self.hvobj.VMs[vm]))
            else:
                self.source_obj = self.hvobj.VMs[vm]

            on_premise = VirtualServerConstants.on_premise_hypervisor(
                vm_restore_options.dest_client_hypervisor.instance_type)
            if vm_restore_options.power_on_after_restore:
                vm_restore_options.dest_client_hypervisor.VMs = restore_vm
                vm_restore_options.dest_client_hypervisor.VMs[restore_vm].update_vm_info('All')
                self.restore_obj = vm_restore_options.dest_client_hypervisor.VMs[restore_vm]

                if vm_restore_options.in_place_overwrite and on_premise:
                    if not self.restore_obj.GUID == self.source_obj.GUID:
                        raise Exception("The GUID id of the in place restored VM does not match the source VM")
                if not self.restore_obj.NoofCPU == self.source_obj.NoofCPU:
                    raise Exception("The CPU count does not match for the source and restored VM")
                if not self.restore_obj.Diskcount == self.source_obj.Diskcount:
                    raise Exception("The disk count does not match for the source and restored VM")

                if prop == 'Basic':
                    if re.match(VirtualServerConstants.Ip_regex, "%s" % self.restore_obj.IP):
                        raise Exception("The IP address of the restored VM is not of the proper format"
                                        ". Boot validation failed.")
                else:
                    if ((not (re.match(VirtualServerConstants.Ip_regex, "%s" % self.restore_obj.IP))) and (
                            not (self.restore_obj.IP is None))):

                        for each_drive in self.source_obj.drive_list:
                            dest_location = self.controller_machine.join_path(self.source_obj.drive_list[each_drive],
                                                                              self.backup_folder_name, "TestData",
                                                                              self.pid)
                            self.fs_testdata_validation(self.restore_obj.machine, dest_location)
                    else:
                        self.log.info(
                            "This is Linux VM and the destination Ip is not proper ,"
                            "so no Data Validation cannot be performed")

            elif ((self.hvobj.VMs[vm].GuestOS == "Windows") and (
                    not vm_restore_options.in_place_overwrite) and (on_premise)):
                if self.hvobj.instance_type == "hyper-v":
                    dest_location = os.path.join(vm_restore_options.destination_path, restore_vm, "Virtual Hard Disks")
                    self.disk_validation(self.source_obj, vm_restore_options._destination_pseudo_client,
                                         dest_location, vm_restore_options.dest_machine)
                else:
                    self.log.info("Skipping disk validation for powered off restored vm for {0} instance".format(
                        self.hvobj.instance_type))
            else:
                self.log.info("This is Linux VM and the destination Ip is not proper,"
                              " so no Data Validation cannot be performed")

        except Exception as err:
            self.log.exception("Exception occurred in VM restore validation " + str(err))
            raise Exception("Exception in VM restore validation")

    def _get_all_backup_jobs(self):
        """
        Get all the backup jobs for the subclient
        :return:
            job_history     (dict)  -   all the unaged jobs for that subclient
                Ex:
                    {'job_cycle_1': {'bkp_level_full':  {'job_id':['aux_copy_jobid_1','aux_2']},
                                     'bkp_level_incr': {'job_id1':['aux1','aux2'],
                                                        'job_id2':['aux1','aux2']}
                                    },
                     'job_cycle_2': {'bkp_level_synth': {'job_id':['aux1','aux2']}
                                    }
                    }
        """
        job_history = {}

        _query = "select distinct BS.jobID, BS.bkpLevel, BS.fullCycleNum, DS.auxCopyJobId " \
                 "from JMBkpStats as BS join JMJobDataStats as DS ON BS.jobId = DS.jobId " \
                 "where BS.agedTime = 0 and BS.appId={0}".format(self.subclient_id)
        self.csdb.execute(_query)

        _results = self.csdb.fetch_all_rows()

        for result in _results:
            cycle_num = result[2].strip()
            job_id = result[0].strip()
            level = result[1].strip()
            aux_copy = result[3].strip()
            if cycle_num in job_history.keys():
                if level in job_history[cycle_num].keys():
                    if job_id in job_history[cycle_num][level].keys():
                        aux_jobs = job_history[cycle_num][level][job_id]
                        aux_jobs.append(aux_copy)
                        aux_jobs = list(set(aux_jobs))
                        try:
                            aux_jobs.remove('0')
                        except ValueError:
                            pass
                        job_history[cycle_num][level][job_id] = aux_jobs
                    else:
                        job_history[cycle_num][level][job_id] = [aux_copy]
                else:
                    job_history[cycle_num][level] = {job_id: [aux_copy]}
            else:
                job_history[cycle_num] = {level: {}}
                job_history[cycle_num][level] = {job_id: [aux_copy]}

        return job_history

    def create_ini_files(self):
        """
        Create a temp folder and files for storing and verifying changeID

        Raise Exception:
                If unable to create temp folder and files

        """
        try:
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            path_dir = os.path.join(_vserver_path, "TestCases", "CBT")
            if not self.controller_machine.check_directory_exists(path_dir):
                self.controller_machine.create_directory(path_dir)

            current_date = self.controller_machine.create_current_timestamp_folder(path_dir, "date")
            current_time = self.controller_machine.create_current_timestamp_folder(current_date, "time")
            self.controller_machine.create_file(os.path.join(current_time, "cbtStats.ini"), "$null")
            self.controller_machine.create_file(os.path.join(current_time, "usedChangeIDStatus.ini"), "$null")
        except Exception as err:
            self.log.exception(
                "Exception while creating files" + str(err))
            raise err

    def get_changeid_from_metadata(self, backup_type, backupjobid=None):
        """
        Get changeID generated for given backup job

        Args:
                backup_type    (String) - FULL/INCR/DIFF/SYNTH_FULL
                backupjobid    (int) - job ID of the backup job

        Raise Exception:
                If unable to get end time of given job

        """
        try:
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            path_dir = os.path.join(_vserver_path, "TestCases", "CBT")
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(path_dir)
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(curfolder)
            for each_vm in self.vm_list:
                vmguid = self.hvobj.VMs[each_vm].GUID
                pathtoBrowse1 = "\\" + vmguid
                fileToWriteTo = open(curfolder + "\\cbtStats.ini", "a")
                fileToWriteTo.write("\n[" + backup_type + "_" + each_vm + "]\n")
                fileToWriteTo.close()
                if backupjobid is None:
                    backupjobid = self.subclient.find_latest_job(include_active=False)
                response_json = self.get_metadata(backupjobid._job_id, pathtoBrowse1)
                self.write_changeid_tofile(response_json)
        except Exception as err:
            self.log.exception(
                "Exception while getting changeID from Metadata" + str(err))
            raise err

    def get_metadata(self, backupjobid, Pathtobrowse):
        """
        Get metadata for given backup job using browse request

        Args:
                backupjobid    (int) - job ID of the backup job
                Pathtobrowse   (int)   Guid of VM

        Raise Exception:
                If unable to get metdata from brose request 

        """
        try:
            options = {}
            options['path'] = Pathtobrowse
            options['_subclient_id'] = self.subclient_id
            _backup_job = Job(self.auto_commcell.commcell, backupjobid)
            from datetime import timezone, datetime
            temp_time = datetime.strptime(_backup_job.start_time, "%Y-%m-%d %H:%M:%S")
            from_time = temp_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
            from_time = datetime.strftime(from_time, "%Y-%m-%d %H:%M:%S")
            temp_time = datetime.strptime(_backup_job._end_time, "%Y-%m-%d %H:%M:%S")
            end_time = temp_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
            end_time = datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")
            options['from_time'] = from_time
            options['to_time'] = end_time
            options['media_agent'] = self._browse_ma
            options['show_deleted'] = True
            options['vm_disk_browse'] = True
            paths, response_json = self.auto_vsa_backupset.backupset.browse(options)
            return response_json
        except Exception as err:
            self.log.exception(
                "Exception while getting metadata using browse request" + str(err))
            raise err

    def write_changeid_tofile(self, response_json):
        """
        Find and write changeID generated for given backupjob to cbtStats.ini file

        Args:
                response_json    (string) Browse response received for given VM

        Raise Exception:
                If unable to find and write changeID 

        """
        try:
            # Open the file to write to
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            path_dir = os.path.join(_vserver_path, "TestCases", "CBT")
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(path_dir)
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(curfolder)
            fileToWriteTo = open(curfolder + "\\cbtStats.ini", "a")
            for key, value in response_json.items():
                for key1, value1 in value.items():
                    if 'name' in key1:
                        path_name = value1
                    if 'advanced_data' in key1:
                        for key2, value2 in value1.items():
                            if 'browseMetaData' in key2:
                                for key3, value3 in value2.items():
                                    if 'virtualServerMetaData' in key3:
                                        for key4, value4 in value3.items():
                                            if 'changeId' in key4:
                                                fileToWriteTo.write(path_name + ":" + value4 + "\n")
            fileToWriteTo.close()
        except Exception as err:
            self.log.exception(
                "Exception while finding and writing changeID to file " + str(err))
            raise err

    def parse_diskcbt_stats(self, cbtstat_folder, backup_type):
        """
        Find and copy cbt_stat file from hyperv to controller machine.
        And write changedID used by given backup to usedChangeIDStatus.ini file

        Args:
                cbtstat_folder    (string) Folder to which CBT stats are stored on HyperV
                backup_type      (string) FULL/INCR/DIFF/SYNTH_FULL

        Raise Exception:
                If unable to find and write changeID 

        """
        try:
            for each_vm in self.vm_list:
                # get CBTstat file and copy it on local system
                vmguid = self.hvobj.VMs[each_vm].GUID
                vmcbtstat_folder = os.path.join(cbtstat_folder, str(vmguid).upper())
                for each_proxy in self.auto_vsainstance.proxy_list:
                    proxy_machine = Machine(each_proxy, self.auto_commcell.commcell)
                    if proxy_machine.check_directory_exists(vmcbtstat_folder):
                        break
                _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
                cbt_folder = os.path.join(_vserver_path, "TestCases", "CBT")
                cbt_stat = os.path.join(_vserver_path, "TestCases", "CBTStats")
                destvmcbt_stat = os.path.join(cbt_stat, str(vmguid).upper())
                if proxy_machine.is_local_machine:
                    if not proxy_machine.check_directory_exists(destvmcbt_stat):
                        proxy_machine.create_directory(destvmcbt_stat)
                    proxy_machine.copy_folder(vmcbtstat_folder, destvmcbt_stat)
                else:
                    _dest_base_path = os.path.splitdrive(vmcbtstat_folder)
                    host_name = self.auto_commcell.get_hostname_for_client(each_proxy)
                    remote_vmcbtstat_folder = "\\\\" + host_name + "\\" + _dest_base_path[0].replace(
                        ":", "$") + _dest_base_path[-1]
                    if not self.controller_machine.check_directory_exists(destvmcbt_stat):
                        self.controller_machine.create_directory(destvmcbt_stat)
                        self.controller_machine.copy_files_from_network_share(destvmcbt_stat, remote_vmcbtstat_folder,
                                                                              self.auto_vsainstance.user_name,
                                                                              self.auto_vsainstance.password)
                proxy_machine.remove_directory(vmcbtstat_folder)
                self.log.info("Copied CBTstat folder at {0}".format(destvmcbt_stat))

                # Find and write changeID used
                curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(cbt_folder)
                curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(curfolder)
                fileToWriteTo = open(curfolder + "\\usedChangeIDStatus.ini", "a")
                fileToWriteTo.write("\n[" + backup_type + "_" + each_vm + "]\n")
                paths1 = [os.path.join(destvmcbt_stat, fn) for fn in next(os.walk(destvmcbt_stat))[2]]
                paths = []
                for element in paths1:
                    if "avhdx.txt" not in element.lower() and (".vhd" in element.lower() or ".vhdx" in element.lower()):
                        paths.append(element)
                previousChangedIDUsed = {}
                diskName = ""
                for file in paths:
                    statsFile = open(file, "r")
                    lines = statsFile.readlines()
                    for line in lines:
                        if "ChangeId from previous job : " in line:
                            changeIDLine = line
                            subStrChangeID = changeIDLine.index("[")
                            subStrChangeID2 = changeIDLine.index("]")
                            lenLine = len(line)
                            changeID = changeIDLine[subStrChangeID + 1:subStrChangeID2]
                            indexDash = file.rfind("-")
                            diskName = file[indexDash + 1:len(file) - 4]
                            previousChangedIDUsed[diskName] = changeID
                            fileToWriteTo.write(diskName + ":" + changeID + "\n")
                    statsFile.close()
                    os.remove(file)
                fileToWriteTo.close()
        except Exception as err:
            self.log.exception(
                "Exception while parsing and writing used changeID to file " + str(err))
            raise err

    def verify_changeid_used(self, backup_type):
        """
        Compare and verify if changeID generated by previous backupjob is used by next 
        backup job

        Args:
                backup_type      (string) FULL/INCR/DIFF/SYNTH_FULL

        Raise Exception:
                If unable to verify the changeID

        """
        try:
            import configparser
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            cbt_folder = os.path.join(_vserver_path, "TestCases", "CBT")
            currentfolder = self.controller_machine.get_latest_timestamp_file_or_folder(cbt_folder)
            currentfolder = self.controller_machine.get_latest_timestamp_file_or_folder(currentfolder)
            changeid_generatedfile = os.path.join(currentfolder, "cbtStats.ini")
            changeid_usedfile = os.path.join(currentfolder, "usedChangeIDStatus.ini")
            Config_Curr = configparser.ConfigParser(strict=False)
            Config_Curr.read(changeid_usedfile)
            Config_Prev = configparser.ConfigParser(strict=False)
            Config_Prev.read(changeid_generatedfile)
            if backup_type is "DIFFERENTIAL":
                cmp_bk_type = "FULL"
            else:
                cmp_bk_type = "INCREMENTAL"
            for each_vm in self.vm_list:
                if not Config_Prev.has_section(cmp_bk_type + "_" + each_vm):
                    cmp_bk_type = "FULL"
                currentDict = Config_Prev[cmp_bk_type + "_" + each_vm]
                previousDict = Config_Curr[backup_type + "_" + each_vm]
                for curKey in currentDict:
                    if currentDict[curKey].strip() != previousDict[curKey].strip():
                        self.log.info(
                            "Used incorrect change IDs for {0} backup for Disk {1}".format(backup_type,
                                                                                           curKey))
                        return False
                    else:
                        self.log.info(
                            "Used correct change IDs for {0} backup Disk {1}".format(backup_type, curKey))

            return True
        except Exception as err:
            self.log.exception(
                "Exception while verifying changeID used by job " + str(err))
            raise err

    def check_migrate_vm(self):
        """
        Check if more than one proxy/node is available and migrate to best possible node

        Raise Exception:
                If unable to check/migrate the vm

        """
        try:
            if len(self.auto_vsainstance.proxy_list) > 1:
                self.log.info("More than one node available to migrate the VM")
                for each_vm in self.vm_list:
                    self.hvobj.VMs[each_vm].migrate_vm()
            else:
                self.log.info("No other host is available for migration")
        except Exception as err:
            self.log.exception(
                "An Exception occurred while checking and if possible migrating VM to other node %s" % err)
            raise err

    def find_snap_guest_file_path(self, _browse_result, _drive_letter):
        """
        Get the Drive's Serial number
        Args:
            _browse_result:                     (dict)      guest file browse for vm from snap at vm level
            _drive_letter:      (               string)    drive for which the serial number is evaulated

        Returns:
            _browse_result['snap_display_name'] (string)    Serial number of the _drive_letter
        Raise Exception:
                If unable to verify the changeID
        """
        try:
            if "name" in _browse_result:
                if _browse_result['name'] == _drive_letter:
                    return _browse_result['snap_display_name']
            for k, v in _browse_result.items():
                if isinstance(v, dict):
                    item = self.find_snap_guest_file_path(v, _drive_letter)
                    if item is not None:
                        return item
        except Exception as err:
            self.log.exception(
                "Exception while getting guest file path for snap " + str(err))
            raise err

    def disk_count_validation(self, disk_count_before_restore):
        """
        Comparing the total number of disks before and after browse
        Args:
            disk_count_before_restore (int) :       Number of disk in the MA before Browse

        Returns:

        """
        try:
            self.log.info("Calculating the disk-count of the MA after restore")
            disk_count_after_restore = self.ma_machine.get_disk_count()
            self.log.info("Performing Live Browse Un-mount Validation")
            if (int(disk_count_before_restore)) >= (int(disk_count_after_restore)):
                self.log.info("Disk Unmounted Successfully")
            else:
                self.log.info(
                    "Failed to unmount disk, Number of Disk before restore:%s and Number of disk after restore:%s" % (
                        disk_count_before_restore, disk_count_after_restore))
                raise Exception("Failed to Un-mount Disk")
        except Exception as err:
            self.log.exception(
                "Exception while disk count validation " + str(err))
            raise err

    def vmware_live_browse_validation(self, _vm, disk_count_before_restore, snap_backup_job, backup_copy_job):
        """

        Args:
            _vm (str)   :       Name of the vm which was browsed and restored
            disk_count_before_restore (int) :       Number of disk on the controller before restore
            vsa_restore_job (int)   :       File level restore job id

        Returns:

        """
        try:
            if self.auto_commcell.find_job_transport_mode(backup_copy_job) == 'directsan':
                self.log.info("Validating Live Browse for Proxyless")
                self.log.info(" Sleeping for 11 minutes")
                time.sleep(700)
                self.disk_count_validation(disk_count_before_restore)
            else:
                self.log.info("Validating Live Browse for Traditional method")
                _flag = False
                _list_of_mounted_ds = self.auto_commcell.live_browse_get_ds_info(snap_backup_job)
                if self.hvobj.VMs[_vm].live_browse_vm_exists(_vm, snap_backup_job):
                    self.log.info(" Sleeping for 11 minutes")
                    time.sleep(700)
                    if not self.hvobj.VMs[_vm].live_browse_vm_exists(_vm, snap_backup_job):
                        self.log.info(" Sleeping for 3 minutes")
                        time.sleep(200)
                        if self.hvobj.VMs[_vm].live_browse_ds_exists(_list_of_mounted_ds):
                            _flag = True
                if _flag:
                    self.log.info("Live browse Validation successful")
                else:
                    self.log.info("Live Browse Validation failed")
                    raise Exception("Live Browse Validation failed")
        except Exception as err:
            self.log.exception(
                "Exception at Live browse validation %s", str(err))
            raise err
