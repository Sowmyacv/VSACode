# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
CommonUtils:   Provides test common commcell related operations.

CommonUtils:

    __init__()                  -- initialize instance of CommonUtils class

    __repr__()                  --  Representation string for the instance of the
                                    CommonUtils class for specific test case

    check_client_readiness()    -- performs check readiness on the list of clients

    get_subclient()             -- Gets default subclient object for a given commcell
                                    client, agent, backupset.

    restart_services()          -- restarts services on the list of clients

    subclient_backup()          -- Executes backup on any subclient object and waits for job
                                    completion.

    subclient_restore_in_place()
                                -- Restores the files/folders specified in the input paths list
                                    to the same location.

    subclient_restore_out_of_place()
                                -- Restores the files/folders specified in the input paths list
                                    to the input client, at the specified destination location.

    subclient_backup_and_restore()
                                -- Executes backup on a subclient, and restores data out of place

    subclient_restore_from_job()
                                -- Initiates restore for data backed up in a given job
                                    and performs the applicable verifications.

    osc_backup_and_restore()    -- Validates backup works fine from osc schedule for incremental
                                     backup for devices and out of place restore works.

    aux_copy()                  -- Executes aux copy on a specific storage policy copy and waits
                                    for job completion.

    data_aging()                -- Executes data aging for a specific storage policy copy and
                                    waits for job completion.

    compare_file_metadata()     -- Compares the meta data of source path with destination path
                                    and checks if they are same.

    cleanup_jobs()              -- Kills all the jobs in the job list self.job_list,
                                    if the jobs are not completed already.

    modify_additional_settings() -- Updates GXGlobalParam table based on name and value

get_backup_copy_job_id()        -- Method to fetch backup copy job ID given the snap job ID for
                                        snap subclient

backup_validation()             --  Method to validate backup jobs with application size
                                        and data size


