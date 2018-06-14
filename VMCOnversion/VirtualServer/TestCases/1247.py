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
        self.name = "VSA Hyper-V Full Backup and Restore Cases"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))

            log.info(
                "-------------------Initialize helper objects------------------------------------"
                )
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                                                        auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            # """
            log.info(
                "----------------------------------------Backup-----------------------------------"
                )
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options)

            # """
            # """
            log.info(
                "----------------------------------------FULL VM out of Place restores------------"
                )
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            vm_restore_options.unconditional_overwrite = True
            auto_subclient.virtual_machine_restore(vm_restore_options)

            # """

            difference = list(set(auto_subclient.source_obj.disk_list) - set(auto_subclient.restore_obj.disk_list))
            if difference:
                raise Exception("Disk Level Filtering failed")

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
