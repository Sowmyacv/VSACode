# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
File having backup_validation function for all backup jobs as common
"""
from enum import Enum
from AutomationUtils import constants
from cvpysdk import job
from AutomationUtils import logger


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
        backup_type_latest_running = "INCREMENTAL"
        backup_type_latest_finished = "SYNTHETIC_FULL"

    else:
        backup_type_latest_running = "SYNTHETIC_FULL"
        backup_type_latest_finished = "INCREMENTAL"

    latest_running_job = subclient.find_latest_job(include_finished=False)
    latest_completed_job = subclient.find_latest_job(include_active=False)

    if ((latest_running_job.job_type == backup_type_latest_running) and
            (latest_completed_job.job_type == backup_type_latest_finished)):
        return latest_running_job

    else:
        raise Exception("Synthfull job did not start : {0} .".format(latest_running_job.job_id))


def backup_validation(commcell, jobid, backup_type):
    """
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
        raise Exception("Backup Type sent does not fall under available backup levels. Kindly check the spelling and case")
    jobobj = job.Job(commcell, jobid)
    GUIbackupType = jobobj.backup_level
    log.info("Backup Type from GUI : {0}".format(GUIbackupType))

    # Comparing the given backup type with actually ran backup type 
    if str(GUIbackupType) != str(backup_type):
        log.info("Expected Backup Type is  " + str(backup_type) + " Ran Backup Type  " + str(GUIbackupType) +"  for JobId : " + str(jobid))
    else:
        log.info("Expected Backup Type is " + str(backup_type) + " Ran Backup Type " + str(GUIbackupType) +"  for JobId : " + str(jobid))
        type_status = True
    jobobj = job.Job(commcell, jobid)
    full_job_details = jobobj.details
    sub_dict = full_job_details['jobDetail']['detailInfo']
    dataSize = sub_dict.get('compressedBytes')
    applicationSize = int(sub_dict.get('sizeOfApplication'))

    # Checking Application and Data size for data size validation during backup
    if applicationSize > 0:
        if dataSize <= 0:
            log.info("Even though job was completed the transefered datasize is 0" + str(dataSize1))
        else:
            log.info("Application Data size is : " + str(applicationSize) +" Data Written Size is :" + str(dataSize) + " for jobId: " + str(jobid))
            size_status = True
    if type_status and size_status:
        status = True
        return status
    else:
        raise Exception("Backup Validation for Job Id : {0} failed.".format(jobobj.job_id))

