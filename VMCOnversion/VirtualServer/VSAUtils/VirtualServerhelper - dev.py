#!/usr/bin/env python

# --------------------------------------------------------------------------
# Copyright 2016 Commvault Systems, Inc.
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
import time
from copy import deepcopy
from AutomationUtils.machine import Machine
from .HypervisorHelper import Hypervisor
from . import VirtualServerConstants
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

            _check_backup_job_type_expected()   - check the passed job id type and passed job type is expeted

            _client_exist_in_cs()       - check if the client exist in CS

            get_job_duration()          - get the job duration of the job passed

            get_job_results_dir()                   - get the job results directory of the client
                                        (default: commserv client)

    """

    def __init__(self, testcase):
        """
        Initialize the  SDK objects
        """

        self.log = logger.get_log()
        self.commcell = testcase.commcell
        self.csdb = testcase.csdb
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
            self.log.info("Getting the client ID for %s " % client_name)
            _client_obj = self.commcell.clients.get(client_name)
            return _client_obj.client_id

        except Exception as errrr:
            self.log.exception(
                "An exception occured in getting the client ID %s" % X)
            raise errrr

    def get_hostname_for_client(self, client_name=None):
        """
        Get the Host name for the given HostName

        Args:
                client_name     (str)   - Client name for which client Id
                                                                                need to be fetched
                        default:    (str)   commsev_name

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

        except Exception as errrr:
            self.log.exception(
                "An exception occured in getting the client ID %s" % X)
            raise errrr

    def get_base_dir(self, client_name=None):
        """
        Get the base directory for the commvault installation

        Args:
                client_name     (str)   - Client name for which client Id
                                                                        need to be fetched
                        default:    (str)   commsev_name

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

        except Exception as errrr:
            self.log.exception("Error in getting the base directory %s" % X)
            raise errrr

    def get_client_os_type(self, client_name=None):
        """
        Gets the OS type [Windows / Unix] of the client

        Args:
                client_name     (str)   - Client name for which os info
                                                                        need to be fetched
                        default:    (str)   commsev_name
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
                                default(str)    - commserv_name

                Exception:
                        if client does jnot exist in cs
        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.job_results_dir

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

    def find_snap_copy_id(self, sp_id: object) -> object:
        """
        find the snap copy id of the specified storage policy

        Args:
                sp_id   (int)   : storage policy id

        Return:
                snap copy id of that storage policy
        """

        try:
            _query = "select copy from archgroup AG,archGroupCopy AGC where AGC.isSnapCopy = 1 and \
                                    ag.id = AGC.archGroupId and AGC.archGroupId = '%s'" % sp_id

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred getting Sp details details")

            return _results[0]

        except Exception as err:
            self.log.exception("An Aerror occurred in FindSnapCopyId ")
            raise err

    def find_aux_copy_id(self, sp_id):
        """
        find the aux copy id of the specified storage policy

        Args:
                sp_id   (int)   : storage policy id

        Return:
                aux copy id of that storage policy
        """

        try:
            _query = "select copy from archgroup AG,archGroupCopy AGC where \
                            ag.id = AGC.archGroupId and AGC.archGroupId = '%s'" % sp_id

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred getting Sp details details")

            return _results[0]

        except Exception as err:
            self.log.exception("An Aerror occurred in find_aux_copy_id ")
            raise err