"""
import inspect
import ntpath
from datetime import datetime

from cvpysdk import job
from cvpysdk.client import Client
from cvpysdk.commcell import Commcell
from cvpysdk.subclient import Subclient
from cvpysdk.backupset import Backupset
from cvpysdk.policies.storage_policies import StoragePolicy
from cvpysdk.job import JobController

from AutomationUtils import constants
from AutomationUtils import logger
from AutomationUtils import database_helper
from AutomationUtils.options_selector import OptionsSelector

from Server.JobManager.jobmanager_helper import JobManager


class CommonUtils(object):
    """Class to perform common commcell operations."""

    def __init__(self, init_object):
        ''' Initialize instance of CommonUtils class

        Args:
        init_object : Should be either the commcell or the testcase object'''

        # Pre-initialized attributes applicable for all instances of the class
        self._init_object = init_object
        if isinstance(init_object, Commcell):
            self._testcase = None
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        self.log = logger.get_log()
        self.job_list = []
        self._utility = OptionsSelector(self._commcell)
        self.job_manager = JobManager(commcell=self._commcell)
        self.job_controller = JobController(self._commcell)

    def __repr__(self):
        """Representation string for the instance of the CommonUtils class."""
        return "CommonUtils class instance"

    def check_client_readiness(self, clients):
        """Performs check readiness on the list of clients


            Args:
                clients(list)  -- list of clients on which check readiness needs to be performed

            Example:

                ["auto", "v11-restapi"]

        """
        try:
            self.log.info("Performing check readiness on clients [{0}]".format(clients))

            for client in clients:
                _client_obj = self._commcell.clients.get(client)

                if _client_obj.is_ready:
                    self.log.info("Client {0} is ready".format(client))
                else:
                    raise Exception("Check readiness failed for client {0}".format(client))

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def get_subclient(self,
                      client=None,
                      agent='File System',
                      backupset='defaultBackupset',
                      subclient_name='default'):
        """" Gets subclient object for a given commcell client, agent, backupset

            Args:
                client_name    (str)    -- Client name
                                            default: Testcase initialized client

                agent          (str)    -- Client data agent name

                backupset      (str)    -- Agents backupset name

                subclient_name (str)    -- Subclient name

            Returns:
                (object)    -    Subclient object for the given client

            Raises:
                Exception
                    -    if failed to get the default subclient
        """
        try:
            if client is None and self._testcase is not None:
                client = self._testcase.client.client_name
            elif not isinstance(client, (Client, str)):
                raise Exception("Subclient object expected as argument")

            self.log.info("Getting subclient object for client [{0}], agent [{1}], backupset"
                          " [{2}]".format(client, agent, backupset))

            self._commcell.clients.refresh()
            client = self._commcell.clients.get(client)
            backupset = client.agents.get(agent).backupsets.get(backupset)
            subclient = backupset.subclients.get(subclient_name)

            self.log.info("Subclient object: [{0}]".format(subclient))

            return subclient

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def restart_services(self, clients):
        """Restarts services on the list of clients

        Args:
                clients(list)  -- list of clients on which services needs to be
                                    restarted

            Example:

                ["testproxy", "v11-restapi"]

        """
        try:
            for client in clients:
                _client_obj = self._commcell.clients.get(client)

                self.log.info("Restarting services on client {0}".format(client))

                _client_obj.restart_services()

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def subclient_backup(self,
                         subclient,
                         backup_type="Incremental",
                         wait=True,
                         target_subclient=None,
                         **kwargs):
        """Executes backup on any subclient object and waits for job completion.

            Args:
                subclient          (obj)   -- Instance of SDK Subclient class

                backup_type        (str)   -- Backup type:
                                                Full / Incremental / Differential / Synthetic_full
                                                default: Incremental

                wait               (bool)  -- If True, will wait for backup job to complete.
                                              If False, will return job object for the backup job
                                                  without waiting for job to finish.

                target_subclient   (str)   -- subclient target string where backup shall be
                                                executed.
                        e.g:
                        client1->file system->defaultinstancename->backupset_199->subclient_199
                        OR could be any custom string from user.

                **kwargs           (dict)  -- Key value pair for the various subclients type
                                                inputs, depending on the subclient iDA.
                                                scheduling options to be included for the task
                                                Please refer schedules.schedulePattern.
                                                createSchedule() doc for the types of Jsons

            Returns:
                (object)    - Job class instance for the backup job in case of immediate Job.
                              Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception if:

                    - is subclient object is not passed as an argument.

                    - failed during execution of module

            Example:
                - Executes full backup for subclient and **does not wait for job completion

                    job = subclient_backup(subclient_object, "full", False)

                - Executes incremental backup for subclient and waits for job completion

                    job = subclient_backup(subclient_object, "incremental")

                - Runs incremental backup for subclient
                    job = subclient_backup(subclient_object)
        """
        try:
            if subclient is None and self._testcase is not None:
                subclient = self._testcase.subclient
            elif not isinstance(subclient, Subclient):
                raise Exception("Subclient object expected as argument")

            if target_subclient is None:
                target_subclient = subclient.subclient_name

            if 'schedule_pattern' not in kwargs:
                self.log.info("Starting [{0}] backup for subclient [{1}]"
                              "".format(backup_type.upper(), target_subclient))
            else:
                self.log.info("Creating {0} Backup Schedule for subclient {1} with "
                              "pattern {2}".format(backup_type, subclient,
                                                   kwargs['schedule_pattern']))

            if not bool(kwargs):
                _obj = subclient.backup(backup_type)
            else:
                _obj = subclient.backup(backup_type, **kwargs)

            if 'schedule_pattern' not in kwargs:
                self.job_list.append(_obj.job_id)
                job_type = _obj.job_type if _obj.backup_level is None else _obj.backup_level

                self.log.info("Executed [{0}] backup job id [{1}]".format(job_type.upper(),
                                                                          str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)

            else:
                self.log.info("Successfully created Backup Schedule with Id {0}"
                              .format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def subclient_restore_in_place(self, paths, subclient=None, wait=True, **kwargs):
        """Restores the files/folders specified in the input paths list to the same location.

            Args:
                paths                 (list)       --  list of full paths
                                                        of files/folders to restore

                subclient             (obj)        --  subclient object of relevant SDK subclient
                                                        class.

                wait                  (bool)       -- If True, will wait for backup job to
                                                        complete.
                                                      If False, will return job object for the
                                                        backup job without waiting for job to
                                                        finish.

                **kwargs           (dict)  -- Key value pair for the various subclients type
                                                inputs for underlying restore_in_place module,
                                                depending on the subclient iDA. Schedule Pattern
                                                if schedule is needed
                                                Please refer schedules.schedulePattern.
                                                createSchedule() doc for the types of Jsons
            Returns:
                object - instance of the Job class for this restore job
                         Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception - Any error occurred while running restore
                            or restore didn't complete successfully.
        """

        try:

            # Use the current test case client as default
            if subclient is None and self._testcase is not None:
                subclient = self._testcase.subclient
            elif not isinstance(subclient, Subclient):
                raise Exception("subclient object expected as argument")

            if 'schedule_pattern' not in kwargs:
                self.log.info("Execute in place restore for subclient [{0}]"
                              "".format(subclient.subclient_name))
            else:
                self.log.info(
                    "Creating Restore In Place Schedule for subclient '{0}' with paths {1} "
                    "using schedule pattern {2}".format(subclient.subclient_name, paths,
                                                        kwargs['schedule_pattern']))

            _obj = subclient.restore_in_place(paths=paths, **kwargs)

            if 'schedule_pattern' not in kwargs:
                self.job_list.append(_obj.job_id)

                self.log.info("Executed in place restore with job id [{0}]".
                              format(str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)
            else:
                self.log.info("Successfully created In Place Restore Schedule with Id {0}"
                              .format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def subclient_restore_out_of_place(
            self, destination_path, paths, client=None, subclient=None, wait=True, **kwargs
    ):
        """Restores the files/folders specified in the input paths list to the input client,
            at the specified destination location.

            Args:
                client                (str/object) --  either the name or the instance of Client

                destination_path      (str)        --  full path of the restore location on client

                paths                 (list)       --  list of full paths of files/folders
                                                        to restore

                subclient             (obj)        --  subclient object of relevant SDK subclient
                                                        class.

                wait                  (bool)       -- If True, will wait for backup job to
                                                        complete.
                                                      If False, will return job object for the
                                                        backup job without waiting for job to
                                                        finish.

                **kwargs           (dict)  -- Key value pair for the various subclients type
                                                inputs for underlying restore_out_of_place module,
                                                depending on the subclient iDA.
                                                Schedule Pattern if schedule is needed
                                                Please refer schedules.schedulePattern.
                                                createSchedule() doc for the types of Jsons
            Returns:
                object - instance of the Job class for this restore job
                         Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception - Any error occurred while running restore or restore didn't
                                complete successfully.
        """
        try:

            # Use the current test case client as default
            if subclient is None and self._testcase is not None:
                subclient = self._testcase.subclient
            elif not isinstance(subclient, Subclient):
                raise Exception("subclient object expected as argument")

            # Use the current test case subclient as default
            if client is None and self._testcase is not None:
                client = self._testcase.client

            if 'schedule_pattern' not in kwargs:
                self.log.info("Executing out of place restore for subclient [{0}]"
                              "".format(subclient.subclient_name))

            else:
                self.log.info(
                    "Creating Restore Out of Place Schedule for subclient '{0}' with paths "
                    "{1} to client '{2}' using schedule pattern {3}"
                    .format(subclient.subclient_name, paths, client.client_name,
                            kwargs['schedule_pattern']))

            _obj = subclient.restore_out_of_place(
                client=client,
                destination_path=destination_path,
                paths=paths,
                **kwargs,
            )

            if 'schedule_pattern' not in kwargs:

                self.job_list.append(_obj.job_id)

                self.log.info("Executed out of place restore with job id [{0}]"
                              "".format(str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)

            else:
                self.log.info("Successfully created Out Of Place Restore Schedule with Id {0}"
                              .format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def subclient_backup_and_restore(self,
                                     client_name,
                                     subclient,
                                     backup_type='full',
                                     validate=True):
        """Executes backup on a subclient, and restores data out of place.
            Main purpose of this module is to test if backup and restore works on a client
            for given subclient.

            Args:
                client_name          (str)/(Machine object)
                                                 -- Client name

                subclient            (object)    -- subclient object
                                                        Default: default subclient

                backup_type          (str)       -- Backup type. Various types supported by
                                                        underlying SDK backup module.

                validate             (bool)      -- Validate source content and resotred content
                                                        metadata/contents/acl/xattr

            Raises:
                Exception if:

                    - failed during execution of module
        """
        try:
            machine_obj = self._utility.get_machine_object(client_name)
            old_content = subclient.content
            source_dir = self._utility.create_directory(machine_obj)

            self.log.info("Adding directory to subclient content: {0}".format(source_dir))

            subclient.content += [self._utility.create_test_data(machine_obj, source_dir)]

            backup_job = self.subclient_backup(subclient, backup_type)

            # Execute out of place restore and validate data post restore.
            self.subclient_restore_from_job(source_dir,
                                            job=backup_job,
                                            subclient=subclient,
                                            client=machine_obj,
                                            validate=validate)

            self.log.info("Setting subclient content to: {0}".format(old_content))

            subclient.content = old_content

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))
        finally:
            self._utility.remove_directory(machine_obj, source_dir)

    def subclient_restore_from_job(self,
                                   data_path,
                                   tmp_path=None,
                                   job=None,
                                   cleanup=True,
                                   subclient=None,
                                   client=None,
                                   validate=True,
                                   **kwargs):
        """ Initiates restore for data backed up in the given job
            and performs the applicable verifications

            Args:
                data_path (str)          -- Source data path

                tmp_path (str)           -- temporary path for restoring the data
                                                default: None
                                                If not provided, directory to restore will be
                                                created on client.

                job (obj)/(id)           -- instance of the job class whose data needs to be
                                                restored. Or the job id.
                                                default : None

                cleanup (bool)           -- to indicate if restored data
                                             should be cleaned up
                    default : True

                subclient (object)       -- Subclient object

                client (str)/(Machine object)
                                         -- Client name or corresponding machine object

                validate (bool)          -- If True will validate metadata for restored content
                                                default: True

                **kwargs (dict)          -- Key value pairs:
                                                supported :
                                                    dirtime (bool) - Whether to validate directory
                                                                        time stamps or not

                                                    applicable_os (str) - UNIX/WINDOWS

                                                    acls (bool) - Validate acls for files or not

                                                    xattr (bool) - Validate attributed for the
                                                                    file or not
            Returns:
                job object for the restore job.

            Raises:
                Exception
                - if any error occurred while running restore or during verification.
                - Meta data comparison failed
                - Checksum comparison failed
                - ACL comparison failed
                - XATTR comparison failed
        """
        try:

            if subclient is None and self._testcase is not None:
                subclient = self._testcase.subclient
            elif not isinstance(subclient, Subclient):
                raise Exception("subclient object expected as argument")

            # Use the current test case client as default
            if subclient is None and client is None and self._testcase is not None:
                subclient = self._testcase.subclient
                client = self._testcase.client
            elif not isinstance(subclient, Subclient):
                raise Exception("subclient object needs to be passed as argument.")

            machine_obj = self._utility.get_machine_object(client)
            client_name = machine_obj.machine_name

            log = self.log
            paths = [data_path]
            if tmp_path is None:
                tmp_path = self._utility.create_directory(machine_obj)
            data_path_leaf = ntpath.basename(data_path)
            dest_path = machine_obj.os_sep.join([tmp_path, data_path_leaf + "_restore"])

            restore_from_time = None
            restore_to_time = None
            if job is not None:
                if isinstance(job, (str, int)):
                    job = self._commcell.job_controller.get(job)
                restore_from_time = str(datetime.utcfromtimestamp(job.summary['jobStartTime']))
                restore_to_time = str(datetime.utcfromtimestamp(job.summary['jobEndTime']))

            log.info(
                """
                Starting restore with source:{1},
                destination:[{0}],
                from_time:[{2}],
                to_time:[{3}]
                """.format(
                    dest_path, str(paths), restore_from_time, restore_to_time
                )
            )

            # Clean up destination directory before starting restore
            self._utility.remove_directory(machine_obj, dest_path)
            _job = self.subclient_restore_out_of_place(dest_path,
                                                       paths,
                                                       client_name,
                                                       subclient,
                                                       from_time=restore_from_time,
                                                       to_time=restore_to_time)
            if not validate:
                return _job

            # Validation for restored content
            compare_source = data_path
            compare_destination = machine_obj.os_sep.join([dest_path, data_path_leaf])
            log.info("""Executing backed up content validation:
                        Source: [{0}], and
                        Destination [{1}]""".format(compare_source, compare_destination))

            result, diff_output = machine_obj.compare_meta_data(
                compare_source, compare_destination, dirtime=kwargs.get('dirtime', False)
            )

            log.info("Performing meta data comparison on source and destination")
            if not result:
                log.error("Meta data comparison failed")
                log.error("Diff output: \n{0}".format(diff_output))
                raise Exception("Meta data comparison failed")
            log.info("Meta data comparison successful")

            log.info("Performing checksum comparison on source and destination")
            result, diff_output = machine_obj.compare_checksum(compare_source, compare_destination)
            if not result:
                log.error("Checksum comparison failed")
                log.error("Diff output: \n{0}".format(diff_output))
                raise Exception("Checksum comparison failed")
            log.info("Checksum comparison successful")

            if kwargs.get('applicable_os') == 'UNIX':
                if kwargs.get('acls'):
                    log.info("Performing ACL comparison on source and destination")
                    result, diff_output = machine_obj.compare_acl(
                        compare_source, compare_destination
                    )
                    if not result:
                        log.error("ACL comparison failed")
                        log.error("Diff output: \n{0}".format(diff_output))
                        raise Exception("ACL comparison failed")
                    log.info("ACL comparison successful")

                if kwargs.get('xattr'):
                    log.info("Performing XATTR comparison on source and destination")
                    result, diff_output = machine_obj.compare_xattr(
                        compare_source, compare_destination
                    )
                    if not result:
                        log.error("XATTR comparison failed")
                        log.error("Diff output: \n{0}".format(diff_output))
                        raise Exception("XATTR comparison failed")
                    log.info("XATTR comparison successful")

            return _job
        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))
        finally:
            if cleanup:
                self._utility.remove_directory(machine_obj, dest_path)

    def backupset_restore_in_place(
            self, paths, backupset=None, wait=True, **kwargs):
        """Restores the files/folders specified in the input paths list to the input client,
            to the same location.

            Args:
                paths                 (list)       --  list of full paths of files/folders
                                                        to restore

                backupset             (obj)        --  backupset object of relevant SDK subclient
                                                        class.

                wait                  (bool)       -- If True, will wait for backup job to
                                                        complete.
                                                      If False, will return job object for the
                                                        backup job without waiting for job to
                                                        finish.

                **kwargs           (dict)  -- Key value pair for the various backupset type
                                                inputs for underlying restore_out_of_place module
            Returns:
                object - instance of the Job class for this restore job
                         Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception - Any error occurred while running restore or restore didn't
                                complete successfully.
        """
        try:

            # Use the current test case client as default
            if backupset is None and self._testcase is not None:
                backupset = self._testcase.backupset
            elif not isinstance(backupset, Backupset):
                raise Exception("Backupset object expected as argument")

            if 'schedule_pattern' not in kwargs:
                self.log.info("Executing out of place restore for backupset [{0}]"
                              "".format(backupset.backupset_name))
            else:
                self.log.info(
                    "Creating Restore In Place Schedule for subclient '{0}' with paths {1}"
                    "using schedule pattern {2}"
                    .format(backupset.backupset_name, paths,
                            kwargs['schedule_pattern']))

            _obj = backupset.restore_in_place(paths=paths, **kwargs)

            if 'schedule_pattern' not in kwargs:
                self.job_list.append(_obj.job_id)

                self.log.info("Executed in place restore with job id [{0}]"
                              "".format(str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)

            else:
                self.log.info("Successfully created In Place Restore Schedule with Id {0}"
                              .format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def backupset_restore_out_of_place(
            self, destination_path, paths, client=None, backupset=None, wait=True, **kwargs):
        """Restores the files/folders specified in the input paths list to the input client,
            at the specified destination location.

            Args:
                client                (str/object) --  either the name or the instance of Client

                destination_path      (str)        --  full path of the restore location on client

                paths                 (list)       --  list of full paths of files/folders
                                                        to restore

                backupset             (obj)        --  backupset object of relevant SDK subclient
                                                        class.

                wait                  (bool)       -- If True, will wait for backup job to
                                                        complete.
                                                      If False, will return job object for the
                                                        backup job without waiting for job to
                                                        finish.

                **kwargs           (dict)  -- Key value pair for the various backupset type
                                                inputs for underlying restore_out_of_place module
            Returns:
                object - instance of the Job class for this restore job
                         Schedule Object will be returned to perform
                                         tasks on created Schedule

            Raises:
                Exception - Any error occurred while running restore or restore didn't
                                complete successfully.
        """
        try:

            # Use the current test case client as default
            if backupset is None and self._testcase is not None:
                backupset = self._testcase.backupset
            elif not isinstance(backupset, Backupset):
                raise Exception("Backupset object expected as argument")

            # Use the current test case subclient as default
            if client is None and self._testcase is not None:
                client = self._testcase.client

            if 'schedule_pattern' not in kwargs:
                self.log.info("Executing out of place restore for backupset [{0}]"
                              "".format(backupset.backupset_name))

            else:
                self.log.info(
                    "Creating Restore Out of Place Schedule for subclient '{0}' with paths "
                    "{1} to client '{2}' using schedule pattern {3}"
                    .format(backupset.backupset_name, paths, client.client_name,
                            kwargs['schedule_pattern']))

            _obj = backupset.restore_out_of_place(
                client=client,
                destination_path=destination_path,
                paths=paths,
                **kwargs
            )

            if 'schedule_pattern' not in kwargs:

                self.job_list.append(_obj.job_id)

                self.log.info("Executed out of place restore with job id [{0}]"
                              "".format(str(_obj.job_id)))

                if wait:
                    self.job_manager.job = _obj
                    self.job_manager.wait_for_state('completed')
                    self.job_list.remove(_obj.job_id)

            else:
                self.log.info("Successfully created Out Of Place Restore Schedule with Id {0}"
                              .format(_obj.schedule_id))

            return _obj

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def osc_backup_and_restore(self, client, validate=True):
        """ Validates backup works fine from osc schedule for incremental backup for devices

            Args:
                client          (str)/(Machine object)       -- Client name or Machine object

            Raises:
                Exception if:

                    - failed during execution of module
        """
        try:
            machine_obj = self._utility.get_machine_object(client)
            client_name = machine_obj.machine_name

            # Wait for auto triggered backups
            self.job_manager.get_filtered_jobs(client_name, time_limit=5, retry_interval=5)

            # Add new content to default subclient of this client and check auto triggered
            # incremental backup
            subclient = self.get_subclient(client_name)
            source_dir = self._utility.create_directory(machine_obj)

            self.log.info("Adding directory to subclient content with: {0}".format(source_dir))

            subclient.content += [self._utility.create_test_data(machine_obj, source_dir)]
            jobs = self.job_manager.get_filtered_jobs(client_name, time_limit=5, retry_interval=5)

            # Execute out of place restore and validate data post restore.
            self.subclient_restore_from_job(source_dir,
                                            job=jobs[1][0],
                                            subclient=subclient,
                                            client=machine_obj,
                                            validate=validate)

            self.log.info("Successfully executed auto backup jobs and validated "
                          "out of place restore on client [{0}]".format(client_name))

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))
        finally:
            self._utility.remove_directory(machine_obj, source_dir)

    def aux_copy(self, storage_policy, sp_copy, media_agent, wait=True):
        """Executes aux copy on a specific storage policy copy and waits for job completion.

            Args:
                storage_policy    (obj/str)   -- storage policy name OR corresponding storage
                                                    policy SDK instance of class StoragePolicy

                sp_copy           (str)       -- name of the storage policy copy

                media_agent       (str)       -- name of the media agent

                wait              (bool)      -- If True, will wait for backup job to complete.

                                                  If False, will return job object for the job
                                                      without waiting for job to finish.

            Returns:
                job object        (object)    -- Job class instance for the aux copy job

            Raises:
                Exception if :

                    - storage_policy is neither the policy name nor SDK object

                    - failed during execution of module

            Example:
                - Executes aux copy for the storage policy sp01 and copy sp01_copy on media agent
                    ma01 and waits for job completion.

                job = aux_copy('sp01', 'sp01_copy', 'ma01')
        """
        try:

            # If storage policy name is passed as argument get it's object
            if isinstance(storage_policy, str):
                storage_policies = self._commcell.storage_policies
                storage_policy = storage_policies.get(storage_policy)
            elif not isinstance(storage_policy, StoragePolicy):
                raise Exception("storage_policy should either be policy name or SDK object")

            self.log.info("Starting aux copy for storage policy [{0}] copy [{1}]"
                          "".format(storage_policy.storage_policy_name, sp_copy))

            _job = storage_policy.run_aux_copy(sp_copy, media_agent)
            _jobid = str(_job.job_id)
            self.job_list.append(_jobid)

            self.log.info("Executed [{0}] aux copy job id [{1}]".format(_job.job_type, _jobid))

            if wait:
                self.job_manager.job = _job
                self.job_manager.wait_for_state('completed')
                self.job_list.remove(_jobid)

            return _job

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def data_aging(self, storage_policy, sp_copy, wait=True):
        """Executes data aging for a specific storage policy copy and waits for job completion.

            Args:
                storage_policy    (obj/str)   -- storage policy name OR corresponding storage
                                                    policy SDK instance of class StoragePolicy

                sp_copy           (str)       -- name of the storage policy copy

                wait              (bool)      -- If True, will wait for backup job to complete.

                                                  If False, will return job object for the job
                                                      without waiting for job to finish.

            Returns:
                job object        (object)    -- Job class instance for the data aging job.

            Raises:
                Exception if :

                    - failed during execution of module

            Example:
                - Executes data aging for the storage policy sp01 and copy sp01_copy and waits
                    for job completion

                job = aux_copy('sp01', 'sp01_copy')
        """
        try:

            # If storage policy object is passed as argument get policy name from object
            if isinstance(storage_policy, StoragePolicy):
                storage_policy = storage_policy.storage_policy_name

            self.log.info("Starting data aging job on commcell.")

            _job = self._commcell.run_data_aging(sp_copy, storage_policy)
            _jobid = str(_job.job_id)
            self.job_list.append(_jobid)

            self.log.info("Executed [{0}] data aging job id [{1}]".format(_job.job_type, _jobid))

            if wait:
                self.job_manager.job = _job
                self.job_manager.wait_for_state('completed')
                self.job_list.remove(_jobid)

            return _job

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def compare_file_metadata(self, client, source_path, destination_path, dirtime=True):
        """Compares the meta data of source path with destination path and checks if they are same

             Args:

                client              (str)/(Machine object)
                                            -- Client name on which source and destination paths
                                                exist. Or corresponding machine object for client.

                source_path         (str)   --  source path of the folder to compare

                destination_path    (str)   --  destination path of the folder to compare

                dirtime             (bool)  --  whether to get time stamp of all directories
                    default: False

            Returns:
                bool   -   Returns True if lists are same or returns False

            Raises:
                Exception:
                    if any error occurred while comparing the source and destination paths.
        """

        try:
            machine_obj = self._utility.get_machine_object(client)
            client = machine_obj.machine_name

            self.log.info("Client: [{0}], Source path [{1}]".format(client, source_path))
            self.log.info("Client: [{0}], Destination path [{1}]".format(client, destination_path))
            self.log.info("Comparing meta data for source and destination paths")

            response = machine_obj.compare_meta_data(source_path, destination_path, dirtime)
            if not response[0]:
                self.log.error("Differences found between source and destination")
                self.log.error("Diff list: [{0}]".format(response[1]))
                raise Exception("Metadata comparison failed")

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def cleanup_jobs(self):
        """ Kills all the jobs in the job list self.job_list, if the jobs are not completed
                already.

            self.job_list is populated with every call to the function in this module which
                executes a job.

                For example : aux_copy, data_aging, subclient_backup

            This module can be called as part of the testcase cleanup code in case the testcase
            ends abruptly in between leaving behind these running jobs which might interfere with
            other test cases execution.

            Args:
                None:

            Returns:
                None

            Raises:
                Exception if :

                    - failed during execution of module
        """
        try:
            for _job in self.job_list:
                if isinstance(_job, str):
                    _job = self._commcell.job_controller.get(_job)

                self.log.info("Job [{0}] status = [{1}]".format(str(_job.job_id), _job.status))

                if not _job.is_finished:
                    self.job_manager.job = _job
                    self.job_manager.modify_job('kill')

                del _job

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def modify_additional_settings(self, activity_name, activity_value):
        """ Updates GXGlobalParam table based on name and value

            Args:
                activity_name  (str)   --  Name to update in GXGlobalParam
                                                Ex:"JobsCompleteIfActivityDisabled",
                                                   "JMJobActivityLevelHighWaterMark"

                activity_value (str)  --   Value to update in GXGlobalParam
                                                Ex: "0 or 1",
                                                    "500"
            Returns:
                None

            Exception:
                failed to update parameters

        """
        try:
            self.log.info("Setting {0} to {1}".format(activity_name, activity_value))
            self.job_controller.modify_jobmanagement_options(activity_name, activity_value)
            self.log.info("Successfully! updated {0} activity on {1} with {2}".
                          format(activity_name, self._commcell.commserv_name, activity_value))
        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))


def get_backup_copy_job_id(commcell, subclient, snap_job_id):
    """Method to fetch inline backup copy job ID given the snap job ID for s nsap subclient
    Args:
        commcell            (object)    --  commcell object on which the operations are
                                                to be performed

        subclient           (object)    --  subclient object

        snap_job_id         (str)       --  snap backup job ID

    Returns:
        str                         -- returns string of backup copy job ID
    """
    log = logger.get_log()
    subclient_id = subclient.subclient_id
    log.info("Snap Job ID : {0}".format(snap_job_id))
    backup_copy_job_id = None
    query = """SELECT childJobId FROM JMJobWF WHERE processedJobId = {0}""".format(
        int(snap_job_id))
    csdb = database_helper.CommServDatabase(commcell)
    csdb.execute(query)
    job_list = csdb.fetch_one_row()
    backup_copy_job_id = job_list[0]
    return backup_copy_job_id


def backup_validation(commcell, jobid, backup_type):
    """
    Method to validate backup jobs with application size and data size
       Args:
            commcell    (object)     --     commcell object on which the operations are
                                                to be performed

            jobid     (str)         --     jobid which needs to be validated on backup completion

            backup_type     (str)    --     expected backup type from calling method

        Returns:
            (bool)     -     Returns true if the validation of backup type and size check suceeds

        Raises:
            Exception:

                if backup validation fails

                if response was not success

                if response received is empty

                if failed to get response
    """
    log = logger.get_log()
    status = False
    type_status = False
    size_status = False

    # Validating the backup type sent by user
    base_backup_level = constants.backup_level

    if base_backup_level(backup_type) not in base_backup_level:
        raise Exception(
            "Backup Type sent does not fall under available backup levels. "
            "Kindly check the spelling and case"
        )

    jobobj = job.Job(commcell, jobid)
    gui_backup_type = jobobj.backup_level
    log.info("Backup Type from GUI: [%s]", gui_backup_type)

    # Comparing the given backup type with actually ran backup type
    if str(gui_backup_type) != str(backup_type):
        log.info("Expected Backup Type is  " + str(backup_type) +
                 " Ran Backup Type  " + str(gui_backup_type) + "  for JobId : " + str(jobid))
    else:
        log.info("Expected Backup Type is " + str(backup_type) +
                 " Ran Backup Type " + str(gui_backup_type) + "  for JobId : " + str(jobid))
        type_status = True

    jobobj = job.Job(commcell, jobid)
    full_job_details = jobobj.details
    sub_dict = full_job_details['jobDetail']['detailInfo']
    data_size = sub_dict.get('compressedBytes')
    application_size = int(sub_dict.get('sizeOfApplication'))

    # Checking Application and Data size for data size validation during backup
    if application_size > 0:
        if data_size <= 0:
            log.info("Even though job was completed the transefered datasize is: [%s]", data_size)
        else:
            log.info(
                "Application Data size is: [%s]. \nData Written Size is: [%s] for Job Id: [%s]",
                application_size,
                data_size,
                jobid
            )
            size_status = True
    if type_status and size_status:
        status = True
        return status
    else:
        raise Exception("Backup Validation for Job Id : {0} failed.".format(jobobj.job_id))


def get_synthetic_full_job(subclient, backup_type):
    """
    This gets the synthetic full job if after incr or before incr
    Args:
        csdb:           cs DB object for the commcell
        subclient:   subcleint object of SDK
        backup_type:
                AFTER_SYNTH - if synthetic full is triggereged after Incremental
                BEFORE_SYNTH - if synthetic full is triggereged Before Incremental


    Returns:
        job - job object of synthetic full/incremental that triggered after synthetic full

    """

    if backup_type == "AFTER_SYNTH":
        backup_type_latest_running = "Incremental"
        backup_type_latest_finished = "Synthetic Full"

    else:
        backup_type_latest_running = "Synthetic Full"
        backup_type_latest_finished = "Incremental"

    latest_running_job = subclient.find_latest_job(include_finished=False)
    latest_completed_job = subclient.find_latest_job(include_active=False)

    if ((latest_running_job.backup_level == backup_type_latest_running) and
            (latest_completed_job.job_type == backup_type_latest_finished)):
        return latest_running_job

    else:
        raise Exception("Synthfull job did not start : {0} .".format(latest_running_job.job_id))