"""Main file that does all operations on hypervsor

classes defined:
    Base class:
        Hypervisor- Act as base class for all hypervior operations

    Inherited class:
        HyperVHelper - Does all operations on Hyper-V Hypervisor

    Methods:
        get_all_vms_in_hypervisor()    - abstract -get all the VMs in that hypervisor

        compute_free_resources()    - compute teh free resource for perfoming restores
"""

import os
import re
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from operator import itemgetter
import hashlib
import requests
from AutomationUtils import logger
from . import VMHelper, VirtualServerConstants, VirtualServerUtils, VmwareServices, FusionComputeServices
from AutomationUtils import machine
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Hypervisor(object):
    __metaclass__ = ABCMeta
    """
    Base class for performing all Hypervisor operations

    Methods:
         get_all_vms_in_hypervisor()    - abstract -get all the VMs in HYper-V Host

        compute_free_resources()        - compute the hyperv host and destiantion path
                                                    for perfoming restores

    """
    def __new__(cls, server_host_name,
                host_machine,
                user_name,
                password,
                instance_type,
                commcell):
        """
        Initialize the object based in intstance_type

        server_name (list)  - hypervisor name eg: vcenter name or Hyperv host

        host_machine    (str)  - client of cs where we will execute all hypervisor operations


        """

        hv_type = VirtualServerConstants.hypervisor_type
        if instance_type == hv_type.MS_VIRTUAL_SERVER.value.lower():
            return object.__new__(HyperVHelper)
        elif instance_type == hv_type.VIRTUAL_CENTER.value.lower():
            return object.__new__(VmwareHelper)
        elif instance_type == hv_type.AZURE_V2.value.lower():
            return object.__new__(AzureHelper)
        elif instance_type == hv_type.Fusion_Compute.value.lower():
            return object.__new__(FusionComputeHelper)

    def __init__(self,
                 server_host_name,
                 host_machine,
                 user_name,
                 password,
                 instance_type,
                 commcell):
        """
        Initialize common variables for hypervior
        """
        self.commcell = commcell
        self.instance_type = instance_type
        self.server_list = server_host_name
        self.server_host_name = server_host_name[0]
        self.host_machine = host_machine
        self.user_name = user_name
        self.password = password
        self.instance_type = instance_type
        self._VMs = {}
        self.log = logger.get_log()
        self.utils_path = VirtualServerUtils.UTILS_PATH
        self.machine = machine.Machine(
            self.host_machine, self.commcell)

    @property
    def vm_user_name(self):
        """gets the user name of the Vm . it si read only attribute"""

        return self._user_name

    @vm_user_name.setter
    def vm_user_name(self, value):
        """sets the user name of the VM if it is differnt form default"""
        self._user_name = value

    @property
    def vm_password(self):
        """gets the user name of the Vm . it si read only attribute"""

        return self._password

    @vm_password.setter
    def vm_password(self, value):
        """sets the user name of the VM if it is differnt form default"""
        self._password = value

    @property
    def VMs(self):
        """Returns List of VMs. It is read onlyt attribute"""
        return self._VMs

    @VMs.setter
    def VMs(self, vm_list):
        """creates VMObject for list of VM passed
        Args:
            vmList    (list) - list of VMs for creating VM object
        """

        try:
            if isinstance(vm_list, list):
                for each_vm in vm_list:
                    self._VMs[each_vm] = VMHelper.HypervisorVM(self, each_vm)

            else:
                self._VMs[vm_list] = VMHelper.HypervisorVM(self, vm_list)
                self.log.info("VMs are %s" % self._VMs)

        except Exception as err:
            self.log.exception(
                "An exception occurred in creating object %s" % err)
            raise Exception(err)

    @abstractmethod
    def get_all_vms_in_hypervisor(self, server=""):
        """
        get all the Vms in Hypervisor

        Args:
                server    (str)    - specific hypervisor Host for which all Vms has to be fetched

        Return:
                Vmlist    (list)    - List of Vms in  in host of Pseudoclient
        """
        self.log.info("get all the VMs in hypervisor class")

    @abstractmethod
    def compute_free_resources(self, proxy_list, vm_list):
        """
        compute the free hosting hypervisor and free space for disk in hypervisor

        Args:
            proxy_list  - list of servers from which best has to be chosen

            vm_list     - list of Vm to be restored

        Return:
                host         (str)    - hypervisor host where vm is to be restored
                                            like esx, resourcegroup,region,hyperv host

                datastore    (str)    - diskspace where vm needs to be restored
                                            like destinationpath,datastore,bucket
        """
        self.log.info(
            "computes the free ESXHost and Datastore in case of VMware")

    def update_hosts(self):
        """
        update the Information of Host
        """
        self.log.info("Host Is updated")