class AutoVSAVSClient(object):
    """
    Main class for performing all VSClient operations

    Methods:
       enable_snap_on_client - Enable intellisnap on client

    """


    def __init__(self, commcell_obj, testcase):
        """Initialize all the class properties of AutoVSAVSClient class"""
        self.log = logger.get_log()
        self.auto_commcell = commcell_obj
        self.vsa_client = testcase.client
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
                "Success - enabled snap on client: [%s]", (self.vsa_client_name))

        except Exception as err:
            self.log.error("Failed Enable Snap on client")
            raise Exception("Exception in EnableSnapOnClient:" + str(err))

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

    def __init__(self , auto_client, testcase):
        """Initialize all the class properties of AutoVSAVSInstance class"""
        self.auto_vsaclient = auto_client
        self.auto_commcell = self.auto_vsaclient.auto_commcell
        self.csdb = testcase.csdb
        self.vsa_agent = testcase.agent
        self.vsa_instance = testcase.instance
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
            self.log.exception("An exception {0} has occurred while setting coordinator client ".format(X))
    
    @property
    def Co_ordinator(self):
        """Retuens Proxy list assocaited witht hat VSInstance . Read only attribute"""
        if self.vsa_co_ordinator is None:
            self.vsa_co_ordinator = self.vsa_instance.co_ordinator
    
        return self.vsa_co_ordinator
    
    @Coordinator.setter
    def Co_ordinator(self, Coordinator):
        """
        set the proxy given as coordinator
        
        Args:
            Coordinator - Proxy that needs to be set as coordinator
        """
        try:

            coordinator_client  = self.auto_commcell.commcell.clients.get(Coordinator)
            temp_vsa_proxy_list = [coordinator_client.client_name]+self.vsa_proxy_list
            self.vsa_proxy_list = list(set(temp_vsa_proxy_list))
            
            self.proxy_list = self.vsa_proxy_list
        
        except Exception as err:
            self.log.exception("An exception {0} has occurred while setting coordinator client ".format(e))
        

    @property
    def fbr_ma(self):
        """Returns FBRMA assocaited witht hat VSInstance . Read only attribute"""
        return self.vsa_instance.fbr_MA_Unix
    
    @FBRMA.setter
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
    
        Args:
                vsa_client  (str)   -- virtualization client for which proxy list is fetched
    
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
                host_name = self.vsa_instance.server_name
            
            else:
                host_name = (self.auto_commcell.commcell.clients.get(client_name)).client_hostname
    
            if self.host_name is None:
                setattr(self, "host_name", host_name)
    
            self._compute_credentials()
            hvobj = Hypervisor(host_name, self.user_name,
                               self.password, self.vsa_instance_name, self.auto_commcell)
    
            return hvobj
    
        except Exception as err:
            self.log.exception(
                "An Exception occurred in creating the Hypervisor object  %s" % err)
            raise err
    
    def _compute_credentials(self):
        """Compute the credentials required to call the Vcenter"""
    
        try:
            _query = "Select attrval from APP_InstanceProp where attrname IN \
                      ('Virtual Server Password','Virtual Server User') and componentNameId = ( \
                      select TOP 1 instance  from APP_Application where clientId= ( \
                Select TOP 1 id from App_Client where name = '%s'))" \
                                       %self.auto_vsaclient.vsa_client_name
    
            self.csdb.execute(_query)
            _results = self.csdb.fetch_all_rows()
            if not(_results):
                raise Exception("An exception occurred getting server details")
    
            self.user_name = _results[0][0].strip()
            _password = _results[1][0].strip()
            #self.user_name = ".\\administrator"
            #self.password = "builder!12"
            self.password = cvhelper.format_string(self.auto_commcell.commcell,_password)
    
        except Exception as err:
            self.log.exception(
                "An Exception occurred in getting credentials for Compute Credentials  %s" % err)
            raise err
    
    
class AutoVSABackupset(object):
    """
    class for performing backupset operations. it acts as wrapper for Testcase and SDK
    """
    
    def __init__(self, InstanceObj, testcase):
        """
        Initialize SDK objects
        """
        self.auto_vsainstance = InstanceObj
        self.auto_commcell = self.auto_vsainstance.auto_vsaclient.auto_commcell
        self.log = self.auto_vsainstance.log
        self.vsa_agent = self.auto_vsainstance.vsa_agent
        self.backupset = testcase.backupset
        self.backupset_name = self.backupset.backupset_name
        self.backupset_id = self.backupset.backupset_id


