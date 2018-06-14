﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for operating on a Virtual Server VMWare Subclient.

VMWareVirtualServerSubclient is the only class defined in this file.

VMWareVirtualServerSubclient:   Derived class from VirtualServerSubClient Base
                                class,representing a VMware Subclient,
                                and to perform operations on that Subclient

VMWareVirtualServerSubclient:

    __init__(
        backupset_object,
        subclient_name,
        subclient_id)           --  initialize object of vmware subclient class,
                                    associated with the VirtualServer subclient

    full_vm_restore_in_place()  --  restores the VM specified by the user to
                                    the same location

    full_vm_restore_out_of_place() -- restores the VM specified to the provided
                                      VMware psuedoclient vcenter via
                                      vcenter_client

"""

from ..vssubclient import VirtualServerSubclient
from ...exception import SDKException
from past.builtins import basestring


class VMWareVirtualServerSubclient(VirtualServerSubclient):
    """Derived class from VirtualServerSubclient Base class.
       This represents a VMWare virtual server subclient,
       and can perform restore operations on only that subclient.

    """

    def __init__(self, backupset_object, subclient_name, subclient_id=None):
        """Initialize the Instance object for the given Virtual Server instance.
        Args
        class_object (backupset_object, subclient_name, subclient_id)  --  instance of the
                                         backupset class, subclient name, subclient id

        """
        self._disk_option = {
            'Original': 0,
            'Thick Lazy Zero': 1,
            'Thin': 2,
            'Thick Eager Zero': 3
        }

        self._transport_mode = {
            'Auto': 0,
            'SAN': 1,
            'Hot Add': 2,
            'NBD': 5,
            'NBD SSL': 4
        }
        super(VMWareVirtualServerSubclient, self).__init__(
            backupset_object, subclient_name, subclient_id)
        self.diskExtension = [".vmdk"]



    def full_vm_restore_in_place(
            self,
            vm_to_restore=None,
            overwrite=True,
            power_on=True,
            copy_precedence=0,
            disk_option='Original',
            transport_mode='Auto',
            proxy_client=None):
        """Restores the FULL Virtual machine specified in the input list
            to the location same as the actual location of the VM in VCenter.

            Args:
                vm_to_restore         (list)        --  provide the VM name to
                                                        restore
                                                        default: None

                overwrite             (bool)        --  overwrite the existing VM
                                                        default: True

                power_on              (bool)        --  power on the  restored VM
                                                        default: True

                copy_precedence       (int)         --  copy precedence value
                                                        default: 0

                disk_option           (basestring)  --  disk provisioning for the
                                                        restored vm
                                                        Options for input are: 'Original',
                                                        'Thick Lazy Zero', 'Thin', 'Thick Eager Zero'
                                                        default: Original

                transport_mode        (basestring)  --  transport mode to be used for
                                                        the restore.
                                                        Options for input are: 'Auto', 'SAN', 'Hot Add',
                                                        'NBD', 'NBD SSL'
                                                        default: Auto

                proxy_client          (basestring)  --  proxy client to be used for restore
                                                        default: proxy added in subclient

            Returns:
                object - instance of the Job class for this restore job

            Raises:
                SDKException:
                    if inputs are not of correct type as per definition

                    if failed to initialize job

                    if response is empty

                    if response is not success

        """
        vm_names, vm_ids = self._get_vm_ids_and_names_dict_from_browse()
        restore_option = {}

        # check input parameters are correct
        if bool(restore_option):
            if not isinstance(vm_to_restore, basestring):
                raise SDKException('Subclient', '101')

        disk_option_value = self._disk_option[disk_option]
        transport_mode_value = self._transport_mode[transport_mode]

        if copy_precedence:
            restore_option['copy_precedence_applicable'] = True

        if proxy_client is not None:
            restore_option['client'] = proxy_client

        # set attr for all the option in restore xml from user inputs
        self._set_restore_inputs(
            restore_option,
            vm_to_restore=self._set_vm_to_restore(vm_to_restore),
            in_place=True,
            esx_server_name="",
            volume_level_restore=1,
            unconditional_overwrite=overwrite,
            power_on=power_on,
            disk_option=disk_option_value,
            transport_mode=transport_mode_value,
            copy_preecedence=copy_precedence
        )

        request_json = self._prepare_fullvm_restore_json(restore_option)
        return self._process_restore_response(request_json)

    def full_vm_restore_out_of_place(
            self,
            vm_to_restore={},
            vcenter_client=None,
            esx_host=None,
            datastore=None,
            overwrite=True,
            power_on=True,
            copy_precedence=0,
            disk_option='Original',
            transport_mode='Auto',
            proxy_client=None
    ):
        """Restores the FULL Virtual machine specified in the input list
            to the provided vcenter client along with the ESX and the datastores.
            If the provided client name is none then it restores the Full Virtual
            Machine to the source client and corresponding ESX and datastore.

            Args:
                vm_to_restore          (dict)  --  dict containing the VM name(s) to restore as
                                                   keys and the new VM name(s) as their values.
                                                   Input empty string for default VM name for
                                                   restored VM.
                                                    default: {}

                vcenter_client    (basestring) -- name of the vcenter client
                                                  where the VM should be
                                                    restored.

                esx_host          (basestring) -- destination esx host
                                                    restores to the source VM
                                                    esx if this value is not
                                                    specified

                datastore         (basestring) -- datastore where the
                                                  restored VM should be located
                                                  restores to the source VM
                                                  datastore if this value is
                                                  not specified

                overwrite         (bool)       -- overwrite the existing VM
                                                  default: True

                power_on          (bool)       -- power on the  restored VM
                                                  default: True

                copy_precedence   (int)        -- copy precedence value
                                                  default: 0

                disk_option       (basestring) -- disk provisioning for the
                                                  restored vm
                                                  Options for input are: 'Original',
                                                  'Thick Lazy Zero', 'Thin', 'Thick Eager Zero'
                                                  default: Original

                transport_mode    (basestring) -- transport mode to be used for
                                                  the restore.
                                                  Options for input are: 'Auto', 'SAN', 'Hot Add',
                                                  'NBD', 'NBD SSL'
                                                  default: Auto

                proxy_client      (basestring) -- destination proxy client



            Returns:
                object - instance of the Job class for this restore job

            Raises:
                SDKException:
                    if inputs are not of correct type as per definition

                    if failed to initialize job

                    if response is empty

                    if response is not success

        """

        vm_names, vm_ids = self._get_vm_ids_and_names_dict_from_browse()
        restore_option = {}

        # check mandatory input parameters are correct
        if not isinstance(vm_to_restore, dict):
                raise SDKException('Subclient', '101')

        client = self._commcell_object.clients.get(vcenter_client)
        agent = client.agents.get('Virtual Server')
        instancekeys = next(iter(agent.instances._instances))
        instance = agent.instances.get(instancekeys)
        esx_server_name = instance.server_host_name[0]

        disk_option_value = self._disk_option[disk_option]
        transport_mode_value = self._transport_mode[transport_mode]

        if copy_precedence:
            restore_option['copy_precedence_applicable'] = True

        # populating proxy client. It assumes the proxy controller added in instance
        # properties if not specified
        if proxy_client is not None:
            restore_option['client'] = proxy_client

        vm_list = None
        if vm_to_restore:
            vm_list = list(vm_to_restore.keys())

        self._set_restore_inputs(
            restore_option,
            in_place=False,
            vcenter_client=vcenter_client,
            datastore=datastore,
            esx_host=esx_host,
            esx_server_name=esx_server_name,
            esx_server='',
            unconditional_overwrite=overwrite,
            power_on=power_on,
            vm_to_restore=self._set_vm_to_restore(vm_list),
            disk_option=disk_option_value,
            transport_mode=transport_mode_value,
            copy_precedence=copy_precedence,
            volume_level_restore=1,
            source_item=[]
        )

        new_name_dict = {}
        for _each_vm_to_restore in restore_option['vm_to_restore']:
            # Setting the new name for the restored VM.
            # If new_name is not given, it restores the VM with same name the with prefix 'Delete'
            new_name = vm_to_restore.get(_each_vm_to_restore, None)
            if not new_name:
                new_name = "Delete" + _each_vm_to_restore
            new_name_dict[_each_vm_to_restore] = new_name

        restore_option["restore_new_name"] = new_name_dict

        request_json = self._prepare_fullvm_restore_json(restore_option)
        return self._process_restore_response(request_json)

    def disk_restore(self,
                     vm_name,
                     destination_path,
                     disk_name=None,
                     proxy_client=None,
                     copy_precedence=0,
                     convert_to=None):
        """Restores the disk specified in the input paths list to the same location

            Args:
                vm_name             (basestring)   -- Name of the VM added in subclient content
                                                      whose  disk is selected for restore

                destination_path        (basestring)   -- Staging (destination) path to restore the
                                                      disk.

                disk_name           (list)         -- name of the disk which has to be restored
                                                      (only vmdk files permitted - enter full name
                                                      of the disk)
                                                      default: None

                proxy_client        (basestring)   -- Destination proxy client to be used
                                                      default: None

                copy_precedence     (int)          -- SP copy precedence from which browse has to
                                                      be performed

                convert_to          (basestring)   -- disk format for the restored disk(applicable
                                                      only when the vmdk disk  is selected for
                                                      restore). Allowed values are VHDX or VHD
                                                      default: None
            Returns:
                object - instance of the Job class for this restore job

            Raises:
                SDKException:
                    if inputs are not passed in proper expected format

                    if response is empty

                    if response is not success
        """

        vm_names, vm_ids = self._get_vm_ids_and_names_dict_from_browse()
        _disk_restore_option = {}

        disk_extn = '.vmdk'
        if not disk_name:
            disk_name = []
        else:
            disk_extn = self._get_disk_extension(disk_name)

        # check if inputs are correct
        if not (isinstance(vm_name, basestring) and
                isinstance(disk_name, list) and
                isinstance(destination_path, basestring) and
                disk_extn == '.vmdk'):
            raise SDKException('Subclient', '101')

        if convert_to is not None:
            convert_to = convert_to.lower()
            if convert_to not in ['vhdx', 'vhd']:
                raise SDKException('Subclient', '101')

        if copy_precedence:
            _disk_restore_option['copy_precedence_applicable'] = True

        # fetching all disks from the vm
        disk_list, disk_info_dict = self.disk_level_browse(
            "\\" + vm_ids[vm_name])

        if not disk_name:   # if disk names are not provided, restore all vmdk disks
            for each_disk_path in disk_list:
                disk_name.append(each_disk_path.split('\\')[-1])

        else:   # else, check if the given VM has a disk with the list of disks in disk_name.
            for each_disk in disk_name:
                each_disk_path = "\\" + str(vm_name) + "\\" + each_disk
                if each_disk_path not in disk_list:
                    raise SDKException('Subclient', '111')

        # if conversion option is given
        if convert_to is not None:
            dest_disk_dict = {
                'VHD_DYNAMIC': 13,
                'VHDX_DYNAMIC': 21
            }
            vol_restore, dest_disk = self._get_conversion_disk_Type('vmdk', convert_to)
            _disk_restore_option["destination_disktype"] = dest_disk_dict[dest_disk]
            _disk_restore_option["volume_level_restore"] = 4
        else:
            _disk_restore_option["volume_level_restore"] = 3

        _disk_restore_option["destination_vendor"] = \
            self._backupset_object._instance_object._vendor_id

        if proxy_client is not None:
            _disk_restore_option['client'] = proxy_client
        else:
            _disk_restore_option['client'] = self._backupset_object._instance_object.co_ordinator

        # set Source item List
        src_item_list = []
        for each_disk in disk_name:
            src_item_list.append("\\" + vm_ids[vm_name] + "\\" + each_disk.split("\\")[-1])

        _disk_restore_option['paths'] = src_item_list

        self._set_restore_inputs(
            _disk_restore_option,
            in_place=False,
            copy_precedence=copy_precedence,
            destination_path=destination_path,
            paths=src_item_list
        )

        request_json = self._prepare_disk_restore_json(_disk_restore_option)
        return self._process_restore_response(request_json)