class HyperVHelper(Hypervisor):
    """
    Main class for performing all operations on Hyperv Hyperviosr

    Methods:
            get_all_vms_in_hypervisor()        - abstract -get all the VMs in HYper-V Host

            compute_free_resources()        - compute the hyperv host and destiantion path
                                                    for perfoming restores

            mount_disk()                    - Mount the Vhd/VHDX and return the drive letter

            un_mount_disk()                    - Unmount the VHD mounted provided the path

            _get_datastore_dict()            - get the list of drives with space in Hyper-V

            _get_datastore_priority_list()    - return the drives in Hyper-V Host in
                                                    increasing order of disk size

            _get_proxy_priority_list()        - returns the proxy associated with that instance in
                                                    increasing order of memory

            _get_required_memory_for_restore()- Sum of Memory of the VM to be restored

            _get_required_diskspace_for_restore()- Sum of disk space of the VM to be restored

    """

    def __init__(self, server_host_name,
                 host_machine,
                 user_name,
                 password,
                 instance_type,
                 commcell):
        """
        Initialize Hyper-V Helper class properties
        """

        super(HyperVHelper, self).__init__(server_host_name, host_machine,
                                           user_name, password, instance_type, commcell)

        self.server_host_machine = self.commcell.clients.get(self.server_host_name)
        self.operation_ps_file = "GetHypervProps.ps1"
        self.disk_extension = [".vhd", ".avhd", ".vhdx", ".avhdx"]
        self.prop_dict = {
            "server_name": self.server_host_name,
            "vm_name": "$null",
            "extra_args": "$null"
        }

        self.operation_dict = {
            "server_name": self.server_host_name,
            "extra_args": "$null",
            "vhd_name": "$null"
        }

    def get_all_vms_in_hypervisor(self, server=""):
        """
        get all the Vms in Hypervisor

        Args:
                server    (str)    - specific hypervisor Host for which all Vms has to be fetched

        Return:
                Vmlist    (list)    - List of Vms in  in host of Pseudoclient
        """
        try:
            _all_vm_list = []
            if server == "":
                server_list = self.server_host_name

            else:
                server_list = [server]

            for _each_server in server_list:
                _ps_path = os.path.join(
                    self.utils_path, self.operation_ps_file)
                self.prop_dict["server_name"] = _each_server
                self.prop_dict["property"] = "GetAllVM"
                output = self.machine._execute_script(_ps_path, self.prop_dict)
                # _stdout, _stderr = VirtualServerUtils.ExecutePsFile(
                # _ps_path, _each_server, self.user_name, self.password, "", "GetAllVM")

                _stdout = output.output
                _stdout = _stdout.rsplit("=", 1)[1]
                _stdout = _stdout.strip()
                _temp_vm_list = _stdout.split(",")
                for each_vm in _temp_vm_list:
                    if each_vm != "":
                        each_vm = each_vm.strip()
                        if re.match("^[A-Za-z0-9_-]*$", each_vm):
                            _all_vm_list.append(each_vm)
                        else:
                            self.log.info(
                                "Unicode VM are not supported for now")

            return _all_vm_list

        except Exception as err:
            self.log.exception(
                "An exception occurred while getting all Vms from Hypervisor")
            raise Exception(err)

    def mount_disk(self, vm_obj, _vhdpath, destination_client=None):
        """
        mount the disk and return the drive letter mounted

        vm_obj -         (str)    - Vm helper object of the VM for which disk has to be mounted

        _vhdpath    (str)    - diks path has to be mounted

        destination_client  (obj)   - client where the disk to be mounted are located

        return:
                _drive_letter    (list)    - drive lettter in which disk is mounted

        Exception:
                if disk failed to mount

        """
        try:

            _drive_letter = vm_obj.mount_vhd(_vhdpath, destination_client)
            if not _drive_letter:
                self.log.error("VsHD might be corrupted mouting failed,")
                raise Exception("Cannot Mount the disk")

            else:
                self.log.info("Mounting restored VHD was succesfull")
                self.log.info("Drive letter is %s" % _drive_letter)
                return _drive_letter

        except Exception as err:
            self.log.exception(
                "exception raised in Mounting Disk , cannot proceed")
            raise err

    def un_mount_disk(self, vm_obj, _vhdpath):
        """
        unmount the disk taht is mounted

         vm_obj -         (str)    - Vm helper object of the VM for which disk has to be unmounted

        _vhdpath    (str)    - diks path has to be unmounted


        Exception:
                if disk failed to unmount

        """
        try:
            self.log.info("Trying to unmount diks %s" % _vhdpath)
            if not os.path.isdir(_vhdpath):
                self.log.info("VHD file exists...unmounting the file")
                vm_obj.un_mount_vhd(_vhdpath)
            else:
                self.log.info(
                    "Mountpath provided for cleanup...checking for vhd files")
                for root, dirs, files in os.walk(_vhdpath):
                    for file in files:
                        filename, ext = os.path.splitext(file)
                        if ((ext == ".vhd") or (ext == ".vhdx") or
                                (ext == ".avhd") or (ext == ".avhdx")):
                            _vhdpath = os.path.join(root, file)
                            self.log.info("Found VHD file... " + _vhdpath)
                            vm_obj.un_mount_vhd(_vhdpath)

        except Exception as err:
            self.log.exception(
                "exception raised in UnMounting Disk , cannot proceed")
            raise err

    def _get_datastore_dict(self, proxy, proxy_host_name):
        """
        get the list of datastore in an proxy

        proxy                 (str)    - list of datastores in that
                                            particular proxy would be returned
        proxy_host_name       (str)    - host_name of the proxy

        Return:
                disk_size_dict    (dict)    - with drive as keys and size
                                                    as values in proxy provided
                                                        disk_size_dict = {'proxy-c':14586}

        """
        try:
            if proxy is None:
                proxy = self.server_host_name

            _disk_size_dict = {}

            _ps_path = os.path.join(self.utils_path, self.operation_ps_file)
            self.prop_dict["vm_name"] = proxy_host_name
            self.prop_dict["property"] = "DISKSIZE"
            self.prop_dict["server_name"] = proxy_host_name
            proxy_machine = machine.Machine(proxy, self.commcell)
            output = proxy_machine._execute_script(_ps_path, self.prop_dict)

            _stdout = output.output
            if _stdout:
                _stdout = _stdout.strip()
                _stdout = _stdout.split("=")[1]
                _stdlines = [disk for disk in _stdout.split(",") if disk]
                for _each_disk in _stdlines:
                    _diskname = proxy + "-" + _each_disk.split("-")[0]
                    _disksize = _each_disk.split("-")[1]
                    _disk_size_dict[_diskname] = int(float(_disksize))

            return _disk_size_dict

        except Exception as err:
            self.log.exception("exception raised in GetDatastoreDict Disk ")
            raise err


    def _get_host_memory(self, proxy, proxy_host_name):
        """
        get the free memory in proxy

        Args:

                proxy     (str)    - list of datastores in that particular proxy would be returned

                proxy_host_name       (str)    - host_name of the proxy

        return:
                val     (int)    - free  memory of Host in GB eg:; 3GB

        Exception:
                Raise exception when failed to get Memeory

        """
        try:
            if proxy is None:
                proxy = self.server_host_name

            _ps_path = os.path.join(self.utils_path, self.operation_ps_file)
            self.prop_dict["property"] = "HostMemory"
            self.prop_dict["server_name"] = proxy_host_name
            proxy_machine = machine.Machine(proxy, self.commcell)
            output = proxy_machine._execute_script(_ps_path, self.prop_dict)

            _stdout = output.output
            if _stdout:
                _stdout = _stdout.strip()
                val = int(float(_stdout.split("=")[1]))
                return val

            else:
                raise Exception("Failed to get Memory")

        except Exception as err:
            self.log.exception("exception raised in GetMemory  ")
            raise err

    def _get_datastore_priority_list(self, vsa_proxy_list, host_dict):
        """
        From the given list of proxy get all the details of drive and space
                                                                and order them in increasing size

        Args:
                vsa_proxy_list            (list)    - list of proxies which needs to be
                                                                    ordered as per disk size

                host_dict                 (dict)    -dictionary of proxies and their matching host name
        returns:
            _sorted_datastore_dict(dict)    - with disk proxy-drive name as keys and size as values
                                                        _sorted_datastore_dict = {'proxy-c':14586,
                                                                                  'proxy1-D':12456}

        """
        try:
            _datastore_dict = {}
            for _each_proxy in vsa_proxy_list:
                _datastoredict = self._get_datastore_dict(_each_proxy, host_dict[_each_proxy])
                _datastore_dict.update(_datastoredict)
            _sorted_datastore_dict = OrderedDict(sorted(_datastore_dict.items(),
                                                        key=itemgetter(1), reverse=True))
            return _sorted_datastore_dict

        except Exception as err:
            self.log.exception(
                "An Aerror occurred in  GetDatastorePriorityList ")
            raise err

    def _get_proxy_priority_list(self, vsa_proxy_list, host_dict):
        """
        get the free host memory in proxy and arrange them with increarsing order

        Args:
                vsa_proxy_list            (list)    - list of proxies which needs to be
                                                    ordered as per Host Memory

                host_dict                 (dict)    -dictionary of proxies and their matching host name
        returns:
                _sorted_proxy_dict    (dict)    - with disk proxy name as keys and memory as values
                                                                _sorted_proxy_dict = {'proxy':5GB,
                                                                                     'proxy1':4GB}

        """
        try:

            _proxy_dict = {}
            for each_proxy in vsa_proxy_list:
                _proxy_memory = self._get_host_memory(each_proxy, host_dict[each_proxy])
                _proxy_dict[each_proxy] = int(_proxy_memory)

            _sorted_proxy_dict = OrderedDict(sorted(_proxy_dict.items(),
                                                    key=itemgetter(1), reverse=True))
            return _sorted_proxy_dict

        except Exception as err:
            self.log.exception("An Aerror occurred in  GetProxyPriorityList ")
            raise err

    def _get_required_memory_for_restore(self, vm_list):
        """
        sums up all the memory of needs to be restores(passed as VM list)

        Args:
                vm_list    (list)    - list of vm to be restored

        returns:
                sum of total memory of VM to be restored in Gb
        """
        try:

            _vm_total_memory = 0
            for _each_vm in vm_list:
                if self.VMs[_each_vm].GuestOS == "Windows":
                    self.VMs[_each_vm].update_vm_info('Memory')
                    _vm_memory = self.VMs[_each_vm].Memory.strip()
                    _vm_total_memory = _vm_total_memory + int(_vm_memory)

            return _vm_total_memory

        except Exception as err:
            self.log.exception(
                "An Aerror occurred in  _get_required_memory_for_restore ")
            raise err

    def _get_required_diskspace_for_restore(self, vm_list):
        """
        sums up all the disk space of needs to be restores(passed as VM list)

        Args:
                vm_list    (list)    - list of vm to be restored

        returns:
                sum of total disk space of VM to be restored
        """
        try:

            _vm_total_disk_size = 0
            for _each_vm in vm_list:
                if self.VMs[_each_vm].GuestOS == "Windows":
                    storage_details = self.VMs[_each_vm].machine.get_storage_details()
                    _vm_total_disk_size += int(storage_details['total'])
            _vm_total_disk_size = int(_vm_total_disk_size / 1024)
            return _vm_total_disk_size

        except Exception as err:
            self.log.exception(
                "An error occurred in  _get_required_diskspace_for_restore ")
            raise err

    def get_disk_in_the_path(self, folder_path):
        """
         get all the disks in the folder

        Args:
            folder_path     (str)   - path of the folder from which disk needs to be listed
                                        e.g: C:\\CVAutomation

         Returns:
                disk_list   (list)-   list of disks in the folder

        Raises:
            Exception:
                if failed to get the list of files
        """
        try:
            _disk_list = []
            output = self.machine.get_files_in_path(folder_path)

            for value in output:
                disk_name = value[0]
                if any(re.search(ext, disk_name.lower()) for ext in self.disk_extension):
                    _disk_list.append(disk_name)

            return _disk_list

        except Exception as err:
            self.log.exception(
                "Exception occurred {0} in getting disk list".format(err)
                        )

    def compute_free_resources(self, proxy_list, host_dict, vm_list):
        """
        compute the free hosting hypervisor and free space for disk in hypervisor

        Args:
                proxy_list    (list)    -list of proxies from which best proxy has to found

                host_dict     (dict)    -dictionary of proxies and their matching host name

                vm_list        (list) - list of Vms to be restored

        return:
                proxy_name    (str)    - the proxy where restore can be performed

                datastore_name(str)    - datastore where restore has to be performed
        """
        try:

            proxy_name = None
            datastore_name = None
            _proxy_priority_dict = self._get_proxy_priority_list(proxy_list, host_dict)
            _datastore_priority_dict = self._get_datastore_priority_list(
                proxy_list, host_dict)
            _total_vm_memory = self._get_required_memory_for_restore(vm_list)
            _total_disk_space = self._get_required_diskspace_for_restore(
                vm_list)
            for each_datastore in _datastore_priority_dict.items():
                if (each_datastore[1]) > _total_disk_space:
                    datastore_name = each_datastore[0].split("-")[1]
                    proxy_name = each_datastore[0].split("-")[0]
                    self.log.info(
                        "The Datastore %s has more than total disk space in VM" % datastore_name)
                    if _proxy_priority_dict[proxy_name] > _total_vm_memory:
                        self.log.info(
                            "the Proxy %s has higher memory than the total VMs" % proxy_name)
                        break
                    else:
                        continue
                else:
                    continue

            return proxy_name, datastore_name

        except Exception as err:
            self.log.exception("An Aerror occurred in  ComputeFreeResources ")
            raise err

    def copy_test_data_to_each_volume(self, vm_name, _drive, backup_folder, _test_data_path,
                                      machine=None):
        """
        copy testdata to each volume in the vm provided


        Args:
                vm_name    (str)        - vm to which test data has to be copied

                _drive(str)            - Drive letter where data needs to be copied

                _test_data_path(str) - path where testdata needs to be generated

                backup_folder(str)  - name of the folder to be backed up

                machine(obj)        - the machine class object of the controller

        Exception:

                if fails to generate testdata

                if fails to copy testdata

        """

        try:



            # initializing prerequisites
            _failed_file_list = []

            # create Base dir
            _dest_base_path = os.path.join(self.VMs[vm_name].drive_list[_drive], os.path.sep, backup_folder)
            if not self.VMs[vm_name].machine.check_directory_exists(_dest_base_path):
                _create_dir = self.VMs[vm_name].machine.create_directory(_dest_base_path)
                if not _create_dir:
                    _failed_file_list.append(_dest_base_path)

            _dest_base_path = os.path.join(_dest_base_path, "TestData")
            # here create machine object with localhost as machine name for other
            # hypervisors for Hyper-V the same server name can act as controller

            self.log.info("Generating test data was successful now copying it")
            self.VMs[vm_name].machine.copy_from_local(_test_data_path, _dest_base_path)

        except Exception as err:
            self.log.exception(
                "An error occurred in  Copying test data to Vm  ")
            raise err

    def check_cbt_driver_running(self, proxy_list, host_dict):
        """
        check if CBT driver is running on the hyperv node

        Args:
                proxy_list    (list)    -list of proxies/ hyperv nodes

                host_dict     (dict)    -dictionary of proxies and their matching host name

        Exception:
                If unable to check CBT driver status
        """
        try:
            for each_proxy in proxy_list:
                driver_state = r'cmd.exe /c "sc query cvcbt"'
                proxy_machine = machine.Machine(each_proxy, self.commcell)
                output = proxy_machine.execute_command(driver_state)

                if re.search("RUNNING", output._output):
                    self.log.info("The CVCBT driver is running on proxy {0}".format(each_proxy))
                else:
                    raise Exception("The CVCBT driver is not running on the proxy {0}".format(each_proxy))

        except Exception as err:
            self.log.exception(
                "An error occurred in  checking if CVCBT driver is running  ")
            raise err

    def check_or_set_cbt_registry(self, proxy_list, host_dict, instanceno_dict):
        """
        Check/Set if CBT registry for CBT testing is set on the proxies

        Args:
                proxy_list    (list)    -list of proxies/ hyperv nodes

                host_dict     (dict)    -dictionary of proxies and their matching host name

        Return:
                CBTStatFolder (String) -Folder path where CBT stats are collected

        Exception:
                An error occurred while checking/creating the registry 
        """
        try:
            for each_proxy in proxy_list:
                proxy_machine = machine.Machine(each_proxy, self.commcell)
                proxy_machine.instance = instanceno_dict[each_proxy]
                registry_path = "VirtualServer"
                output = proxy_machine.check_registry_exists(registry_path, "sCVCBTStatsFolder")
                if output:
                    CBTStatFolder = proxy_machine.get_registry_value(registry_path, "sCVCBTStatsFolder")
                else:
                    CBTStatFolder = "C:\\CBTStatus"
                    output = proxy_machine.create_registry(registry_path, "sCVCBTStatsFolder", CBTStatFolder , "String")
                    output = proxy_machine.create_registry(registry_path, "bDumpCVCBTStatsToFile", "00000001", "DWord")
                    output = proxy_machine.create_registry(registry_path, "bDumpCVCBTStats", "00000001", "DWord")

                if not output:
                    raise Exception("An error occured while creating the registry")
                else:
                    self.log.info("Checked and created CBT driver dump stats registry")
                return CBTStatFolder
        except Exception as err:
            self.log.exception(
                "An error occurred while checking/creating the registry  ")
            raise err

