"""
main file for selcting all the options for all backups and restore

Class:
BackupOptions - class defined for setting all backup options
"""

from AutomationUtils import logger
import os, re
from cvpysdk.job import Job
from AutomationUtils import machine



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
		self.copy_preceedence = "0"
		self.failed_vm_only = False
		self.granular_recovery = False
		self.overwrite = False
		self.use_impersonation = False
		self.resore_backup_job_id = None
		self.run_incr_before_synth = False
		self.copy_preceedence_applicable = False
		self.granular_recovery_for_backup_copy = False
		self.run_backup_copy_immediately = True
		self.incr_level = 'BEFORE_SYNTH'


	@property
	def data_set(self): return self.testdata_path

	@data_set.setter
	def data_set(self, path):
		"""
		sets the path where the data set needs to be created
		
		args:
			path	(str)	- path where data needs to be created
		"""
		self.testdata_path = path
		self.backup_folder_name = self.testdata_path.split("\\")[-1]

	@property
	def backup_type(self): return self._backup_type

	@backup_type.setter
	def backup_type(self, option):
		"""
		Type of backup to be performed
		
		Args:
			optiion - Values: FULL, INCR,DIFF,SYNTH
		"""
		self._backup_type = option

	@property
	def backup_method(self): return self._backup_method

	@backup_method.setter
	def backup_method(self, option):
		"""
		Backup Method like app or crash consistent
		
		Args:
			option	- Appconsistent or Crashconsistent
		"""
		self._backup_method = option

	@property
	def backup_failed_vm(self): return self.failed_vm_only

	@backup_failed_vm.setter
	def backup_failed_vm(self, value):
		"""
		Backup the VM failed in Full Backup
		
		Args:
			value (bool)	 True or False based on needs to be set ot not
		"""
		self.failed_vm_only = value

	@property
	def run_incremental_backup(self): return self.run_incr_before_synth

	@run_incremental_backup.setter
	def run_incremental_backup(self, value):
		"""
		Run Incremental bakcup before synthic full
		Args:
		
		value	(bool)	- based on Incremental need to be run or not
		"""
		self.run_incr_before_synth = True
		self.incr_level = value


	@property
	def collect_metadata(self): return self.granular_recovery

	@collect_metadata.setter
	def collect_metadata(self, value):
		"""
		Enable granular recovery for backup
		Args:
			value	(bool) - based on value need to be set or not
		
		"""
		self.granular_recovery = value

	@property
	def collect_metadata_for_bkpcopy(self): return self.granular_recovery_for_backup_copy

	@collect_metadata_for_bkpcopy.setter
	def collect_metadata_for_bkpcopy(self, value):
		"""
		Enable granular recovery for backup copy
		Args:
			value	(bool) - based on value need to be set or not
		
		"""
		self.granular_recovery_for_backup_copy = value

	@property
	def run_backupcopy_immediately(self):
		return self.run_backup_copy_immediately

	@RunBkpCopyImmediately.setter
	def run_backupcopy_immediately(self, value):
		"""
		Run backup copy immediately after snap backup
		Args:
			value	(bool) - based on value need to be set or not
		
		"""
		self.run_backup_copy_immediately = value

