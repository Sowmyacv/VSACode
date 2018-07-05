# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
main file for selcting all the options for all backups and restore

Class:
BackupOptions - class defined for setting all backup options
"""

import os
import re
from AutomationUtils import logger
from cvpysdk.job import Job
from AutomationUtils import machine
from . import VirtualServerHelper
from datetime import datetime


class BackupOptions(object):
    """
    Main class which handles all backup level options
    """

    def __init__(self, auto_vsasubclient):
        """
        Initializes all basic properties of performing backup
        """
        self.auto_vsasubclient = auto_vsasubclient
        self._backup_type = "FULL"
        self._backup_method = "REGULAR"
        self.testdata_path = None
        self.copy_precedence = "0"
        self.failed_vm_only = False
        self.granular_recovery = self.auto_vsasubclient.subclient.metadata
        self.overwrite = False
        self.use_impersonation = False
        self.resore_backup_job_id = None
        self.run_incr_before_synth = False
        self.copy_precedence_applicable = False
        self.granular_recovery_for_backup_copy = False
        self.run_backup_copy_immediately = True
        self._app_aware = False
        self.incr_level = 'BEFORE_SYNTH'
        self._advance_options = {}

    @property
    def data_set(self):
        """
        sets the path where the data set needs to be created
        It is read only attribute
        """
        return self.testdata_path

    @data_set.setter
    def data_set(self, path):
        """
        sets the path where the data set needs to be created

        args:
                path    (str)   - path where data needs to be created
        """
        self.testdata_path = path
        self.backup_folder_name = self.testdata_path.split("\\")[-1]

    @property
    def backup_type(self):
        """
        Type of backup to be performed
        It is read only attribute
        """

        return self._backup_type

    @backup_type.setter
    def backup_type(self, option):
        """
        Type of backup to be performed

        Args:
                optiion - Values: FULL, INCR,DIFF,SYNTH
        """
        self._backup_type = option

    @property
    def backup_method(self):
        """
        Backup Method like app or crash consistent
        It is read only attribute
        """
        return self._backup_method

    @backup_method.setter
    def backup_method(self, option):
        """
        Backup Method like app or crash consistent

        Args:
                option  - Appconsistent or Crashconsistent
        """
        self._backup_method = option

    @property
    def backup_failed_vm(self):
        """
        Backup the VM failed in Full Backup
        It is read only attribute
        """
        return self.failed_vm_only

    @backup_failed_vm.setter
    def backup_failed_vm(self, value):
        """
        Backup the VM failed in Full Backup

        Args:
                value (bool)     True or False based on needs to be set ot not
        """
        self.failed_vm_only = value

    @property
    def run_incremental_backup(self):
        """
        Run Incremental bakcup before synthic full
        It is read only attribute
        """
        return self.run_incr_before_synth

    @run_incremental_backup.setter
    def run_incremental_backup(self, value):
        """
        Run Incremental bakcup before synthic full
        Args:

        value   (bool)  - based on Incremental need to be run or not
        """
        self.run_incr_before_synth = True
        self.incr_level = value

    @property
    def collect_metadata(self):
        """
        Enable granular recovery for backup
        It is read only attribute
        """
        return self.granular_recovery

    @collect_metadata.setter
    def collect_metadata(self, value):
        """
        Enable granular recovery for backup
        Args:
                value   (bool) - based on value need to be set or not

        """
        self.granular_recovery = value
        self.auto_vsasubclient.subclient.metadata = self.granular_recovery

    @property
    def collect_metadata_for_bkpcopy(self):
        """
        Enable granular recovery for backup copy
        It is read only attribute
        """
        return self.granular_recovery_for_backup_copy

    @collect_metadata_for_bkpcopy.setter
    def collect_metadata_for_bkpcopy(self, value):
        """
        Enable granular recovery for backup copy
        Args:
                value   (bool) - based on value need to be set or not

        """
        self.granular_recovery_for_backup_copy = value

    @property
    def run_backupcopy_immediately(self):
        """
        Run backup copy immediately after snap backup
        It is read only attribute
        """
        return self.run_backup_copy_immediately

    @run_backupcopy_immediately.setter
    def run_backupcopy_immediately(self, value):
        """
        Run backup copy immediately after snap backup
        Args:
                value   (bool) - based on value need to be set or not

        """
        self.run_backup_copy_immediately = value

    @property
    def Application_aware(self):
        """
        Run backup copy immediately after snap backup
        It is read only attribute
        """
        return self._app_aware

    @Application_aware.setter
    def Application_aware(self, value):
        """
        Run backup copy immediately after snap backup
        Args:
                value   (bool) - based on value need to be set or not

        """
        self._app_aware = value

    @property
    def advance_options(self):
        """
        Setting up Advanced property for the file level backup
        Returns:
            _advance_options (str):     Advanced property fot backup
        """
        return self._advance_options

    @advance_options.setter
    def advance_options(self, value):
        """

        Args:
            value (dict) :       Dictionary for advanced option

        Returns:

        """
        self._advance_options = value


class FileLevelRestoreOptions(object):
    """
    Main class which handles all the option of file level restore

    init:

    subclient - (obj)    - subclient object of the cs

    set_destination_client()    - set the co-ordinator as the default destination client
                                                                        if not specified by user

    set_restore_path()            - set the path with maximum space as  default restore path  for
                                                            file level restore if not set as user

    """

    def __init__(self, subclient):
        self.auto_subclient = subclient
        self.log = logger.get_log()
        self._copy_precedence = 0
        self._overwrite = False
        self._preserve_level = 2
        self.use_impersonation = False
        self.restore_backup_job = None
        self.power_on = False
        self._granular_recovery = self.auto_subclient.subclient.metadata
        self.fs_acl = "ACL_DATA"
        self.copy_precedence_applicable = False
        self._start_time = 0
        self._end_time = 0
        self._dest_client_name = None
        self._browse_from_snap = False
        self._browse_from_backupcopy = False
        self._browse_from_auxcopy = False
        self._browse_ma_client_name, self._browse_ma_id = self.auto_subclient.browse_ma
        self._convert_disk_to = None
        self._dest_host_name = None
        self._destination_client = None
        self.client_machine = None
        self.impersonate_user_name = None
        self._restore_path = None
        self.granular_recovery = self.auto_subclient.subclient.metadata
        self.browse_ma_host_name = None
        self._fbr_ma = None
        self.set_destination_client()

    @property
    def destination_client(self):
        """
        Return destination client where disk are to be restored .
        It is read only attribute
        """
        return self._dest_client_name

    @destination_client.setter
    def destination_client(self, client_name):
        """
        set the particular client as destination client for disk restore

        Args:
        client_name     (str)   - client_name as configured in cs
        """
        self._destination_client = self.auto_subclient.auto_commcell.commcell.clients.get(client_name)
        self._dest_client_name = client_name
        self._dest_host_name = self._destination_client.client_hostname
        self.set_restore_path()

    @property
    def metadata_collected(self):
        """
        Enable granular recovery for backup
        It is read only attribute
        """
        return self.granular_recovery

    @metadata_collected.setter
    def metadata_collected(self, value):
        """
        Enable granular recovery for backup
        Args:
                value   (bool) - based on value need to be set or not

        """
        self.granular_recovery = value
        self.auto_subclient.subclient.metadata = value

    @property
    def fbr_ma(self):
        """
        Enable granular recovery for backup
        It is read only attribute
        """
        return self._fbr_ma

    @fbr_ma.setter
    def fbr_ma(self, value):
        """
        Enable granular recovery for backup
        Args:
                value   (bool) - based on value need to be set or not

        """
        self._fbr_ma = value

    @property
    def copy_precedence(self):
        """
        copy precedence from which disk restore needs to be performed
        It is read only attribute
        """
        return self._copy_precedence

    @copy_precedence.setter
    def copy_precedence(self, value=None):
        """
        set the copy precedence from which disk restore needs to be performed
        Args:
            value (int) - The copy precedeence of the copy from which
                            disk restore needs to be performed eg: 1
        """

        self.copy_precedence_applicable = True
        self._copy_precedence = value

    @property
    def browse_from_snap(self):
        """
        The property returns true if browse happened from snap
        It is read only attribute
        """
        return self._browse_from_snap

    @browse_from_snap.setter
    def browse_from_snap(self, value):
        """
        Property needs to be set if browse needs to be done from snap copy
        Args:
            value   (bool) - True if needs to browse from snap
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_snap_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def preserve_level(self):
        """
        The property returns default preserve level for file level restores
        It is read only attribute
        """
        return self._preserve_level

    @preserve_level.setter
    def preserve_level(self, value):
        """
        Property needs to be set if restore has to be done with  different preserve level
        Args:
            value   (int) - represent preserve level need to be set
        """
        self._preserve_level = value

    @property
    def browse_from_backup_copy(self):
        """
        The property returns true if browse happened from backup copy
        It is read only attribute
        """
        return self._browse_from_backupcopy

    @browse_from_backup_copy.setter
    def browse_from_backup_copy(self, value):
        """
        Property needs to be set if browse needs to be done from backup copy
        Args:
            value   (bool) - True if needs to browse from backup copy
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_primary_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_aux_copy(self):
        """
        The property returns true if browse happened from auxiliary copy
        It is read only attribute
        """
        return self._browse_from_auxcopy

    @browse_from_aux_copy.setter
    def browse_from_aux_copy(self, value):
        """
        Property needs to be set if browse needs to be done from auxiliary copy
        Args:
            value   (bool) - True if needs to browse from auxiliary copy
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_aux_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_restore_job(self):
        """
        Returns the job from which disk was restored
        it is read only attribute
        """
        return self._start_time, self._end_time

    @browse_from_restore_job.setter
    def browse_from_restore_job(self, job_id):
        """
        set the Job id from which the disk restore needs to be done
        Args:
            job_id (int)    - Backup job id from disk restore needs to be done
        """
        _job = Job(self.auto_subclient.auto_subclient.commcell, job_id)
        self._start_time = _job.start_time
        self._end_time = _job.end_time

    @property
    def browse_ma(self):
        """
        Returns the browse MA from which the disk restore is perfomed
        It is read only attribute
        """
        return self._browse_ma_client_name

    @browse_ma.setter
    def browse_ma(self, ma_name):
        """
        Set the browse MA from which the disk restore is perfomed
        Args:
            ma_name (str)   - MA Name from which disk restore needs to be performed
        """
        client = self.auto_subclient.auto_commcell.commcell.clients.get(ma_name)
        self._browse_ma_client_name = client.client_name
        self.browse_ma_host_name = client.client_hostname
        self._browse_ma_id = client.client_id

    @property
    def unconditional_overwrite(self):
        """
        returns if unconditional overwrite disk in place is set for disk restore
        It is read only attribute
        """
        return self._overwrite

    @unconditional_overwrite.setter
    def unconditional_overwrite(self, value):
        """
        set unconditional overwrite disk in place is set for disk restore
        Args:
            value (bool)    - True if needs to overwrite disk in place
        """
        self._overwrite = value

    @property
    def restore_path(self):
        """
        Returns the Restore path where disk is restored
        It is read only attribute
        """
        return self._restore_path

    @restore_path.setter
    def restore_path(self, value):
        """
        Set the restore path where the disk needs to be restored
        Args:
            value   (str) - Restore apth where disk needs to be restored
                            default :C:\CVAutoamtion
        """

        self._restore_path = value

    @property
    def impersonate_user(self):
        """
        returns the user if restored was triggered with some specific user
        It is read only attribute
        """
        return self.impersonate_user_name

    @impersonate_user.setter
    def impersonate_user(self, user_name):
        """
        set the user if restored was to be triggered with some specific user
        Args:
            user_name   (str)   - user with which the restore needs to be performed
        """
        self.impersonate_user_name = user_name
        self.use_impersonation = True

    @property
    def convert_disk_to(self):
        """
        returns the extension to which the disk was converted in disk restore if set
        It is read only attribute
        """
        return self._convert_disk_to

    @convert_disk_to.setter
    def convert_disk_to(self, value):
        """
        set the extension to which the disk needs to be  converted in disk restore
        Args:
            value   (str)   - extension to which it needs to be convereted
                                    eg:vmdk
        """
        self._convert_disk_to = value

    @property
    def restore_acl(self):
        """
        Return whether acl permission is set while restore . It is read only attribute
        """
        return self.fs_acl

    @restore_acl.setter
    def restore_acl(self, value):
        """
        Args:
             value: set whether acl permission need to be restored
        """
        self.fs_acl = value

    def set_destination_client(self):
        """
        set the default destiantion client ifg not given by user and path to restore in that client

        Exception:
            if client si not part of CS
        """
        try:
            if self._dest_client_name is None:
                self._dest_client_name = self.auto_subclient.auto_vsainstance.co_ordinator
                client = self.auto_subclient.auto_commcell.commcell.clients.get(
                    self._dest_client_name)
                self._dest_host_name = client.client_hostname

            self.set_restore_path()

        except Exception as err:
            self.log.exception("An Aerror occurred in SetDestinationClient ")
            raise err

    def set_restore_path(self):
        """
        set the restore path as CVAutomation in the drive with maximum storage space

        Exception:
            if failed to get storage details
            if failed to create directory
        """
        try:
            _temp_storage_dict = {}
            self.client_machine = machine.Machine(self._dest_client_name,
                                                  self.auto_subclient.auto_commcell.commcell)
            storage_details = self.client_machine.get_storage_details()
            _drive_regex = "^[a-zA-Z]$"
            for _drive, _size in storage_details.items():
                if re.match(_drive_regex, _drive):
                    _temp_storage_dict[_drive] = _size["available"]

            _maximum_storage = max(_temp_storage_dict.values())
            results = list(filter(lambda x: x[1] == _maximum_storage, _temp_storage_dict.items()))
            _dir_path = (results[0])[0] + ":\\CVAutomation"
            if not self.client_machine.check_directory_exists(_dir_path):
                self.client_machine.create_directory(_dir_path)

            self._restore_path = _dir_path

        except Exception as err:
            self.log.exception("An Error occurred in PopulateRestorePath ")
            raise err