class VmwareHelper(Hypervisor):
    """
    Main class for performing all operations on Vmware Hypervisor

    Methods:
            get_all_vms_in_hypervisor()		- abstract -get all the VMs in HYper-V Host

            compute_free_resources()		- compute the Vmware host and Datastore
                                                    for performing restores

            _vmware_login                   - Login to vcenter 6.5 and above

            _make_request                   - Rest api calls to vcenter

            _vmware_get_vms                 - Get list of qualified vms

            _get_vcenter_version            - get the vcenter version

            get_all_vms_in_hypervisor       - Get complete list of vms in the vcenter

            compute_free_resources          - Calculate free resources

            _get_datastore_dict             - Get list of datastore with free space

            _get_host_memory                - Get list of esx with free ram and cpu

            _get_required_resource_for_restore - Get restore vm ram and storage requirement

            _get_datastore_priority_list    - Get list of datastore in descending
                                                order as per free space

            _get_host_priority_list         -  Get list of esx in descending oder as per free ram

            _get_datastore_tree_list        - get datastore hierarchy

            copy_test_data_to_each_volume   - Copy test data to backup vm

    """

    def __init__(self, server_host_name, host_machine, user_name,
                 password, instance_type, auto_commcell):
        """
        Initialize Vmware Helper class properties
        """

        super(VmwareHelper, self).__init__(server_host_name, host_machine,
                                           user_name, password, instance_type, auto_commcell)
        self.operation_ps_file = "GetVmwareProps.ps1"
        self.vm_operation_ps_file = "VmwareOperation.ps1"
        self.vcenter_version = 0
        self.vmware_url = 'https://{0}/rest'.format(self.server_host_name)
        self._headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'vmware-api-session-id': None}
        self._services = VmwareServices.get_services(self.server_host_name)
        self.prop_dict = {
            "server_name": self.server_host_name,
            "user": self.user_name,
            "pwd": self.password,
            "vm_name": "$null",
            "extra_args": "$null"
        }
        self.operation_dict = {
            "server_name": self.server_host_name,
            "user": self.user_name,
            "pwd": self.password,
            "vm_name": "$null",
            "vm_user": "$null",
            "vm_pass": "$null",
            "extra_args": "$null"
        }
        self.disk_extension = [".vmdk"]

    def _vmware_login(self):
        """
        Login to vcenter 6.5 and above

        Return:
                Null
        """
        try:
            login_request = (self.user_name, self.password)
            response = self._make_request(
                'POST', self._services['LOGIN'], login_request)
            if response[1].status_code != 200:
                raise Exception
            else:
                self._headers['vmware-api-session-id'] = response[1].json()['value']
        except Exception as err:
            self.log.exception("An exception occurred while logging in to the vcenter")
            raise Exception(err)

    def _make_request(self, method, url, payload=None, attempts=0):
        """Makes the request of the type specified in the argument 'method'

        Args:
            method    (str)         --  http operation to perform, e.g.; GET, POST, PUT, DELETE

            url       (str)         --  the web url or service to run the HTTP request on

            payload   (dict / str)  --  data to be passed along with the request
                default: None

            attempts  (int)         --  number of attempts made with the same request
                default: 0

        Returns:
            tuple:
                (True, response) - in case of success

                (False, response) - in case of failure

        Raises:
            Vmware SDK Exception:
                if the method passed is incorrect/not supported

            requests Connection Error   --  requests.exceptions.ConnectionError

        """
        try:
            headers = self._headers

            if method == 'POST':
                response = requests.post(url, headers=headers, verify=True, auth=payload)
            elif method == 'GET':
                response = requests.get(url, headers=headers, verify=True)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, verify=True, json=payload)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, verify=True)
            else:
                raise Exception('HTTP method {} not supported'.format(method))

            if response.status_code == 401 and headers['vmware-api-session-id'] is not None:
                if attempts < 3:
                    self._headers['vmware-api-session-id'] = self._vmware_login()
                    return self._make_request(method, url, attempts + 1)
                else:
                    # Raise max attempts exception, if attempts exceeds 3
                    raise Exception('Error', '103')

            elif response.status_code == 200:
                return (True, response)
            else:
                return (False, response)
        except requests.exceptions.ConnectionError as con_err:
            raise Exception(con_err)

    def _vmware_get_vms(self):
        """
        sums up all the memory of needs to be restores(passed as VM list)

        Args:

        returns:
                vmlist  (dict)  -    list of powered on vms in the pseudoclients
        """
        try:
            vmlist = []
            flag, response = self._make_request('GET', self._services['GET_ALL_VMS'])
            if flag:
                for i in response.json()['value']:
                    vmlist.append(i['name'])
            return vmlist
        except Exception as err:
            self.log.exception("An exception occurred while logging in to the vcenter")
            raise Exception(err)

    def _get_vcenter_version(self, ps_path):
        """
        Get the vcenter version

        Args:
                ps_path	(str)	- Path for script file

        Return:
                Null
        """
        try:
            self.vcenter_version = self.machine._execute_script(ps_path, self.prop_dict)
        except Exception as err:
            self.log.exception("An exception occurred while getting Vcenter version")
            raise Exception(err)

    def get_all_vms_in_hypervisor(self, server=""):
        """
        Get all the vms for vmware

        Args:
             server (str)   -  Vcenter for which all the VMs has to be fetched

        Returns:
            _all_vm_list    (str)   -   List of VMs in the host of the pseudoclient
        """
        try:
            _ps_path = os.path.join(
                self.utils_path, self.operation_ps_file)
            self.prop_dict["server_name"] = self.server_host_name
            self.prop_dict["property"] = "GetVcenterVersion"
            # next code is commented out till we get full support for API for vmware
            #self._get_vcenter_version(_ps_path)
            _all_vm_list = []
            if self.vcenter_version >= 6.5:
                self._vmware_login()
                _temp_vm_list = self._vmware_get_vms()
            else:
                self.prop_dict["property"] = "GetAllVM"
                output = self.machine._execute_script(_ps_path, self.prop_dict)
                _stdout = output.output
                _stdout = _stdout.rsplit("=", 1)[1]
                _stdout = _stdout.strip()
                _temp_vm_list = _stdout.split(",")
            for each_vm in _temp_vm_list:
                if each_vm != "":
                    each_vm = each_vm.strip()
                    if re.match("^[A-Za-z0-9_-]*$", each_vm):
                        _all_vm_list.append(each_vm)
                    else:
                        self.log.info(
                            "Unicode VM are not supported for now")
            return _all_vm_list
        except Exception as err:
            self.log.exception("An exception occurred while getting all VMs from Vcenter")
            raise Exception(err)

    def compute_free_resources(self, vm_list):
        """
        compute the free Resource of the Vcenter based on free memory and cpu

        Args:

                vm_list		(list) - list of Vms to be restored

        return:
                Datastore	(str)	- the Datastore where restore can be performed

                ESX     (str)	- ESX where restore has to be performed

                Cluster     (str)	- Cluster where restore has to be performed

                Datacenter      (str)	- DataCenter where restore has to be performed
        """
        try:
            _datastore_priority_dict = self._get_datastore_priority_list()
            _host_priority_dict = self._get_host_priority_list()

            if vm_list != []:
                _total_vm_memory, _total_disk_space = self._get_required_resource_for_restore(vm_list)
            else:
                _total_vm_memory = 0
                _total_disk_space = 0

            for each_datastore in _datastore_priority_dict.items():
                if (each_datastore[1]) > _total_disk_space:
                    datastore_name = each_datastore[0]
                    self.log.info(""
                                  "The Datastore %s has more than total"
                                  "disk space in VM" % datastore_name)
                    _tree = self._get_datastore_tree_list(datastore_name)
                    for each_host in _host_priority_dict.items():
                        if (each_host[1]) > _total_vm_memory and each_host[0] == _tree['ESX'][0]:
                            self.log.info(
                                "the Host %s has higher "
                                "memory than the total VMs" % each_host[1])
                            break
                    else:
                        continue
                    break
                else:
                    continue

            return each_datastore[0], _tree['ESX'], _tree['Cluster'], _tree['Datacenter']

        except Exception as err:
            self.log.exception("An exception occurred while getting all VMs from HyperVisor")
            raise Exception(err)

    def _get_datastore_dict(self):
        """
        Get the list of datastore in an ESX

        Args:

        Return:
                _disk_size_dict	(dict)	- Datastores with name name free spaces

        """
        try:

            _disk_size_dict = {}
            if self.vcenter_version >= 6.5:
                self._vmware_login()
                flag, response = self._make_request('GET', self._services['GET_ALL_DATASTORES'])
                if flag:
                    for i in response.json()['value']:
                        if i['type'] == 'VMFS' and re.search("[GX]", i['name']) is None:
                            _ds_name = i['name']
                            _disk_size_dict.setdefault(_ds_name, []).append(i['datastore'])
                            _disk_size_dict[_ds_name].append(i['free_space'])
                            _disk_size_dict[_ds_name].append(i['capacity'])
            else:
                self.prop_dict["property"] = "GetDatastoreDetail"
                output = self.machine._execute_script(os.path.join
                                                      (self.utils_path, self.operation_ps_file),
                                                      self.prop_dict)
                _stdout = output.output
                _temp_ds_list = _stdout.lstrip("GetDatastoreDetail = @{")
                _temp_ds_list = _temp_ds_list.rsplit("} @{")
                for each_ds in _temp_ds_list:
                    each_ds_list = each_ds.rsplit("; ")
                    for each_ds_data in each_ds_list:
                        each_ds_split = each_ds_data.split("=")
                        each_ds_split[1] = each_ds_split[1].strip("}\n")
                        _disk_size_dict.setdefault(each_ds_split[0], []).append(each_ds_split[1])
            return _disk_size_dict
        except Exception as err:
            self.log.exception("exception raised in GetDatastoreDict Disk ")
            raise err

    def _get_all_nics_in_host(self):
        """
        get all the nics in the host
        Returns:
            nics_dict   (list)  - list of nics in each esx host
                    key - esx_host
                    value- VMNetwork Adaptar
        """

        _nics_dict = {}
        self.prop_dict["property"] = "getNicDetail"
        output = self.machine._execute_script(os.path.join
                                              (self.utils_path, self.operation_ps_file),
                                              self.prop_dict)
        _stdout = output.output
        _temp_nics_list = _stdout.lstrip("getNicDetail = @{")
        _temp_nics_list = _temp_nics_list.rsplit("} @{")

        for each_nic in _temp_nics_list:
            each_nic_detail = each_nic.rsplit("; ")
            if ("Portgroup" in each_nic_detail[1] and
                    re.match("^[a-zA-Z0-9.= ]*$", each_nic_detail[1]) and
                    re.match("^[a-zA-Z0-9.= ]*$", each_nic_detail[0])):

                esx_name = each_nic_detail[0].split("ESX=")[1]
                port_group = each_nic_detail[1].split("Portgroup=")[1]
                _nics_dict[esx_name] = port_group

        return _nics_dict

    def _get_host_memory(self):
        """
        Get the free memory in the ESX

        Args:

        return:
                _esx_dict 	(dict)	- Dictionary of ESX and its free space

        Exception:
                Raise exception when failed to get Memory

        """
        try:
            _esx_dict = {}
            self.prop_dict["property"] = "GetESXDetail"
            if self.vcenter_version >= 6.5:
                self.log.info("Vmware Api is limited for HOST. Using powershell")
                '''
                #Vmware Api only gives ESX, name, id, and power state, Commenting the code.
                It can be used in future
                self._vmware_login()
                flag, response = self._make_request('GET', self._services['GET_ALL_ESX'])
                if flag:
                    for i in response.json()['value']:
                        if i['connection_state'] == 'CONNECTED'
                        and i['power_state'] == 'POWERED_ON':
                            _esx_name = i['name']
                            _esx_dict.setdefault(_esx_name, []).append(i['host'])
                '''
            else:
                self.log.info("Getting details for the HOST")
            self.prop_dict["property"] = "GetESXDetail"
            output = self.machine._execute_script(os.path.join
                                                  (self.utils_path, self.operation_ps_file),
                                                  self.prop_dict)
            _stdout = output.output
            _temp_esx_list = _stdout.lstrip("GetESXDetail = @{")
            _temp_esx_list = _temp_esx_list.rsplit("} @{")
            for each_esx in _temp_esx_list:
                each_esx_detail = each_esx.rsplit("; ")
                for each_esx_data in each_esx_detail:
                    each_esx_split = each_esx_data.split("=")
                    each_esx_split[1] = each_esx_split[1].strip("}\n")
                    _esx_dict.setdefault(each_esx_split[0], []).append(each_esx_split[1])
            return _esx_dict
        except Exception as err:
            self.log.exception("exception raised in GetMemory  ")
            raise err

    def _get_required_resource_for_restore(self, vm_list):
        """
        sums up all the memory of needs to be restores(passed as VM list)

        Args:
                vm_list	(list)	- list of vm to be restored

        returns:
                _vm_total_memory    (int)   -   Total memory required for restoring
                _vm_total_space (int)   -   Total disk space required for restoring
        """
        try:

            _vm_total_memory = 0
            _vm_total_space = 0
            for _each_vm in vm_list:
                self.VMs[_each_vm].update_vm_info('Memory')
                _vm_memory = self.VMs[_each_vm].Memory
                self.VMs[_each_vm].update_vm_info('VMSpace')
                _vm_space = self.VMs[_each_vm].VMSpace
                _vm_total_memory = _vm_total_memory + float(_vm_memory)
                _vm_total_space = _vm_total_space + float(_vm_space)
            return _vm_total_memory, _vm_total_space

        except Exception as err:
            self.log.exception(
                "An Aerror occurred in  _get_required_memory_for_restore ")
            raise err

    def _get_datastore_priority_list(self):
        """
        Returns the descending sorted datastore Dict according to free space
        Args:

        returns:
                _sorted_datastore_dict  (dict)  -   Returns the descending
                sorted datastore dict according to free space
        """
        try:
            _datastore_dict = self._get_datastore_dict()
            _datastore_dict = dict(zip(_datastore_dict.get('Name'),
                                       list(map
                                            (float,
                                             _datastore_dict.get
                                             ('FreeSpaceGB')))))
            _sorted_datastore_dict = OrderedDict(sorted
                                                 (_datastore_dict.items(),
                                                  key=itemgetter(1), reverse=True))
            return _sorted_datastore_dict

        except Exception as err:
            self.log.exception(
                "An Error occurred in  _get_datastore_priority_list ")
            raise err

    def _get_host_priority_list(self):
        """
        get the free host memory in ESX, sorted in descending order

        Args:

        returns:
                _sorted_proxy_dict  (dict)  -   Descending Sorted dict of esx according to free RAM
        """
        try:
            _proxy_dict = self._get_host_memory()
            _proxy_dict = dict(zip(_proxy_dict.get('Name'),
                                   list(map(float, _proxy_dict.get('MemoryFreeGB')))))
            _sorted_proxy_dict = OrderedDict(sorted(_proxy_dict.items(),
                                                    key=itemgetter(1), reverse=True))
            return _sorted_proxy_dict

        except Exception as err:
            self.log.exception("An Error occurred in  _get_host_priority_list ")
            raise err

    def _get_datastore_tree_list(self, datastore):
        """
        get the free host memory in proxy and arrange them with increarsing order

        Args:
            datastore   (string)    -   Datastore for which we need need to find the hierarchy

        returns:
                tree_list   (dict)  -   Dict contains parent ESX, Cluster,
                Datacenter for the datastore
        """
        try:
            self.prop_dict["property"] = "GetStructureTree"
            self.prop_dict["extra_args"] = datastore
            output = self.machine._execute_script(os.path.join
                                                  (self.utils_path, self.operation_ps_file),
                                                  self.prop_dict)
            _stdout = output._formatted_output
            tree_list = {}
            _temp_vm_list = _stdout.lstrip("GetStructureTree = ")
            _temp_vm_list = _temp_vm_list.split(" ")
            for each_vm in _temp_vm_list:
                each_vm1 = each_vm.rsplit(" ")
                for each_vmx in each_vm1:
                    each_vm2 = each_vmx.split("=")
                    tree_list.setdefault(each_vm2[0], []).append(each_vm2[1])
            return tree_list

        except Exception as err:
            self.log.exception("An error occurred in  _get_datastore_tree_list ")
            raise err

    def copy_test_data_to_each_volume(self, vm_name, _drive, backup_folder, _test_data_path):
        """
        copy testdata to each volume in the vm provided


        Args:
            vm_name (str)	    - vm to which test data has to be copied
            _drive  (str)		    - Drive letter where data needs to be copied
            _test_data_path (str) - path where testdata needs to be generated
            backup_folder   (str)  - name of the folder to be backed up

        returns:
            NULL
        Exception:

                if fails to generate testdata

                if fails to copy testdata

        """

        try:

            self.log.info("creating test data directory %s" % _test_data_path)
            self.log.info("Generating Test data folders")

            # initializing prerequisites
            _failed_file_list = []
            self.operation_dict["vm_name"] = vm_name
            self.operation_dict["vm_user"] = self.VMs[vm_name].user_name
            self.operation_dict["vm_pass"] = self.VMs[vm_name].password
            # create Base dir
            _dest_base_path = os.path.join(_drive, "\\" + backup_folder + "\\TestData\\")

            # copying files
            self.operation_dict["property"] = "COPYDATA"
            self.operation_dict["extra_args"] = _test_data_path + "@" + _dest_base_path
            _ps_path = os.path.join(
                self.utils_path, self.vm_operation_ps_file)
            _stdout = self.machine._execute_script(
                _ps_path, self.operation_dict)
            if "Error" in _stdout.output:
                _failed_file_list.append(_test_data_path)
            if _failed_file_list:
                raise Exception("Failed to copy x =some files %s" %
                                _failed_file_list)

        except Exception as err:
            self.log.exception(
                "An Error occurred in  Copying test data to Vm  ")
            raise err

    def get_disk_in_the_path(self, folder_path):
        """
         get all the disks in the folder

        Args:
            folder_path     (str)   - path of the folder from which disk needs to be listed
                                        e.g: C:\\CVAutomation

         Returns:
                disk_list   (list)-   list of disks in the folder

        Raises:
            Exception:
                if failed to get the list of files
        """
        try:
            _disk_list = []
            output = self.machine.get_files_in_path(folder_path)

            for value in output:
                disk_name = value
                if any(re.search(ext, disk_name.lower()) for ext in self.disk_extension):
                    _disk_list.append(disk_name)

            return _disk_list

        except Exception as err:
            self.log.exception(
                "Exception occurred {0} in getting disk list".format(err)
            )