class AutoVSASubclient(object):
    """
    class for performing subclient operations. It act as wrapper for Testcase and SDK
    """
    
    def __init__(self, backupset_obj, testcase):
        """
        Initialize subclient SDK objects
        """
    
        self.auto_vsa_backupset = backupset_obj
        self.log = self.auto_vsa_backupset.log
        self.auto_vsainstance = self.auto_vsa_backupset.auto_vsainstance
        self.auto_vsaclient = self.auto_vsainstance.auto_vsaclient
        self.vsa_agent = self.auto_vsainstance.vsa_agent
        self.auto_commcell = self.auto_vsainstance.auto_commcell
        self.csdb = testcase.csdb
        self.hvobj = self.auto_vsainstance.hvobj
        self.subclient = testcase.subclient
        self.subclient_name = self.subclient.subclient_name
        self.subclient_id = self.subclient.subclient_id
        self.quiesce_file_system = True
        self._disk_filter = []
        self._disk_filter_input = None
        self._vm_record = {}
        self.vm_filter = None
        self.vm_content = None
        self.set_content_details()
        # self.set_disk_filter_details()
    
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
    def SetVMContent(self):
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
    
    @SetVMContent.setter
    def SetVMContent(self, content):
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
        self.vm_content = content
        self.set_content_details()
    
    @property
    def browse_ma(self):
        self._browse_ma = self.subclient.storage_ma
        self._browse_ma_id = self.subclient.storage_ma_id
        return self._browse_ma, self._browse_ma_id
    
    def __deepcopy__(self, tempobj):
        """
        over ride deepcopy method
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
                                                (_AppId, VirtualServerConstants.app_type)
    
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
    
            if self.vm_content is None:
                _vm_content_string = self._prepare_content_string_from_dict(
                    self.subclient.content)
                _vm_content_dict = self.subclient.content
    
            elif isinstance(self.vm_content, str):
                _vm_content_string = self.vm_content
                option, equality, pattern = self.split_content_string(
                    _vm_content_string)
                _vm_content_dict = self._prepare_content_dict_from_string(
                    option, pattern, equality)
    
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
                if not self.subclient.vm_filter is None:
                    _vm_filter_string = self._prepare_content_string_from_dict(
                        self.subclient.vm_filter)
                    _vm_filter_dict = self.subclient.vm_filter
    
            elif isinstance(self.vm_content, str):
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
                                'type': 9(VM),1(Host)
                                        }
        
        returns:
                vm_content_string   -(str)  - [VM]=equals=test1
        """
        try:
            _vm_content_string = ''
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
                    vm_content_string = vm_content_string+_vm_content_string
                    continue
        
                elif _vm_display_name.endswith('*'):
                    _equality = "Starts with"
                    _pattern = _vm_display_name[:-1]
                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + ","
                    vm_content_string = vm_content_string+_vm_content_string
                    continue
        
        
                elif "*" in _vm_display_name:
                    if _each_vm["equal_value"]:
                        _equality = "Contains"
                    else:
                        _equality = "Does not Contains"
        
                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + "," 
                    vm_content_string = vm_content_string+_vm_content_string
                    continue
        
                elif _each_vm["equal_value"]:
                    _equality = "Equals"
                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + "," 
                    vm_content_string = vm_content_string+_vm_content_string
                    continue
        
                else:
                    _equality = "Does Not Equals"
                    content_str = _option + "=" + _equality + "=" + _pattern
                    _vm_content_string = content_str + ","
                    vm_content_string = vm_content_string+_vm_content_string
                
        
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
    
            #self.subclient.content = vm_content_dict
    
            #if vm_filter_dict != {}:
                #self.subclient.vm_filter = vm_filter_dict
    
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
                _hypervisor_vm_list = []
                _hypervisor_vm_list.append(pattern)
    
            else:
                _hypervisor_vm_list = self.hvobj.get_all_vms_in_hypervisor()
    
            for _each_vm in _hypervisor_vm_list:
                if not _each_vm in self.hvobj.VMs.keys():
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
    
                pattern     (str)   -patterns which needs to bematched with the vm  like test*,test*1
    
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
                                                                        & ((pattern[0] != '.'))):
                pattern = pattern + '$'
                match = re.match(pattern, vm, flags=re.I)
    
            elif((pattern[0] != '.')):  # pattern of the form abc*
                match = re.match(pattern, vm, flags=re.I)
    
            # pattern of the form *abc
            elif((pattern[len(pattern) - 1] != '*') & (pattern[len(pattern) - 1] != '+')):
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
            listvalue = []
            listvalue = pattern_string.split("=")
            if len(listvalue) == 3:
                option = (listvalue[0]).strip()
                equality = (listvalue[1]).strip()
                pattern = (listvalue[2]).strip()
                # commenting out filter string for now since its functionality is done by MatchPatternforFilter
                #pattern = self.FetchPatterfromFilterString(equality, pattern)
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
    
                    if(((equality == "Does Not Equals") | (equality == "Does Not Contains"))
                                                                            & (_retcode == True)):
                        _disqualified_list.append(vm)
    
                    elif _retcode == True:
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
    
                return:
                        non_dynamic_content -   (list)  - list of Vms from non dynamic contetn
    
                        dynamic_list        -   (list)  - list of Vms from dynamic content
    
    
        """
        self.log.info("Processing VM content is %s" % content)
        try:
            self.log.info("getting VMs using GetVMlist()")
            non_dynamic_content = []
    
            non_dynamic_list, dynamic_content = self._is_dyanamic_content(content)
    
            if non_dynamic_list != []:
                for _each_content in non_dynamic_list:
                    _pattern_list = _each_content.split("=")
                    non_dynamic_content.append(_pattern_list[1])
    
            if len(dynamic_content) == 0:
                for _each_vm in non_dynamic_content:
                    if not _each_vm in self.hvobj.VMs.keys():
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
                content_string = self.vm_content
    
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
    
        except Exception as errrr:
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
            _vm_content_dict = {}
            _vm_content_dict[pattern] = {}
            _vm_content_dict[pattern]["name"] = pattern
            _vm_content_dict[pattern]["displayName"] = pattern
            _vm_content_dict[pattern]["path"] = ""
    
            if not equality is None:
                if (equality == "Does Not Equals") or (equality == "Does Not Contains"):
                    _vm_content_dict[pattern]["equalsOrNotEquals"] = False
                else:
                    _vm_content_dict[pattern]["equalsOrNotEquals"] = True
    
            else:
                _vm_content_dict[pattern]["equalsOrNotEquals"] = True
    
            if option == "[VM]":
                if(is_dynamic):
                    _vm_content_dict[pattern]["type"] = "10"
                else:
                    _vm_content_dict[pattern]["type"] = "9"
                    _vm_content_dict[pattern]["path"] = self.hvobj.VMs[pattern].GUID
    
            else:
                con_type = [_key for _key, _value in VirtualServerConstants.content_type.items(
                ) if _value == option][0]
                _vm_content_dict[pattern]["type"] = "%s" % con_type
    
            return _vm_content_dict
    
        except Exception as err:
            self.log.exception(
                "An exception occurred in  CreateContentinSCFormat %s" % err)
            raise err
    
    def vsa_discovery(self):
        """
        Creates testdata path and generate testdata and copy the test data to each drive in VM .
        """
        try:
            self.log.info("TesdataPath provided is %s" % self.testdata_path)
            for _vm in self.vm_list:
                self.hvobj.VMs[_vm].update_vm_info('All')
                for _drive in self.hvobj.VMs[_vm].drive_list:
                    self.log.info("COpying Testdata to Drive %s" % _drive)
                    self.hvobj.copy_test_data_to_each_volume(_vm,_drive,self.testdata_path)
    
        except Exception as errrr:
            self.log.exception(
                "Exception while doing VSA Discovery  :" + str(X))
            raise errrr
    
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
            self.testdata_path = backup_option.testdata_path
            self.vsa_discovery()
    
            _backup_job = self.subclient.backup(backup_option.BackupType,
                                        backup_option.run_incr_before_synth,
                                        backup_option.incr_level, backup_option.CollectMetadata)
    
            if not _backup_job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " +
                    str(_backup_job.delay_reason)
                )
            self.log.info("Backup Job %s completed successfully" %
                          _backup_job.job_id)
            self.log.info("Backup Job got complete")
    
            self.log.info(
                "Checking if Job type is Expected for job ID %s" % _backup_job.job_id)
            self.auto_commcell._check_backup_job_type_expected(
                _backup_job.job_id, VirtualServerConstants.backup_type[backup_option.BackupType])
    
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
    
            for _vm in self.vm_list:
    
                # forLive browse
                is_live_browse = self._check_if_live_browse(
                    self.hvobj.VMs[_vm].machine, fs_restore_options.CollectMetadata)
                if(is_live_browse):
                    self.log.info(
                        "Calculating the diskcount of the MA before restore")
                    ma_machine = Machine(fs_restore_options.BrowseMA)
                    _stdout = ma_machine.execute_command(
                        VirtualServerConstants.disk_count_command)
                    _disk_count_before_restore = _stdout.output.strip()
    
                for _drive in self.hvobj.VMs[_vm].drive_list:
    
                    _preserve_level = self.hvobj.VMs[_vm].preserve_level
                    self.log.info("Restore dest path " +
                                  fs_restore_options.RestorePath)
                    _fs_path_to_browse = _drive + "\\TestData"
    
                    self.dest_location = os.path.join(
                        fs_restore_options.RestorePath, _vm, _drive)
                    fs_restore_job = self.subclient.guest_file_restore(
                                            _fs_path_to_browse, fs_restore_options.DestinationClient,
                                             self.dest_location, fs_restore_options.copy_precedence,
                                             _preserve_level, fs_restore_options.UnconditionalOverwrite)
    
                    if not fs_restore_job.wait_for_completion():
                        raise Exception(
                            "Failed to run file level restore  job with error: " +
                            str(fs_restore_job.delay_reason)
                        )
    
                    self.log.info("file level restore  Job got complete")
    
                    # File level Validation
                    self.fs_testdata_validation(
                        fs_restore_options.client_machine, self.dest_location, _vm)
    
                if is_live_browse:
                    self.perform_block_level_validation(
                        _disk_count_before_restore, ma_machine, _vm)
    
            self.log.info(
                "Ran file level restore from all the VMs and its drives")
    
        except Exception as err:
            self.log.exception(
                "Exception at restore job please check logs for more details %s", str(err))
            self.log.info("Restore: FAIL - File level files Retore Failed")
            raise err
    
    def fs_testdata_validation(self, dest_client, dest_location, vm_name):
        """
        Does Validation of Backed up and data restored from file level
    
        Args:
                dest_client     (obj)   -   Machine class object of Destination client
    
                dest_location   (str)   - destination location of file level restore job
    
        Exception
                if folder comparison fails
    
    
        """
        try:
            _diff_file_list = self.hvobj.VMs[vm_name].host_machine.compare_folders(
                dest_client, self.testdata_path, dest_location)
    
            if not _diff_file_list:
                self.log.info("checksum mismatched for files  %s" %
                              _diff_file_list)
                raise Exception("Folder Comparison Failed for Source:%s and destination %s" % (
                    self.testdata_path, dest_location))
    
        except Exception as err:
            self.log.exception("Exception in FSTestdataValidation")
            raise err
    
    def _check_if_windows_live_browse(self, os_name, metadata_collected):
        """
        Decides Live browse validation need to be perfomred or not.
    
        Args:
                machine             (str)   - machien object of backups VM
    
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
    
    def disk_restore(self, disk_restore_options):
        """
    
        perform Disk restore for specific subclinet
    
        Args:
                disk_restore_options    -options that need to be set while performing disk  restore
    
        Exception:
                        if job fails
                        if validation fails
    
        """
        try:
            for _vm in self.vm_list:
    
                self.disk_restore_dest = os.path.join(
                    disk_restore_options.Restoredest, _vm)
                disk_restore_job = self.subclient.disk_restore(
                                            _vm, disk_restore_options.DestinationClient,
                                            self.disk_restore_dest, disk_restore_options.Overwrite,
                                            disk_restore_options.CopyPreecedence)
    
                if not disk_restore_job.wait_for_completion():
                    raise Exception(
                        "Failed to run file level restore  job with error: " +
                        str(disk_restore_job.delay_reason)
                    )
    
                self.log.info("Disk restore job completed successfully")
    
                if isinstance(self.hvobj.VMs[_vm].machine, "WindowsMachine"):
                    self.disk_validation(_vm, disk_restore_options)
    
        except:
            self.log.exception("Exception occurred please check logs")
            raise Exception("Disk Restore Job failed, please check agent logs")
    
    def disk_validation(self, _vm, disk_restore_options):
        """
        Performs Disk Validation by mounting the restored disk on the Host
    
        Args:
    
        _vm                     (str)   - vm name for which disk restore is performed
    
        disk_restore_options    (obj)   - options of Disk restore options classs
    
        Exception:
                        if job fails
                        if validation fails
    
        """
        try:
    
            _list_of_disks = None
            self.log.info("Performed Restore in client %s" %
                          disk_restore_options.DestinationClient)
            dest_machine = Machine(
                disk_restore_options._dest_host_name, self.auto_commcell.commcell)
            dest_client_hypervisor = self.auto_vsainstance._create_hypervisor_object(
                disk_restore_options.DestinationClient)
    
            _list_of_disks = dest_machine.get_files_in_path(
                disk_restore_options.Restoredest)
    
            _vm_disk_list = self.hvobj.VMs[_vm].disk_list
            if _vm_disk_list == []:
                self.log.info(
                    "Cannot validate the Disk as we cannot find the disk attached to the VM")
                return False
    
            if not((_list_of_disks is None) or (_list_of_disks == [])):
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
    
            if _final_mount_disk_list == []:
                _final_mount_disk_list = _list_of_disks
    
            for _file in _final_mount_disk_list:
                self.log.info("Validation Started For Disk :[%s]" % (_file))
                _drive_letter = dest_client_hypervisor.mount_disk(_vm, _file)
                if(_drive_letter != -1):
                    for each_drive in _drive_letter:
                        dest_folder_path = VirtualServerConstants.get_folder_to_be_compared(
                            self.backup_folder_name, each_drive)
                        self.log.info("Folder comparison started...")
                        time.sleep(5)
                        self.fs_testdata_validation(
                            disk_path.DestinationClient, dest_folder_path, _vm)
                else:
                    self.log.error("ERROR - Error mounting VMDK " + _file)
                    raise Exception("Exception at Mounting Disk ")
    
                dest_client_hypervisor.un_mount_disk(_vm, _file)
    
        except Exception as err:
            self.log.exception("Exception occurred please check logs")
            dest_client_hypervisor.un_mount_disk(_vm, _file)
            raise err
    
    def virtual_machine_restore(self, vm_restore_options):
        """
        perform Full VM restore for specific subclinet
    
        Args:
                vm_restore_options  -options that need to be set while performing vm  restore
    
        Exception:
                        if job fails
                        if validation fails
    
        """
        try:
    
            if vm_restore_options.InPlaceOverwrite:
                vm_restore_job = self.subclient.full_vm_restore_in_place(
                        self.vm_list, vm_restore_options.UnconditionalOverwrite,
                        vm_restore_options.PowerOnAfterRestore, vm_restore_options.CopyPreecedence,
                        vm_restore_options.RegisterwithFailover)
    
            else:
                vm_restore_job = self.subclient.full_vm_restore_out_of_place(
                        vm_restore_options.DestinationClient,
                        vm_restore_options.DestinationPath, vm_restore_options.UnconditionalOverwrite,
                        vm_restore_options.PowerOnAfterRestore, vm_restore_options.CopyPreecedence,
                        vm_restore_options.RegisterwithFailover)
    
            if not vm_restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run VM  restore  job with error: " +
                    str(vm_restore_job.delay_reason)
                )
    
        except Exception as err:
            self.log.error("Exception while submitting Restore job:" + str(X))
            raise err