class DiskRestoreOptions(object):
    """
    Main file for disk restore options in Automation

    set_destination_client()    - set the co-ordinator as the default destination client
                                                                        if not specified by user

    set_restore_path()            - set the path with maximum space as  default restore path  for
                                                            file level restore if not set as user

    """

    def __init__(self, subclient):
        """
        Initializes all basic properties of performing Disk restore

        Args:
            subclient - (obj)    - subclient object of the cs
        """
        self.auto_subclient = subclient
        self.log = logger.get_log()
        self._copy_precedence = None
        self._overwrite = False
        self.use_impersonation = False
        self.restore_backup_job = None
        self.power_on = False
        self.copy_precedence_applicable = False
        self._start_time = 0
        self._end_time = 0
        self._dest_client_name = None
        self._browse_from_snap = False
        self._browse_from_backupcopy = False
        self._browse_from_auxcopy = False
        self._browse_ma_client_name, self._browse_ma_id = self.auto_subclient.browse_ma
        self._convert_disk_to = None
        self._dest_host_name = None
        self._destination_client = None
        self._destination_pseudo_client = None
        self.client_machine = None
        self.impersonate_user_name = None
        self._restore_path = None
        self.browse_ma_host_name = None
        self.set_destination_client()

    @property
    def destination_client(self):
        """
        Return destination client where disk are to be restored .
        It is read only attribute
        """
        return self._dest_client_name

    @destination_client.setter
    def destination_client(self, client_name):
        """
        set the particular client as destination client for disk restore

        Args:
        client_name     (str)   - Pseudo client_name as configured in cs
        """
        self._destination_pseudo_client = client_name[0]
        self._destination_client = self.auto_subclient.auto_commcell.commcell.clients.get(client_name[1])
        self._dest_client_name = self._destination_client.client_name
        self._dest_host_name = self._destination_client.client_hostname
        self.set_restore_path()

    @property
    def copy_precedence(self):
        """
        copy precedence from which disk restore needs to be performed
        It is read only attribute
        """
        return self._copy_precedence

    @copy_precedence.setter
    def copy_precedence(self, value=None):
        """
        set the copy precedence from which disk restore needs to be performed
        Args:
            value (int) - The copy precedeence of the copy from which
                            disk restore needs to be performed eg: 1
        """

        self.copy_precedence_applicable = True
        self._copy_precedence = value

    @property
    def browse_from_snap(self):
        """
        The property returns true if browse happened from snap
        It is read only attribute
        """
        return self._browse_from_snap

    @browse_from_snap.setter
    def browse_from_snap(self, value):
        """
        Property needs to be set if browse needs to be done from snap copy
        Args:
            value   (bool) - True if needs to browse from snap
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_snap_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_backup_copy(self):
        """
        The property returns true if browse happened from backup copy
        It is read only attribute
        """
        return self._browse_from_backupcopy

    @browse_from_backup_copy.setter
    def browse_from_backup_copy(self, value):
        """
        Property needs to be set if browse needs to be done from backup copy
        Args:
            value   (bool) - True if needs to browse from backup copy
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_primary_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_aux_copy(self):
        """
        The property returns true if browse happened from auxiliary copy
        It is read only attribute
        """
        return self._browse_from_auxcopy

    @browse_from_aux_copy.setter
    def browse_from_aux_copy(self, value):
        """
        Property needs to be set if browse needs to be done from auxiliary copy
        Args:
            value   (bool) - True if needs to browse from auxiliary copy
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_aux_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_restore_job(self):
        """
        Returns the job from which disk was restored
        it is read only attribute
        """
        return self._start_time, self._end_time

    @browse_from_restore_job.setter
    def browse_from_restore_job(self, job_id):
        """
        set the Job id from which the disk restore needs to be done
        Args:
            job_id (int)    - Backup job id from disk restore needs to be done
        """
        _job = Job(self.auto_subclient.auto_subclient.commcell, job_id)
        self._start_time = _job.start_time
        self._end_time = _job.end_time

    @property
    def browse_ma(self):
        """
        Returns the browse MA from which the disk restore is perfomed
        It is read only attribute
        """
        return self._browse_ma_client_name

    @browse_ma.setter
    def browse_ma(self, ma_name):
        """
        Set the browse MA from which the disk restore is perfomed
        Args:
            ma_name (str)   - MA Name from which disk restore needs to be performed
        """
        client = self.auto_subclient.auto_commcell.commcell.clients.get(ma_name)
        self._browse_ma_client_name = client.client_name
        self.browse_ma_host_name = client.client_hostname
        self._browse_ma_id = client.client_id

    @property
    def unconditional_overwrite(self):
        """
        returns if unconditional overwrite disk in place is set for disk restore
        It is read only attribute
        """
        return self._overwrite

    @unconditional_overwrite.setter
    def unconditional_overwrite(self, value):
        """
        set unconditional overwrite disk in place is set for disk restore
        Args:
            value (bool)    - True if needs to overwrite disk in place
        """
        self._overwrite = value

    @property
    def restore_path(self):
        """
        Returns the Restore path where disk is restored
        It is read only attribute
        """
        return self._restore_path

    @restore_path.setter
    def restore_path(self, value):
        """
        Set the restore path where the disk needs to be restored
        Args:
            value   (str) - Restore apth where disk needs to be restored
                            default :C:\CVAutoamtion
        """

        self._restore_path = value

    @property
    def impersonate_user(self):
        """
        returns the user if restored was triggered with some specific user
        It is read only attribute
        """
        return self.impersonate_user_name

    @impersonate_user.setter
    def impersonate_user(self, user_name):
        """
        set the user if restored was to be triggered with some specific user
        Args:
            user_name   (str)   - user with which the restore needs to be performed
        """
        self.impersonate_user_name = user_name
        self.use_impersonation = True

    @property
    def convert_disk_to(self):
        """
        returns the extension to which the disk was converted in disk restore if set
        It is read only attribute
        """
        return self._convert_disk_to

    @convert_disk_to.setter
    def convert_disk_to(self, value):
        """
        set the extension to which the disk needs to be  converted in disk restore
        Artgs:
            value   (str)   - extension to which it needs to be convereted
                                    eg:vmdk
        """
        self._convert_disk_to = value

    def set_destination_client(self):
        """
        set the default destiantion client ifg not given by user and path to restore in that client

        Exception:
            if client si not part of CS
        """
        try:
            if self._dest_client_name is None:
                self.destination_client = (self.auto_subclient.auto_vsaclient.vsa_client_name,
                                           self.auto_subclient.auto_vsainstance.co_ordinator)

        except Exception as err:
            self.log.exception("An Aerror occurred in SetDestinationClient ")
            raise err

    def set_restore_path(self):
        """
        set the restore path as CVAutomation in the drive with maximum storage space
        Exception:
            if failed to get storage details
            if failed to create directory
        """
        try:
            _temp_storage_dict = {}
            self.client_machine = machine.Machine(self._dest_client_name,
                                                  self.auto_subclient.auto_commcell.commcell)
            storage_details = self.client_machine.get_storage_details()
            _drive_regex = "^[a-zA-Z]$"
            for _drive, _size in storage_details.items():
                if re.match(_drive_regex, _drive):
                    _temp_storage_dict[_drive] = _size["available"]

            _maximum_storage = max(_temp_storage_dict.values())
            results = list(filter(lambda x: x[1] == _maximum_storage, _temp_storage_dict.items()))
            _dir_path = (results[0])[0]+":\\CVAutomation"
            if not self.client_machine.check_directory_exists(_dir_path):
                self.client_machine.create_directory(_dir_path)

            self._restore_path = _dir_path

        except Exception as err:
            self.log.exception("An Error occurred in PopulateRestorePath ")
            raise err


class FullVMRestoreOptions(object):
    """
    Main class for full restore options in Automation
    """

    def __init__(self, subclient, testcase):
        """
        Initialize all class variables for Full VM restore

        init:

        subclient - (obj)    - subclient object of the cs

        inputs   - (dict)   - entire input dictionary passed for automation

        populate_hypervisor_restore_inputs()    - populate all the smart defaults
        """

        self.inputs = testcase.tcinputs
        self.testcase = testcase
        self.auto_subclient = subclient
        self.log = logger.get_log()
        self.perform_disk_validation = False
        self._copy_precedence = 0
        self._overwrite = False
        self.use_impersonation = False
        self._restore_backup_job = None
        self.advanced_restore_options = {}
        self.power_on = False
        self.copy_precedence_applicable = False
        self._start_time = 0
        self._end_time = 0
        self._browse_from_snap = False
        self._browse_from_backupcopy = False
        self._browse_from_auxcopy = False
        self._dest_client_name = None
        self._dest_host_name = None
        self.client_machine = None
        self.impersonate_user_name = None
        self._restore_path = None
        self.dest_machine = None
        self.browse_ma_host_name = None
        self.dest_client_hypervisor = None
        self._browse_ma_client_name, self._browse_ma_id = self.auto_subclient.browse_ma
        self.in_place = False
        self._proxy_client = None
        self.add_to_failover = False
        self._destination_client = None
        self.destination_path = ""
        self.Resource_Group = None
        self.Storage_account = None
        self.dest_auto_vsa_instance = None
        self.populate_hypervisor_restore_inputs()

    @property
    def destination_client(self):
        """
        Return destination client where disk are to be restored .
        It is read only attribute
        """
        return self._dest_client_name

    @destination_client.setter
    def destination_client(self, client_name):
        """
        set the particular client as destination client for disk restore

        Args:
        client_name     (str)   - client_name as configured in cs
        """

        self._destination_pseudo_client = client_name
        self._destination_client = self.auto_subclient.auto_commcell.commcell.clients.get(
            client_name)
        self._dest_client_name = self._destination_client.client_name
        self._dest_host_name = self._destination_client.client_hostname

    @property
    def copy_precedence(self):
        """
        copy precedence from which disk restore needs to be performed
        It is read only attribute
        """
        return self._copy_precedence

    @copy_precedence.setter
    def copy_precedence(self, value=None):
        """
        set the copy precedence from which disk restore needs to be performed

        Args:
            value (int) - The copy precedeence of the copy from which
                            disk restore needs to be performed eg: 1
        """

        self.copy_precedence_applicable = value
        self._copy_precedence = value

    @property
    def browse_from_snap(self):
        """
        The property returns true if browse happened from snap
        It is read only attribute
        """
        return self._browse_from_snap

    @browse_from_snap.setter
    def browse_from_snap(self, value):
        """
        Property needs to be set if browse needs to be done from snap copy
        Args:
            value   (bool) - True if needs to browse from snap
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_snap_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_backup_copy(self):
        """
        The property returns true if browse happened from backup copy
        It is read only attribute
        """
        return self._browse_from_backupcopy

    @browse_from_backup_copy.setter
    def browse_from_backup_copy(self, value):
        """
        Property needs to be set if browse needs to be done from backup copy
        Args:
            value   (bool) - True if needs to browse from backup copy
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_primary_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_aux_copy(self):
        """
        The property returns true if browse happened from auxiliary copy
        It is read only attribute
        """
        return self._browse_from_auxcopy

    @browse_from_aux_copy.setter
    def browse_from_aux_copy(self, value):
        """
        Property needs to be set if browse needs to be done from auxiliary copy
        Args:
            value   (bool) - True if needs to browse from auxiliary copy
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_aux_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_restore_job(self):
        """
        Returns the job from which disk was restored
        it is read only attribute
        """
        return self._start_time, self._end_time

    @browse_from_restore_job.setter
    def browse_from_restore_job(self, job_id):
        """
        set the Job id from which the disk restore needs to be done
        Args:
            job_id (int)    - Backup job id from disk restore needs to be done
        """
        _job = Job(self.auto_subclient.auto_commcell.commcell, job_id)
        self._start_time = _job.start_time
        self._end_time = _job.end_time

    @property
    def restore_backup_job(self):
        return self._restore_backup_job

    @restore_backup_job.setter
    def restore_backup_job(self, job_id):
        self._restore_backup_job = Job(self.auto_subclient.auto_commcell.commcell, job_id)
        self.advanced_restore_options['from_time'] = str(datetime.strftime(datetime.strptime(
            self._restore_backup_job.start_time, "%a %b %d %H:%M:%S %Y"), "%Y-%m-%d %H:%M:%S"))
        self.advanced_restore_options['to_time'] = str(datetime.strftime(datetime.strptime(
            self._restore_backup_job.end_time, "%a %b %d %H:%M:%S %Y"), "%Y-%m-%d %H:%M:%S"))

    @property
    def browse_ma(self):
        """
        Returns the browse MA from which the disk restore is perfomed
        It is read only attribute
        """
        return self._browse_ma_client_name

    @browse_ma.setter
    def browse_ma(self, ma_name):
        """
        Set the browse MA from which the disk restore is perfomed
        Args:
            ma_name (str)   - MA Name from which disk restore needs to be performed
        """
        client = self.auto_subclient.auto_commcell.commcell.clients.get(ma_name)
        self._browse_ma_client_name = client.client_name
        self.browse_ma_host_name = client.client_hostname
        self._browse_ma_id = client.client_id

    @property
    def unconditional_overwrite(self):
        """
        returns if unconditional overwrite disk in place is set for disk restore
        It is read only attribute
        """
        return self._overwrite

    @unconditional_overwrite.setter
    def unconditional_overwrite(self, value):
        """
        set unconditional overwrite disk in place is set for disk restore
        Args:
            value (bool)    - True if needs to overwrite disk in place
        """
        self._overwrite = value

    @property
    def restore_path(self):
        """
        Returns the Restore path where disk is restored
        It is read only attribute
        """
        return self._restore_path

    @restore_path.setter
    def restore_path(self, value):
        """
        Set the restore path where the disk needs to be restored
        Args:
            value   (str) - Restore apth where disk needs to be restored
                            default :C:\CVAutoamtion
        """

        self._restore_path = value

    @property
    def impersonate_user(self):
        """
        returns the user if restored was triggered with some specific user
        It is read only attribute
        """
        return self.impersonate_user_name

    @impersonate_user.setter
    def impersonate_user(self, user_name):
        """
        set the user if restored was to be triggered with some specific user
        Args:
            user_name   (str)   - user with which the restore needs to be performed
        """
        self.impersonate_user_name = user_name
        self.use_impersonation = True

    @property
    def power_on_after_restore(self):
        """
        Returns value of Power VM set in Full VM restore
        it is read only attribute
        """
        return self.power_on

    @power_on_after_restore.setter
    def power_on_after_restore(self, value):
        """
        set the value of power on option in Full VM restore

        Args:
            value   (bool)  - True if poweron option need to be set
        """
        self.power_on = value

    @property
    def in_place_overwrite(self):
        """
        Returns value of Overwrite set in Full VM restore
        it is read only attribute
        """
        return self.in_place

    @in_place_overwrite.setter
    def in_place_overwrite(self, value):
        """
        set the value of overwrite option in Full VM restore

        Args:
            value   (bool)  - True if overwrite option need to be set
        """
        self.in_place = value
        self._overwrite = value

    @property
    def register_with_failover(self):
        """
        Returns value of Overwrite set in Full VM restore
        it is read only attribute
        """
        return self.add_to_failover

    @register_with_failover.setter
    def register_with_failover(self, value):
        """
        This registers VM with Failover cluster

        Args:

        Value    (bool)     - True -  Register with Failover
            default:False

        """
        self.add_to_failover = value

    @property
    def proxy_client(self):
        """
        Returns value of Overwrite set in Full VM restore
        it is read only attribute
        """
        return self._proxy_client

    @proxy_client.setter
    def proxy_client(self, value):
        """
        This registers VM with Failover cluster

        Args:

        Value    (bool)     - True -  Register with Failover
            default:False

        """
        _proxy = self.auto_subclient.auto_commcell.commcell.clients.get(value)
        self._proxy_client = _proxy.client_name

    def _process_inputs(self, attr_to_set, user_input):
        """
        will process all the inputs from user and set it as calss variable

        attr_to_set    (str)    - property need to eb set as class variable

        user_input    (str)    - property  to be set as class variable that is passed from user

        Exception:
            if the property is not given in user input
        """
        try:
            if user_input in self.inputs.keys():
                setattr(self, attr_to_set, self.inputs[user_input])
            else:
                self.log.info("The Tag %s is not specified by the user" % user_input)
                setattr(self, attr_to_set, None)

        except Exception as err:
            self.log.exception("An Aerror occurred in setting hypervisor tags")
            raise err

    def populate_hypervisor_restore_inputs(self):
        """
        populate all the hypervisor defaults for the full VM restore

        Exception:
            if failed to compute default VSA Client

            if failed to compute proxy and Datastores and Host

        """
        try:
            instance_name = self.auto_subclient.auto_vsainstance.vsa_instance_name

            def hyperv():
                proxy_host_list = []

                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if "RestoreHyperVServer" not in self.inputs:
                    host_dict = {}
                    proxy_list = self.dest_auto_vsa_instance.proxy_list
                    for each_proxy in proxy_list:
                        host_name = self.auto_subclient.auto_commcell.get_hostname_for_client(each_proxy)
                        proxy_host_list.append(host_name)
                        host_dict[each_proxy] = host_name

                    self.proxy_client, datastore = self.dest_client_hypervisor.compute_free_resources(
                        proxy_list, host_dict, vm_list)

                else:
                    self.proxy_client = self.inputs["RestoreHyperVServer"]

                self.dest_machine = machine.Machine(self.proxy_client,
                                                    self.auto_subclient.auto_commcell.commcell)

                # setting Destination path in VSA Client
                if "DestinationPath" not in self.inputs:
                    _dir_path = os.path.join(datastore, "\\CVAutomation")
                    if not self.dest_machine.check_directory_exists(_dir_path):
                        self.dest_machine.create_directory(_dir_path)

                    self.destination_path = _dir_path

                else:
                    self.destination_path = self.inputs["DestinationPath"]

            def vmware():
                proxy_host_list = []
                vm_list = self.auto_subclient.vm_list
                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if (("datastore" not in self.inputs) and
                        ("host" not in self.inputs) and
                        ("cluster" not in self.inputs) and
                        ("datacenter" not in self.inputs)):

                    self._datastore, self._host, self._cluster, self._datacenter = \
                        self.dest_client_hypervisor.compute_free_resources(vm_list)

                else:
                    self._dest_client_name = self.inputs["RestoreVcenter"]
                    self._datastore = self.inputs["RestoreVcenter"]
                    self._host = self.inputs["host"]
                    self._cluster = self.inputs["cluster"]
                    self._datacenter = self.inputs["datacenter"]

                self._dest_client_name = self.destination_client

            def fusion_compute():
                proxy_host_list = []
                self.power_on_after_restore = True
                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                                                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if (("Host" not in self.inputs) and
                        ("Datastore" not in self.inputs)):

                    self.datastore, self.host = self.dest_client_hypervisor.compute_free_resources(vm_list,
                                                                                                   self.proxy_client)

                else:
                    self.host = self.inputs["Host"]
                    self.datastore = self.inputs["Datastore"]
                    
            def AzureRM():

                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj

                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if (("Resourcegroup" not in self.inputs) and
                        ("Storageaccount" not in self.inputs)):

                    esx_host, datastore = self.dest_client_hypervisor.compute_free_resources(vm_list)
                    self.Resource_Group = esx_host
                    self.Storage_account = datastore

                else:
                    self.Resource_Group = self.inputs["Resourcegroup"]
                    self.Storage_account = self.inputs["Storageaccount"]

            def oraclevm():
                self.power_on_after_restore = True
                vm_list = self.auto_subclient.vm_list

                self.destination_client = self.inputs.get(
                    "virtualizationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                               self.testcase.agent,
                                                                               self.testcase.instance)

                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                                                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if (("Host" not in self.inputs) and
                        ("Datastore" not in self.inputs)):

                    self.host, self.datastore = self.dest_client_hypervisor.compute_free_resources(vm_list)

                else:
                    self.host = self.inputs["Host"]
                    self.datastore = self.inputs["Datastore"]

            hv_dict = {"hyper-v": hyperv, "vmware": vmware, "fusioncompute": fusion_compute,
                       "oraclevm": oraclevm, "azure resource manager": AzureRM}
            (hv_dict[instance_name])()

        except Exception as err:
            self.log.exception("An error occurred in setting hypervisor tags")
            raise err