class AzureHelper(Hypervisor):
    """
        Main class for performing all operations on AzureRM Hypervisor

        Methods:
                get_access_token()		                 - Get access token for any first authorization

                check_for_access_token_expiration()    - this function check if access_token is
                                                          expired if yes it will generate one

                copy_test_data_to_each_volume          - copy testdata to each volume in the vm

                update_hosts                           - Update the VM data Information

                collect_all_vm_data                    - Collect all VM Data

                collect_all_resource_group_data        - Collect All RG Info

                get_all_resource_group                 - get resource group info

                get_resourcegroup_name                 - gets the resource group of that VM

                get_resourcegroup_for_region           - get the Resource group for that particular
                                                         region

                compute_free_resources                 - compute all free resources required

        """

    def __init__(self,
                 server_host_name,
                 host_machine,
                 user_name,
                 password,
                 instance_type,
                 commcell):
        """
        Initialize Hyper-V Helper class properties
        """

        super(AzureHelper, self).__init__(server_host_name,
                                          host_machine,
                                          user_name,
                                          password,
                                          instance_type,
                                          commcell)
        self.disk_extension = [".vhd"]
        self.authentication_endpoint = 'https://login.microsoftonline.com/'
        self.azure_resourceURL = 'https://management.core.windows.net/'
        self.azure_baseURL = 'https://management.azure.com'
        self.azure_apiversion = "api-version="
        self._all_vmdata = {}
        self._all_rgdata = {}
        self.subscriptionID = 'd60bca80-e1a3-4117-aea3-09775a99d8cc'
        self.appID = '839b32ef-dc74-4971-9add-a98d51308e71'
        self.tenantID = 'da72dd62-58c6-4062-abf9-47be4e73c0f6'
        self.app_password = 'builder!12'
        self.azure_session = requests.Session()
        self.get_access_token()
        self.collect_all_resource_group_data()
        self.collect_all_vm_data()

    @property
    def default_headers(self):
        """
        provide the default headers required

        """
        self._default_headers = {"Content-Type": "application/json",
                                 "Authorization": "Bearer %s" % self.access_token}
        return self._default_headers

    @property
    def all_vmdata(self):
        """
        provide info about all VM's
        """
        if self._all_vmdata == None:
            self.collect_all_vm_data()

        return self._all_vmdata

    @all_vmdata.setter
    def all_vmdata(self, value):
        """
        sets the VM related info
        """
        key, value = value
        self._all_vmdata[key] = value

    @property
    def all_rgdata(self):
        """
        collects all resource group data

        """
        if self._all_rgdata == None:
            self.collect_all_resource_group_data()

        return self._all_rgdata

    @all_rgdata.setter
    def all_rgdata(self, value):
        """
        sets the resource group data

        """
        self._all_rgdata = value

    def get_access_token(self):
        """
        Get access token for any first authorization
        """
        try:
            self.log.info("Logging into Azure to get access token")
            import adal
            Context = adal.AuthenticationContext(self.authentication_endpoint + self.tenantID)
            Token_response = Context.acquire_token_with_client_credentials(self.azure_resourceURL,
                                                                           self.appID,
                                                                           self.app_password)
            self.access_token = Token_response.get('accessToken')
            self.log.info("Access Token is %s" % self.access_token)

        except Exception as err:
            self.log.exception("An exception occurred in getting the Access token")
            raise err

    def check_for_access_token_expiration(self):
        """
        this function check if access_token is expired if yes it will generate one
        """
        try:

            self.log.info("checking access token %s supplied is  valid" % self.access_token)
            is_sessionok = False
            count = 0
            while ((not is_sessionok) and (count < 3)):
                azure_list_subscriptionsURL = self.azure_baseURL + "/subscriptions?" \
                                              + self.azure_apiversion + "2017-05-10"
                self.log.info("Trying to get list of subscriptions usign post %s"
                              % azure_list_subscriptionsURL)
                data = self.azure_session.get(azure_list_subscriptionsURL,
                                              headers=self.default_headers)
                if data.status_code == 401:
                    if data["error"]["code"] == "ExpiredAuthenticationToken":
                        self.log.info("The session is unauthorized, trying to get new token")
                        count = count + 1
                        self.get_acess_token()
                    else:
                        self.log.info("The session is not expired , so there are credential issue")

                elif data.status_code == 200:
                    self.log.info("The Session is success no need to create new access token")
                    is_sessionok = True

                else:
                    self.log.info("There was error even after getting new token")
                    count = count + 1

        except Exception as err:
            self.log.exception("An exception occurred in getting the Access token")
            raise err

    def copy_test_data_to_each_volume(self, vm_name, _drive, backup_folder, _test_data_path):
        """
        copy testdata to each volume in the vm provided


        Args:
                vm_name    (str)        - vm to which test data has to be copied

                _test_data_path(str) - path where testdata needs to be generated

                backup_folder(str)  - name of the folder to be backed up

        Exception:

                if fails to generate testdata

                if fails to copy testdata

        """

        try:

            self.log.info("creating test data directory %s" % _test_data_path)
            for _drive in self.VMs[vm_name].drive_list:

                # initializing prerequisites
                _failed_file_list = []

                # create Base dir
                _dest_base_path = os.path.join(_drive, os.path.sep, backup_folder)
                if not self.VMs[vm_name].machine.check_directory_exists(_dest_base_path):
                    _create_dir = self.VMs[vm_name].machine.create_directory(_dest_base_path)
                    if not _create_dir:
                        _failed_file_list.append(_dest_base_path)

                self.log.info("Copying testdata to volume {0}".format(_drive))
                if self.VMs[vm_name].GuestOS == "Windows":
                    if self.machine.is_local_machine:
                        self.VMs[vm_name].machine.copy_from_local(_test_data_path,
                                                                  _dest_base_path)
                    else:
                        _dest_base_path = os.path.splitdrive(_dest_base_path)
                        network_path = "\\\\" + vm_name + "\\" + _dest_base_path[0].replace(
                            ":", "$") + _dest_base_path[-1]
                        self.machine.copy_folder_to_network_share(
                            _test_data_path, network_path,
                            vm_name + "\\" +
                            self.VMs[
                                vm_name].machine.username,
                            self.VMs[
                                vm_name].machine.password)
        except Exception as err:
            self.log.exception(
                "An error occurred in  Copying test data to Vm  ")
            raise err

    def update_hosts(self):
        """
        Update the VM data Information
        """
        try:
            self.collect_all_vm_data()
            self.collect_all_resource_group_data()

        except Exception as err:
            self.log.exception("An exception occurred in updating Host")
            raise err

    def collect_all_vm_data(self):
        """
        Collect all VM Data
        """
        try:
            _allrg = self.get_all_resource_group()
            for each_rg in _allrg:
                azure_list_vmURL = self.azure_baseURL + "/subscriptions/" + \
                                   self.subscriptionID + "/resourceGroups/" \
                                   + each_rg + "/providers/Microsoft.Compute/virtualMachines?" \
                                   + self.azure_apiversion + "2016-04-30-preview"
                self.log.info("Trying to get list of VMs usign post %s" % azure_list_vmURL)
                data = self.azure_session.get(azure_list_vmURL, headers=self.default_headers)
                _all_data = data.json()
                self.all_vmdata = (each_rg, _all_data)

        except Exception as err:
            self.log.exception("An exception occurred in collect_all_vmdata")
            raise err

    def collect_all_resource_group_data(self):
        """
        Collect All RG Info
        """
        try:
            AzureResourceGroupURL = self.azure_baseURL + "/subscriptions/" \
                                    + self.subscriptionID + "/resourceGroups?" \
                                    + self.azure_apiversion + "2014-04-01"
            self.log.info("Trying to get list of VMs usign post %s" % AzureResourceGroupURL)
            data = self.azure_session.get(AzureResourceGroupURL, headers=self.default_headers)
            self.all_rgdata = data.json()

        except Exception as err:
            self.log.exception("An exception occurred in CollectAllResourceGroupData")
            raise err

    def get_all_resource_group(self):
        """
        get All RG Info
        """

        try:
            _allrg_list = []
            datadict = self.all_rgdata
            for eachkey in datadict["value"]:
                rg_name = eachkey["name"]
                _allrg_list.append(rg_name)

            return _allrg_list

        except Exception as err:
            self.log.exception("An exception occurred in collect_all_resource_group_data")
            raise err

    def get__all_vms_in_hypervisor(self):
        """
        this gets all teh VM in the Subscriptions
        """
        try:

            _all_vmlist = []
            datadict = self.all_vmdata
            for eachdata, eachvalue in datadict.items():
                vm_info_value = eachvalue["value"]
                if vm_info_value != []:
                    for eachkey in vm_info_value:
                        vm_name = eachkey["name"]
                        _all_vmlist.append(vm_name)

            return _all_vmlist

        except Exception as err:
            self.log.exception("An exception occurred in getting the Access token")
            raise err

    def get_resourcegroup_name(self, vm_name):
        """
        Get the Resource group of that VM
        """
        try:

            resource_group_name = None
            datadict = self.all_vmdata
            for eachdata, each_value in datadict.items():
                self.log.info("Value in get_resource_group_name is " % each_value)
                if "value" in each_value:
                    vm_info_value = each_value["value"]
                    if vm_info_value != []:
                        for each_key in vm_info_value:
                            _vm_name = each_key["name"]
                            self.log.info("VMname %s in resource group %s" % (_vm_name, each_key))
                            if _vm_name == vm_name:
                                vm_id = each_key["id"]
                                temp_str = vm_id.split("/")
                                resource_group_name = temp_str[temp_str.index("resourceGroups") + 1]
                                break

                else:
                    self.log.info("Cannot collect information for this VM")
            return resource_group_name

        except Exception as err:
            self.log.exception("An exception occurred in getting the Resource group")
            raise err

    def get_resourcegroup_for_region(self, region):
        """
        get the Resource group for region
        """
        try:
            resource_group = []
            rg_data = self.all_rgdata
            for eachRG in rg_data["value"]:
                rg_region = eachRG["location"]
                if rg_region == region:
                    resource_group.append(eachRG["name"])

            return resource_group

        except Exception as err:
            self.log.exception("An exception occurred in get_resourcegroup_for_region")
            raise err

    def compute_free_resources(self, vm_name, resource_group=None):
        """
        compute all the free resources
        """
        try:
            sa_name = None
            if resource_group is None:
                datadict = self.all_vmdata
                for eachdata, eachvalue in datadict.items():
                    vm_info_value = eachvalue["value"]
                    if vm_info_value != []:
                        for eachkey in vm_info_value:
                            _vm_name = eachkey["name"]
                            self.log.info("Check vm %s in resourcegroup %s" % (eachkey, _vm_name))
                            if _vm_name == vm_name[0]:
                                region = eachkey["location"]
                                break

                resource_group = self.get_resourcegroup_for_region(region)

            for each_rg in resource_group:
                storage_account_url = self.azure_baseURL + "/subscriptions/" + \
                                      self.subscriptionID + "/resourceGroups/" + \
                                      each_rg + "/providers/Microsoft.Storage/storageAccounts?" \
                                      + self.azure_apiversion + "2017-06-01"
                self.log.info("Trying to get list of VMs usign post %s" % storage_account_url)
                data = self.azure_session.get(storage_account_url, headers=self.default_headers)
                if data.status_code == 200:
                    storage_account_data = data.json()
                    sa_value = storage_account_data["value"]
                    if sa_value != []:
                        for each_sa in storage_account_data["value"]:
                            sa_name = each_sa["name"]
                            resource_group = each_rg
                            break
                    else:
                        self.log.info("Failed to get SA details for this Resource Group")
                else:
                    self.log.info("Failed to get SA details for this Resource Group")

            return resource_group, sa_name

        except Exception as err:
            self.log.exception("An exception occurred in ComputeFreeResources")
            raise err


