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
import random
import socket

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from AutomationUtils import logger, constants
from AutomationUtils.machine import Machine
from Application.SQL.sqlhelper import SQLHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Hyper-V SQL AppAware Basic with NO Existing SQL Instance"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        self.log = logger.get_log()

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            subcontent = []
            tcdir = None

            self.log.info(
                "-------------------Initialize helper objects------------------------------------"
                )
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                                                        auto_client, self.agent, self.instance)
            # auto_instance.FBRMA = "fbrhv"
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            # """

            self.log.info("--------------------SQL Discovery----------------------------------------------"
                )

            for vm in auto_subclient.vm_list:

                self.log.info("starting SQL discovery")

                self.log.info("reverting snap if exist")
                auto_subclient.hvobj.VMs[vm].revert_snap()
                try:
                    auto_commcell.commcell.clients.delete(vm)

                except Exception as e:
                    self.log.info("The Instance is already cleared so just proceeding {0}".format(e))

                auto_subclient.hvobj.VMs[vm].update_vm_info("All", True)
                sqluser = "{0}\\{1}".format(vm, auto_subclient.hvobj.VMs[vm].user_name)
                sqlpass = auto_subclient.hvobj.VMs[vm].password
                sqlmachine = Machine(vm, username=sqluser, password=sqlpass)
                sqlhelper = SQLHelper(self, vm, vm, sqluser, sqlpass)

                #"""
                ransum = ""
                for i in range(1, 7):
                    ransum = ransum + random.choice("abcdefghijklmnopqrstuvwxyz")
                    dbname = ransum

                sqldump_file1 = "before_backup_full.txt"
                sqldump_file2 = "after_restore.txt"
                _drive = list(auto_subclient.hvobj.VMs[vm].drive_list.keys())[0]
                testdata_path = "{0}:\\DumpData".format(_drive)
                tcdir = os.path.normpath(os.path.join(testdata_path + '-' + ransum))

                noofdbs = 5
                nooffilegroupsforeachdb = 3
                nooffilesforeachfilegroup = 4
                nooftablesforeachfilegroup = 10
                noofrowsforeachtable = 50
                randomization = 100

                self.log.info("Started executing {0} testcase".format(self.id))
                if not sqlmachine.create_directory(tcdir):
                    raise Exception("Failed to create staging directory. ")


                for i in range(1, noofdbs + 1):
                    db = dbname + repr(i)
                    subcontent.append(db)

                # perform database check if exists, if so, drop it first.

                if sqlhelper.dbinit.check_database(dbname):
                    if not sqlhelper.dbinit.drop_databases(dbname):
                        raise Exception("Unable to drop the database")

                """
                # create databases
                self.log.info("*" * 10 + " Creating database [{0}] ".format(dbname) + "*" * 10)
                if not sqlhelper.dbinit.db_new_create(dbname, noofdbs, nooffilegroupsforeachdb,
                                                           nooffilesforeachfilegroup, nooftablesforeachfilegroup,
                                                           noofrowsforeachtable):
                    raise Exception("Failed to create databases.")

                # get table shuffled list
                returnstring, list1, list2, list3 = sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                    randomization, noofdbs, nooffilegroupsforeachdb, nooftablesforeachfilegroup)
                if not returnstring:
                    raise Exception("Error in while generating the random number.")

                # write the original database to file for comparison
                controller_machine = Machine(socket.getfqdn(), auto_commcell.commcell)
                controller_machine.create_directory(tcdir)
                if not sqlhelper.dbvalidate.dump_db_to_file(os.path.join(tcdir, sqldump_file1),
                                                                 dbname, list1, list2, list3, 'FULL'):
                    raise Exception("Failed to write database to file.")
                
                #"""

            self.log.info(
                "----------------------------------------Backup-----------------------------------"
                )
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.Application_aware = True
            auto_subclient.backup(backup_options)

            #"""
            self.log.info(
                "---------------------------------------- VSA FULL VM out of Place restores------------"
                )
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            vm_restore_options.unconditional_overwrite = True
            auto_subclient.virtual_machine_restore(vm_restore_options)

            # """

            self.log.info(
                "---------------------------------------- Run SQL Restore and Validate it ------------"
            )

            # run restore in place job
            client = auto_commcell.commcell.clients.get(vm)
            agent = client.agents.get('SQL Server')
            _instance_keys = next(iter(agent.instances._instances))
            instance = agent.instances.get(_instance_keys)
            subclient = instance.subclients.get("default")
            self.instance = instance
            self.subclient = subclient

            sqlhelper_client = SQLHelper(self, client.client_name, instance.instance_name, sqluser, sqlpass)

            self.log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            if not sqlhelper_client.sql_restore(subclient.content):
                raise Exception("Restore was not successful!")

            # write the restored database to file for comparison
            if not sqlhelper_client.dbvalidate.dump_db_to_file(os.path.join(tcdir, sqldump_file2),
                                                             dbname, list1, list2, list3, 'FULL'):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            self.log.info("*" * 10 + " Validating content " + "*" * 10)
            if not sqlhelper_client.dbvalidate.db_compare(os.path.join(tcdir, sqldump_file1),
                                                        os.path.join(tcdir, sqldump_file2)):
                raise Exception("Failed to compare both files.")

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if not tcdir:
                if controller_machine.check_directory_exists(tcdir):
                    controller_machine.remove_directory(tcdir)