class File_level_restore_options(object):
	"""
	Main class which handles all the option of file level restore

	init:

	subclient - (obj)	- subclient object of the cs

	set_destination_client()	- set the co-ordinator as the default destination client
                                                                        if not specified by user

	set_restore_path()			- set the path with maximum space as  default restore path  for
                                                            file level restore if not set as user

	"""
	def __init__(self, auto_subclient):
		self.auto_subclient = auto_subclient
		self.log = logger.get_log()
		self._copy_preceedence = None
		self._overwrite = False
		self._granular_recovery = False
		self._restore_backup_job_id = None
		self.fs_acl = "ACL_DATA"
		self.copy_preceedence_applicable = False
		self._start_time = 0
		self._end_time = 0
		self._browse_from_snap = False
		self._browse_from_backupcopy = False
		self._browse_from_auxcopy = False
		self.restore_client_is_local = False
		self._dest_client_name = None
		self._browse_ma_client_name, self._browse_ma_id = self.auto_subclient.subclient.browse_ma
		self.set_destination_client()


	@property
	def DestinationClient(self): return self._dest_host_name

	@DestinationClient.setter
	def DestinationClient(self, client_name):
		client = self.auto_subclient.auto_commcell.commcell.clients.get(client_name)
		self._dest_client_name = client_name
		self._dest_host_name = client.host_name
		self.set_restore_path()

	@property
	def CollectMetadata(self): return self._granular_recovery

	@CollectMetadata.setter
	def CollectMetadata(self, value):
		self._granular_recovery = value

	@property
	def CopyPreecedence(self): return self._copy_preceedence

	@CopyPreecedence.setter
	def CopyPreecedence(self, value = None):
		self.copy_preceedence_applicable = True
		self._copy_preceedence = value

	@property
	def BrowseFromSnap(self):
		return self._browse_from_snap

	@BrowseFromSnap.setter
	def BrowseFromSnap(self, Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_snap_copy_id(
                                                                        self.auto_subclient.sp_id)

	@property
	def BrowsefromBackupCopy(self):
		return self._browse_from_backupcopy

	@BrowsefromBackupCopy.setter
	def BrowsefromBackupCopy(self, Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_primary_copy_id(
                                                                        self.auto_subclient.sp_id)

	@property
	def BrowsefromAuxcopy(self):
		return self._browse_from_auxcopy

	@BrowsefromAuxcopy.setter
	def BrowsefromAuxcopy(self, Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_aux_copy_id(
                                                                        self.auto_subclient.sp_id)

	@property
	def BrowseFromRestoreJob(self): return self._start_time, self._end_time

	@BrowseFromRestoreJob.setter
	def BrowseFromRestoreJob(self, job_id):
		_job = Job(self.auto_subclient.auto_subclient.commcell, job_id)
		self._start_time = _job.start_time
		self._end_time = _job.end_time


	@property
	def BrowseMA(self): return self._browse_ma_client_name

	@BrowseMA.setter
	def BrowseMA(self, ma_name):
		client = self.auto_subclient.auto_commcell.commcell.clients.get(ma_name)
		self._browse_ma_client_name = client.client_name
		self.browse_ma_host_name = client.hostname
		self._browse_ma_id = client.client_id



	@property
	def UnconditionalOverwrite(self): return self._overwrite

	@UnconditionalOverwrite.setter
	def UnconditionalOverwrite(self, Value):
		self._overwrite = Value


	@property
	def RestorePath(self): return self._restore_path

	@RestorePath.setter
	def RestorePath(self, Value):
		self._restore_path = Value

	@property
	def RestoreACL(self): return self.fs_acl

	@RestoreACL.setter
	def RestoreACL(self, Value):
		self.fs_acl = Value

	def set_destination_client(self):
		"""
		set the default destiantion client ifg not given by user and path to restore in that client

		Exception:
			if client si not part of CS
		"""
		try:
			if not self._dest_client_name is None:
				self._dest_client_name = self.auto_subclient.auto_vsainstance.co_ordinator
				client = self.auto_subclient.auto_commcell.commcell.clients.get(self._dest_client_name)
				self._dest_host_name = client.host_name

			self.set_restore_path()

		except Exception as e:
				self.log.exception("An Aerror occurred in SetDestinationClient ")
				raise  e

	def set_restore_path(self):
		"""
		set the restore path as CVAutomation in the drive with maximum storage space

		Exception:
			if failed to get storage details
			if failed to create directory
		"""
		try:


			self.client_machine = machine.Machine(self._dest_client_name,
							 self.auto_subclient.auto_commcell.commcell)

			_temp_storage_dict = {}
			storage_details = self.client_machine.get_storage_details()
			_drive_regex = "^[a-zA-Z]$"
			for _drive, _size in storage_details.iteritems():
				if re.match(_drive_regex, _drive):
					_temp_storage_dict[_drive] = _temp_storage_dict[_size]


			_maximum_storage = max(_temp_storage_dict.values())
			results = filter(lambda x: x[1] == _maximum_storage, _temp_storage_dict.items())
			_dir_path = results[0][0]+":\\CVAutomation"
			if not self.client_machine.check_directory_exists(_dir_path):
				self.client_machine.create_directory(_dir_path)

			self._restore_path = _dir_path


		except Exception as e:
			self.log.exception("An Error occurred in PopulateRestorePath ")
			raise  e


class disk_restore_options(object):
	"""
	Main file for disk restore options in Automation

	init:

	subclient - (obj)	- subclient object of the cs

	set_destination_client()	- set the co-ordinator as the default destination client
                                                                        if not specified by user

	set_restore_path()			- set the path with maximum space as  default restore path  for
                                                            file level restore if not set as user

	"""

	def __init__(self, subclient):
		self.auto_subclient = subclient
		self.log = logger.get_log()
		self._copy_preceedence = None
		self.over_write = False
		self.use_impersonation = False
		self.restore_backup_job = None
		self.power_on = False
		self.copy_preceedence_applicable = False
		self._start_time = 0
		self._end_time = 0
		self._browse_from_snap = False
		self._browse_from_backupcopy = False
		self._browse_from_auxcopy = False
		self._browse_ma_client_name, self._browse_ma_id = self.auto_subclient.browse_ma
		self._convert_disk_to = None
		self.set_destination_client()


	@property
	def DestinationClient(self): return self._dest_host_name

	@DestinationClient.setter
	def DestinationClient(self, client_name):
		client = self.auto_subclient.auto_commcell.commcell.clients.get(client_name)
		self._dest_client_name = client_name
		self._dest_host_name = client.host_name
		self.set_restore_path()

	@property
	def CopyPreecedence(self): return self._copy_preceedence

	@CopyPreecedence.setter
	def CopyPreecedence(self, value = None):
		self.copy_preceedence_applicable = True
		self._copy_preceedence = value

	@property
	def BrowseFromSnap(self):
		return self._browse_from_snap

	@BrowseFromSnap.setter
	def BrowseFromSnap(self, Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_snap_copy_id(
                                                                    self.auto_subclient.sp_id)

	@property
	def BrowsefromBackupCopy(self):
		return self._browse_from_backupcopy

	@BrowsefromBackupCopy.setter
	def BrowsefromBackupCopy(self, Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_primary_copy_id(
                                                                    self.auto_subclient.sp_id)

	@property
	def BrowsefromAuxcopy(self):
		return self._browse_from_auxcopy

	@BrowsefromAuxcopy.setter
	def BrowsefromAuxcopy(self, Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_aux_copy_id(
                                                                    self.auto_subclient.sp_id)

	@property
	def BrowseFromRestoreJob(self): return self._start_time, self._end_time

	@BrowseFromRestoreJob.setter
	def BrowseFromRestoreJob(self, job_id):
		_job = Job(self.auto_subclient.auto_subclient.commcell, job_id)
		self._start_time = _job.start_time
		self._end_time = _job.end_time


	@property
	def BrowseMA(self): return self._browse_ma_client_name

	@BrowseMA.setter
	def BrowseMA(self, ma_name):
		client = self.auto_subclient.auto_commcell.commcell.clients.get(ma_name)
		self._browse_ma_client_name = client.client_name
		self.browse_ma_host_name = client.hostname
		self._browse_ma_id = client.client_id



	@property
	def UnconditionalOverwrite(self): return self._overwrite

	@UnconditionalOverwrite.setter
	def UnconditionalOverwrite(self, Value):
		self._overwrite = Value


	@property
	def RestorePath(self): return self._restore_path

	@RestorePath.setter
	def RestorePath(self, Value):
		self._restore_path = Value

	@property
	def ImpersonateUser(self): return self.impersonate_user_name

	@ImpersonateUser.setter
	def ImpersonateUser(self, user_name):
		self.impersonate_user_name = user_name
		self.use_impersonation = True


	@property
	def ConvertDiskTo(self): return self._convert_disk_to

	@ConvertDiskTo.setter
	def ConvertDiskTo(self, Value):
		self._convert_disk_to = Value


	def set_destination_client(self):
		"""
		set the default destiantion client ifg not given by user and path to restore in that client

		Exception:
			if client si not part of CS
		"""
		try:
			if not self._dest_client_name is None:
				self._dest_client_name = self.auto_subclient.auto_vsainstance.co_ordinator
				client = self.auto_subclient.auto_commcell.commcell.clients.get(self._dest_client_name)
				self._dest_host_name = client.host_name

			self.set_restore_path()

		except Exception as e:
				self.log.exception("An Aerror occurred in SetDestinationClient ")
				raise  e

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
			for _drive, _size in storage_details.iteritems():
				if re.match(_drive_regex,_drive):
					_temp_storage_dict[_drive] = _temp_storage_dict[_size]


			_maximum_storage = max(_temp_storage_dict.values())
			results = filter(lambda x: x[1] == _maximum_storage, _temp_storage_dict.items())
			_dir_path  = results[0][0]+":\\CVAutomation"
			if not self.client_machine.check_directory_exists(_dir_path):
				self.client_machine.create_directory(_dir_path)

			self._restore_path = _dir_path


		except Exception as e:
			self.log.exception("An Error occurred in PopulateRestorePath ")
			raise  e


class full_vm_restore_options(object):
	"""
	Main class for full restore options in Automation

	init:

	subclient - (obj)	- subclient object of the cs

	inputs   - (dict)   - entire input dictionary passed for automation

	"""
	def __init__(self, subclient, inputs):
		self.inputs = inputs
		self.auto_subclient = subclient
		self.log = logger.get_log()
		self.perform_disk_validation = False
		self._copy_preceedence = None
		self.over_write = False
		self.use_impersonation = False
		self.restore_backup_job = None
		self.power_on = False
		self.copy_preceedence_applicable = False
		self._start_time = 0
		self._end_time = 0
		self._browse_from_snap = False
		self._browse_from_backupcopy = False
		self._browse_from_auxcopy = False
		self._browse_ma_client_name, self._browse_ma_id = self.auto_subclient.subclient.browse_ma
		self.in_place = False
		self.add_to_failover = False
		self.ProxyDict = {}
		self.DataStoreDict = {}
		self.RestoreInfoDict = {}

	@property
	def DestinationClient(self): return self._dest_host_name

	@DestinationClient.setter
	def DestinationClient(self, client_name):
		client = self.auto_subclient.auto_commcell.commcell.clients.get(client_name)
		self._dest_client_name = client_name
		self._dest_host_name = client.host_name

	@property
	def CopyPreecedence(self): return self._copy_preceedence

	@CopyPreecedence.setter
	def CopyPreecedence(self, value = None):
		self.copy_preceedence_applicable = True
		self._copy_preceedence = value

	@property
	def BrowseFromSnap(self):
		return self._browse_from_snap

	@BrowseFromSnap.setter
	def BrowseFromSnap(self, Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_snap_copy_id(
                                                                    self.auto_subclient.sp_id)

	@property
	def BrowsefromBackupCopy(self):
		return self._browse_from_backupcopy

	@BrowsefromBackupCopy.setter
	def BrowsefromBackupCopy(self,Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_primary_copy_id(self.auto_subclient.sp_id)

	@property
	def BrowsefromAuxcopy(self):
		return self._browse_from_auxcopy

	@BrowsefromAuxcopy.setter
	def BrowsefromAuxcopy(self,Value):
		self.copy_preceedence = self.auto_subclient.auto_commcell.find_aux_copy_id(self.auto_subclient.sp_id)

	@property
	def BrowseFromRestoreJob(self): return self._start_time, self._end_time

	@BrowseFromRestoreJob.setter
	def BrowseFromRestoreJob(self, job_id):
		_job = Job(self.auto_subclient.auto_subclient.commcell, job_id)
		self._start_time = _job.start_time
		self._end_time = _job.end_time


	@property
	def BrowseMA(self): return self._browse_ma_client_name

	@BrowseMA.setter
	def BrowseMA(self, ma_name):
		client = self.auto_subclient.auto_commcell.commcell.clients.get(ma_name)
		self._browse_ma_client_name = client.client_name
		self.browse_ma_host_name = client.hostname
		self._browse_ma_id = client.client_id



	@property
	def UnconditionalOverwrite(self): return self._overwrite

	@UnconditionalOverwrite.setter
	def UnconditionalOverwrite(self, Value):
		self._overwrite = Value


	@property
	def PowerOnAfterRestore(self): return self.power_on

	@PowerOnAfterRestore.setter
	def PowerOnAfterRestore(self, Value):
		self.power_on = Value

	@property
	def InPlaceOverwrite(self): return self.in_place

	@InPlaceOverwrite.setter
	def InPlaceOverwrite(self, Value):
		self.in_place = Value


	@property
	def ImpersonateUser(self): return self.ImpersonateUserName

	@ImpersonateUser.setter
	def ImpersonateUser(self, UserName):
		self.ImpersonateUserName = UserName
		self.useImpersonation = True

	@property
	def RegisterwithFailover(self): return self.add_to_failover

	@RegisterwithFailover.setter
	def RegisterwithFailover(self, value):
		"""
		This registers VM with Failover cluster

		Args:

		Value	(bool)	 - True -  Register with Failover
			default:False

		"""
		self.add_to_failover = value

	def _process_inputs(self, attr_to_set, user_input):
		"""
		will process all the inputs from user and set it as calss variable

		attr_to_set	(str)	- property need to eb set as class variable

		user_input	(str)	- property  to be set as class variable that is passed from user

		Exception:
			if the property is not given in user input
		"""
		try:
			if user_input in self.inputs.keys():
				setattr(self, attr_to_set, self.inputs[user_input])
			else:
				self.log.info("The Tag %s is not specified by the user"%user_input)
				setattr(self, attr_to_set, None)

		except Exception as e:
			self.log.exception("An Aerror occurred in setting hypervisor tags")
			raise  e



	def populate_hypervisor_restore_inputs(self):
		"""
		populate all the hypervisor defaults for the full VM restore

		Exception:
			if failed to compute default VSA Client

			if failed to compute proxy and Datastores and Host

		"""
		try:
			instance_name = self.auto_subclient.auto_vsainstance.instance_name


			def HyperV():
				proxy_host_list = []

				vm_list = self.auto_subclient.subclient.vm_list


				#setting Virtualization client
				self.DestinationClient = self.inputs.get(
                        "DestinationClient",
                        self.auto_subclient.auto_vsaclient.vsa_client_name)
				dest_auto_vsaclient = self.auto_subclient.auto_vsaclient(
                        self._dest_client_name, self.auto_subclient.auto_vsacommcell)
				dest_auto_vsa_instance = self.auto_subclient.auto_vsainstance(dest_auto_vsaclient)
				dest_client_hypervisor = dest_auto_vsa_instance._create_hypervisor_object(
                                                            dest_auto_vsa_instance.server_name)



				#setting server in the VSA Client
				if not self.inputs.has_key("RestoreHyperVServer"):
					proxy_list = dest_auto_vsa_instance.proxy_list.keys()
					for each_proxy in proxy_list:
						proxy_host_list.append(self.auto_subclient.auto_commcell.get_hostname_for_client(each_proxy))

					self.DestinationClient, Datastore = dest_client_hypervisor.compute_free_resources(
                                                                            proxy_host_list,vm_list)
					self.dest_client_hypervisor = dest_auto_vsa_instance._create_hypervisor_object(
                                                                            self._dest_client_name)
					self.dest_machine = machine.Machine(self._dest_client_name,
                                                     self.auto_subclient.auto_vsacommcell.commcell)

				#setting Destination path in VSA Client
				if not self.inputs.has_key("DestinationPath"):
					proxy_host_list = []
					proxy_host_list.append(self.DestinationClient)
					dest_host_name, datastore = self.dest_client_hypervisor.compute_free_resources(
                                                                        proxy_host_list, vm_list)
					_dir_path = os.path.join(datastore,"CVAutomation")
					if not self.dest_machine.check_directory_exists(_dir_path):
						self.dest_machine.create_directory(_dir_path)

					self.DestinationPath = _dir_path


			hv_dict = {"Hyper-V":HyperV}
			(hv_dict[instance_name])()

		except Exception as e:
			self.log.exception("An Aerror occurred in setting hypervisor tags")
			raise  e