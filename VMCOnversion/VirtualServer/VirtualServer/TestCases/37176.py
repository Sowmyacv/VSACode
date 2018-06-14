# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import os

from AutomationUtils.cvtestcase import CVTestCase

from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper

from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Full Backup and Restore Cases"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))
            log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_instance.vm_user_name = self.tcinputs['VMUserName']
            auto_instance.vm_password = self.tcinputs['VMPassword']
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            log.info(
                "-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options)

            log.info(
                "-" * 25 + " Files restores " + "-" * 25)
            file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
            auto_subclient.guest_file_restore(file_restore_options)

            log.info(
                "-" * 25 + " Disk restores " + "-" * 25)
            disk_restore_options = OptionsHelper.DiskRestoreOptions(auto_subclient)
            #auto_subclient.disk_restore(disk_restore_options)

            log.info(
                "-" * 15 + " FULL VM out of Place restores " + "-" * 15)
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            #auto_subclient.disk_restore(vm_restore_options)

        except Exception as exp:
            log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