class FusionComputeHelper(Hypervisor):
    """
    Main class for performing all operations on Fusion Compute Hypervisor
    """

    def __init__(self, server_host_name,
                 host_machine,
                 user_name,
                 password,
                 instance_type,
                 commcell):

        super(FusionComputeHelper, self).__init__(server_host_name, host_machine,
                                           user_name, password, instance_type, commcell)

        self.vm_dict = {}
        self._services = FusionComputeServices.get_services(self.server_host_name)
        self._headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'Accept-Language': 'en_US',
            'X-Auth-Token': None
            }

        self.version = self.get_version()

        self._vm_services = FusionComputeServices.get_vm_services(self.server_host_name, 
                                                                  self._get_site_url())
        self.get_all_vms_in_hypervisor()

    def get_version(self):
        """
        Get the Fusion Compute Hypervisor Version Provided
        :return:
            version    (str)    : version of the Fusion COmpute Hypervisor
        """

        try:
            flag, response = self._make_request('GET', self._services['GET_VERSION'])
            if flag:
                latest_version = response.json()["versions"][-1]
                self._headers["version"] = latest_version["version"]
                self._compute_login()
                return latest_version["version"]

            raise response.json()

        except Exception as err:
            self.log.exception("An exception {0} occurred "\
                               "getting version from VRM".format(err))
            raise Exception(err)

    def _compute_login(self):
        """
        Does login to the Fusion compute Hypervisor
        :return:
            set the token in headers
        """

        try:

            hash_object = hashlib.sha256(self.password.encode('UTF-8'))
            self._headers['X-Auth-User'] = self.user_name
            self._headers['X-Auth-Key'] = hash_object.hexdigest()
            self._headers['X-Auth-AuthType'] = '0'
            self._headers['X-Auth-UserType'] = '0'
            flag, response = self._make_request('POST', self._services['LOGIN'])
            if flag:
                self._headers['X-Auth-Token'] = response.headers['x-auth-token']
                self._headers.pop('X-Auth-User', None)
                self._headers.pop('X-Auth-Key', None)
                self._headers.pop('X-Auth-AuthType', None)
                self._headers.pop('X-Auth-UserType', None)

        except Exception as err:
            self.log.exception("An exception occurred while logging in to the VRM")
            raise Exception(err)

    def _make_request(self, method, url, payload=None, attempts=0):
        """Makes the request of the type specified in the argument 'method'

        Args:
            method    (str)         --  http operation to perform, e.g.; GET, POST, PUT, DELETE

            url       (str)         --  the web url or service to run the HTTP request on

            payload   (dict / str)  --  data to be passed along with the request
                default: None

            attempts  (int)         --  number of attempts made with the same request
                default: 0

        Returns:
            tuple:
                (True, response) - in case of success

                (False, response) - in case of failure

        Raises:
            Fusion Compute SDK Exception:
                if the method passed is incorrect/not supported

            requests Connection Error   --  requests.exceptions.ConnectionError

        """
        try:
            headers = self._headers

            if method == 'POST':
                response = requests.post(url, headers=headers, 
                                         verify=True, auth=payload)
            elif method == 'GET':
                response = requests.get(url, headers=headers, verify=True)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, 
                                        verify=True, json=payload)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, verify=True)
            else:
                raise Exception('HTTP method {} not supported'.format(method))

            if response.status_code == 401 and headers['X-Auth-Token'] is not None:
                if attempts < 3:
                    self._compute_login()
                    return self._make_request(method, url, attempts + 1)
                else:
                    # Raise max attempts exception, if attempts exceeds 3
                    raise Exception('Error', '103')

            elif response.status_code == 200:
                return True, response
            else:
                return False, response

        except requests.exceptions.ConnectionError as con_err:
            raise Exception(con_err)

    def _get_site_url(self):
        """
        Get the site urn for the Fusion VRM
        :return:
            site_url (str)  - site url for querying about VMs
        """

        try:
            flag, response = self._make_request('GET', self._services['GET_SITES'])
            if flag:
                site_url = response.json()['sites'][0]['uri']

            return site_url

        except Exception as err:
            self.log.exception(
                    "An exception {0} occurred getting version from VRM".format(err)
                    )
            raise Exception(err)

    def update_hosts(self):
        """
        update the Information of Host
        """
        try:
            flag, response = self._make_request('GET', self._vm_services['GET_VMS'])
            if flag:
                vm_list_response = response.json()['vms']
                for vm in vm_list_response:
                    self.vm_dict[vm['name']] = vm['uri']
                    return

            raise Exception(response.json())

        except Exception as err:
            self.log.exception(
                    "An exception {0} occurred getting VMs from VRM".format(err)
                    )
            raise Exception(err)


    def get_all_vms_in_hypervisor(self, server=""):
        """
       Get all the vms for Fusion Compute

       Args:
            server (str)   -  VRM  for which all the VMs has to be fetched

       Returns:
           _all_vm_list    (str)   -   List of VMs in the host of the pseudoclient
       """

        try:
            _temp_vm_list = []
            vm_list = []
            flag, response = self._make_request('GET', self._vm_services['GET_VMS'])
            if flag:
                vm_list_response = response.json()['vms']
                for vm in vm_list_response:
                    self.vm_dict[vm['name']] = vm['uri']
                    _temp_vm_list.append(vm['name'])

            for each_vm in _temp_vm_list:
                if each_vm != "":
                    each_vm = each_vm.strip()
                    if re.match("^[A-Za-z0-9_-]*$", each_vm):
                        vm_list.append(each_vm)
                    else:
                        self.log.info(
                            "Unicode VM are not supported for now")

            return vm_list

        except Exception as err:
            self.log.exception("An exception {0} occurred getting VMs from VRM".format(err))
            raise Exception(err)

    def _get_datastore_dict(self):
        """
        Get the list of datastore in an Host in VRM

        Args:

        Return:
                _disk_size_dict	(dict)	- Datastores with name name free spaces

        """
        try:
            _disk_size_dict = {}
            flag, response = self._make_request('GET', self._vm_services['GET_DATASTORES'])
            if flag:
                disk_list_response = response.json()['datastores']
                for disk in disk_list_response:
                    _disk_size_dict[disk['name']] = disk['actualFreeSizeGB']

            return _disk_size_dict

        except Exception as err:
            self.log.exception(
                    "An exception {0} occurred getting datastores  from VRM".format(err)
                    )
            raise Exception(err)

    def _get_host_dict(self):
        """
        Get the list of hosts  in VRM

        Args:

        Return:
                _host_dict	(dict)	- host with name and freememory

        """
        try:
            _host_dict = {}
            flag, response = self._make_request('GET', self._vm_services['GET_HOSTS'])
            if flag:
                host_dict_response = response.json()['hosts']
                for host in host_dict_response:
                    _host_dict[host['name']] = (host['memQuantityMB'])/1024

            return _host_dict

        except Exception as err:
            self.log.exception(
                    "An exception {0} occurred getting hosts  from VRM".format(err)
                    )
            raise Exception(err)

    def _get_datastore_priority_list(self):
        """
        Returns the descending sorted datastore Dict according to free space
        Args:

        returns:
                _sorted_datastore_dict  (dict)  -   Returns the descending
                sorted datastore dict according to free space
        """
        try:
            _datastore_dict = self._get_datastore_dict()
            _sorted_datastore_dict = OrderedDict(sorted
                                                 (_datastore_dict.items(),
                                                  key=itemgetter(1), reverse=True))
            return _sorted_datastore_dict

        except Exception as err:
            self.log.exception("An exception {0} occurred getting datastore priority list from VRM".format(err))
            raise Exception(err)

    def _get_host_priority_list(self):
        """
        Returns the descending sorted host Dict according to Memory
        Args:

        returns:
                _sorted_host_dict  (dict)  -   Returns the descending
                sorted datastore dict according to Memory
        """
        try:
            _host_dict = self._get_host_dict()
            _sorted_host_dict = OrderedDict(sorted
                                                 (_host_dict.items(),
                                                  key=itemgetter(1), reverse=True))
            return _sorted_host_dict

        except Exception as err:
            self.log.exception("An exception {0} occurred getting host priority list from VRM".format(err))
            raise Exception(err)

    def _get_required_resource_for_restore(self, vm_list):
        """
        get the required resource for restore
        :param vm_list:  list of Vms for restore
        :return:
            _vm_total_memory    (int)   -   Total memory required for restoring
            _vm_total_space (int)   -   Total disk space required for restoring
        """

        try:
            _vm_total_memory = 0
            _vm_total_space = 0
            for _each_vm in vm_list:
                self.VMs[_each_vm].update_vm_info('Memory')
                _vm_memory = self.VMs[_each_vm].Memory
                self.VMs[_each_vm].update_vm_info('VMSpace')
                _vm_space = self.VMs[_each_vm].VMSpace
                _vm_total_memory = _vm_total_memory + float(_vm_memory)
                _vm_total_space = _vm_total_space + float(_vm_space)
            return _vm_total_memory, _vm_total_space

        except Exception as err:
            self.log.exception(
                "An Aerror occurred in  _get_required_memory_for_restore ")
            raise err

    def compute_free_resources(self, vm_list):
        """
        compute the free Resource of the Vcenter based on free memory and cpu

        Args:

                vm_list		(list) - list of Vms to be restored

        return:
                Datastore	(str)	- the Datastore where restore can be performed

                Host     (str)	- Host where restore has to be performed

        """
        try:
            datastore_name = None
            host_name = None
            _datastore_priority_dict = self._get_datastore_priority_list()
            _host_priority_dict = self._get_host_priority_list()
            _total_vm_memory, _total_disk_space = self._get_required_resource_for_restore(vm_list)
            for each_datastore in _datastore_priority_dict.items():
                if (each_datastore[1]) > _total_disk_space:
                    datastore_name = each_datastore[0]
                    self.log.info(""
                                  "The Datastore %s has more than total"
                                  "disk space in VM" % datastore_name)
                    break
                else:
                    continue

            for each_host in _host_priority_dict.items():
                if (each_host[1]) > _total_vm_memory :
                    self.log.info(
                        "the Host %s has higher "
                        "memory than the total VMs" % each_host[1])
                    host_name = each_host[0]
                    break
                else:
                    continue

            return datastore_name, host_name

        except Exception as err:
            self.log.exception(
                    "An exception {0} occurred in computing free resources for restore".format(err)
                    )
            raise Exception(err)

