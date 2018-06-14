# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for operating on a UserMailbox Subclient.

UsermailboxSubclient is the only class defined in this file.

UsermailboxSubclient:   Derived class from ExchangeMailboxSubclient Base class, representing a
                            UserMailbox subclient, and to perform operations on that subclient

UsermailboxSubclient:

    _get_subclient_properties()         --  gets the properties of UserMailbox Subclient

    _get_subclient_properties_json()    --  gets the properties JSON of UserMailbox Subclient

    users()                             --  creates users association for subclient

    Databases()                         --  creates Db association for  the subclient

    Adgroups()                          --  creates Adgroup association for subclient

    restore_in_place()                  --  runs in-place restore for the subclient

"""


from __future__ import unicode_literals

from past.builtins import basestring

from ...exception import SDKException

from ..exchsubclient import ExchangeSubclient


class UsermailboxSubclient(ExchangeSubclient):
    """Derived class from ExchangeSubclient Base class.

        This represents a usermailbox subclient,
        and can perform discover and restore operations on only that subclient.

    """

    def __init__(self, backupset_object, subclient_name, subclient_id=None):
        """Initialize the Instance object for the given UserMailbox Subclient.

            Args:
                backupset_object    (object)    --  instance of the backupset class

                subclient_name      (str)       --  subclient name

                subclient_id        (int)       --  subclient id

        """
        super(UsermailboxSubclient, self).__init__(backupset_object, subclient_name, subclient_id)

        self._instance_object = backupset_object._instance_object
        self._client_object = self._instance_object._agent_object._client_object
        self._SET_EMAIL_POLICY_ASSOCIATIONS = self._commcell_object._services[
            'SET_EMAIL_POLICY_ASSOCIATIONS']

        self.refresh()

    def _get_discover_users(self):
        """Gets the discovered users from the Subclient .

            Returns:
                list    -   list of discovered users associated with the subclient

        """
        self._DISCOVERY = self._commcell_object._services['EMAIL_DISCOVERY'] % (
            int(self._backupset_object.backupset_id), 'User'
        )

        flag, response = self._commcell_object._cvpysdk_object.make_request('GET', self._DISCOVERY)

        if flag:
            discover_content = response.json()
            if 'discoverInfo' in discover_content.keys():

                if 'mailBoxes' in discover_content['discoverInfo']:
                    self._discover_users = discover_content['discoverInfo']['mailBoxes']

                return self._discover_users

        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def _get_discover_database(self):
        """Gets the discovered databases from the Subclient .

            Returns:
                list    -   list of discovered databases associated with the subclient

        """
        self._DISCOVERY = self._commcell_object._services['EMAIL_DISCOVERY'] % (
            int(self._backupset_object.backupset_id), 'Database'
        )

        flag, response = self._commcell_object._cvpysdk_object.make_request('GET', self._DISCOVERY)

        if flag:
            discover_content = response.json()
            if 'discoverInfo' in discover_content.keys():
                if 'databases' in discover_content['discoverInfo']:
                    discover_content = discover_content['discoverInfo']['databases']
                return discover_content

        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def _get_discover_adgroups(self):
        """Gets the discovered adgroups from the Subclient .

            Returns:
                list    -   list of discovered adgroups associated with the subclient

        """
        self._DISCOVERY = self._commcell_object._services['EMAIL_DISCOVERY'] % (
            int(self._backupset_object.backupset_id), 'AD Group'
        )

        flag, response = self._commcell_object._cvpysdk_object.make_request('GET', self._DISCOVERY)

        if flag:
            discover_content = response.json()
            if 'discoverInfo' in discover_content.keys():

                if 'adGroups' in discover_content['discoverInfo']:
                    discover_content = discover_content['discoverInfo']['adGroups']

                return discover_content

        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def _get_user_assocaitions(self):
        """Gets the appropriate users associations from the Subclient.

            Returns:
                list    -   list of users associated with the subclient

        """
        users = []

        self._EMAIL_POLICY_ASSOCIATIONS = self._commcell_object._services[
            'GET_EMAIL_POLICY_ASSOCIATIONS'] % (self.subclient_id, 'User')

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'GET', self._EMAIL_POLICY_ASSOCIATIONS
        )

        if flag:
            subclient_content = response.json()

            if 'associations' in subclient_content:
                children = subclient_content['associations']

                for child in children:
                    archive_policy = None
                    cleanup_policy = None
                    retention_policy = None
                    display_name = str(child['userMailBoxInfo']['displayName'])
                    alias_name = str(child['userMailBoxInfo']['aliasName'])
                    smtp_address = str(child['userMailBoxInfo']['smtpAdrress'])
                    database_name = str(child['userMailBoxInfo']['databaseName'])
                    exchange_server = str(child['userMailBoxInfo']['exchangeServer'])
                    user_guid = str(child['userMailBoxInfo']['user']['userGUID'])
                    is_auto_discover_user = str(child['userMailBoxInfo']['isAutoDiscoveredUser'])

                    for policy in child['policies']['emailPolicies']:
                        if policy['detail']['emailPolicy']['emailPolicyType'] == 1:
                            archive_policy = str(policy['policyEntity']['policyName'])
                        elif policy['detail']['emailPolicy']['emailPolicyType'] == 2:
                            cleanup_policy = str(policy['policyEntity']['policyName'])
                        elif policy['detail']['emailPolicy']['emailPolicyType'] == 3:
                            retention_policy = str(policy['policyEntity']['policyName'])

                    temp_dict = {
                        'display_name': display_name,
                        'alias_name': alias_name,
                        'smtp_address': smtp_address,
                        'database_name': database_name,
                        'exchange_server': exchange_server,
                        'user_guid': user_guid,
                        'is_auto_discover_user': is_auto_discover_user,
                        'archive_policy': archive_policy,
                        'cleanup_policy': cleanup_policy,
                        'retention_policy': retention_policy
                    }

                    users.append(temp_dict)

        return users

    def _get_database_associations(self):
        """Gets the appropriate database association from the Subclient.

            Returns:
                list    -   list of database associated with the subclient

        """
        databases = []

        self._EMAIL_POLICY_ASSOCIATIONS = self._commcell_object._services[
            'GET_EMAIL_POLICY_ASSOCIATIONS'] % (self.subclient_id, 'Database')

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'GET', self._EMAIL_POLICY_ASSOCIATIONS
        )

        if flag:
            subclient_content = response.json()

            if 'associations' in subclient_content:
                children = subclient_content['associations']

                for child in children:
                    database_name = str(child['databaseInfo']['databaseName'])
                    exchange_server = str(child['databaseInfo']['exchangeServer'])
                    archive_policy = None
                    cleanup_policy = None
                    retention_policy = None
                    is_auto_discover_user = str(child['additionalOptions']['enableAutoDiscovery'])

                    for policy in child['policies']['emailPolicies']:
                        if policy['detail']['emailPolicy']['emailPolicyType'] == 1:
                            archive_policy = str(policy['policyEntity']['policyName'])
                        elif policy['detail']['emailPolicy']['emailPolicyType'] == 2:
                            cleanup_policy = str(policy['policyEntity']['policyName'])
                        elif policy['detail']['emailPolicy']['emailPolicyType'] == 3:
                            retention_policy = str(policy['policyEntity']['policyName'])

                    temp_dict = {
                        'database_name': database_name,
                        'exchange_server': exchange_server,
                        'is_auto_discover_user': is_auto_discover_user,
                        'archive_policy': archive_policy,
                        'cleanup_policy': cleanup_policy,
                        'retention_policy': retention_policy
                    }

                    databases.append(temp_dict)

        return databases

    def _get_adgroup_assocaitions(self):
        """Gets the appropriate adgroup assocaitions from the Subclient.

            Returns:
                list    -   list of adgroups associated with the subclient

        """
        adgroups = []

        self._EMAIL_POLICY_ASSOCIATIONS = self._commcell_object._services[
            'GET_EMAIL_POLICY_ASSOCIATIONS'] % (self.subclient_id, 'AD Group')

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'GET', self._EMAIL_POLICY_ASSOCIATIONS
        )

        if flag:
            subclient_content = response.json()

            if 'associations' in subclient_content:
                children = subclient_content['associations']

                for child in children:
                    archive_policy = None
                    cleanup_policy = None
                    retention_policy = None
                    adgroup_name = str(child['adGroupsInfo']['adGroupName'])
                    is_auto_discover_user = str(child['additionalOptions']['enableAutoDiscovery'])

                    for policy in child['policies']['emailPolicies']:
                        if policy['detail']['emailPolicy']['emailPolicyType'] == 1:
                            archive_policy = str(policy['policyEntity']['policyName'])
                        elif policy['detail']['emailPolicy']['emailPolicyType'] == 2:
                            cleanup_policy = str(policy['policyEntity']['policyName'])
                        elif policy['detail']['emailPolicy']['emailPolicyType'] == 3:
                            retention_policy = str(policy['policyEntity']['policyName'])

                    temp_dict = {
                        'adgroup_name': adgroup_name,
                        'is_auto_discover_user': is_auto_discover_user,
                        'archive_policy': archive_policy,
                        'cleanup_policy': cleanup_policy,
                        'retention_policy': retention_policy
                    }

                    adgroups.append(temp_dict)

        return adgroups

    @property
    def discover_users(self):
        """"Returns the list of discovered users for the UserMailbox subclient."""
        return self._discover_users

    @property
    def discover_databases(self):
        """Returns the list of discovered databases for the UserMailbox subclient."""
        return self._discover_databases

    @property
    def discover_adgroups(self):
        """Returns the list of discovered AD groups for the UserMailbox subclient."""
        return self._discover_adgroups

    @property
    def users(self):
        """Returns the list of users associated with UserMailbox subclient."""
        return self._users

    @property
    def databases(self):
        """Returns the list of databases associated with the UserMailbox subclient."""
        return self._databases

    @property
    def adgroups(self):
        """Returns the list of AD groups associated with the UserMailbox subclient."""
        return self._adgroups

    def set_user_assocaition(self, subclient_content):
        """Create User assocaition for UserMailboxSubclient.

            Args:
                subclient_content   (dict)  --  dict of the Users to add to the subclient

                    subclient_content = {

                        'mailboxNames' : ["AutoCi2"],,

                        'is_auto_discover_user' : True,

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                    }

        """
        users = []

        if not isinstance(subclient_content, dict):
            raise SDKException('Subclient', '101')

        from ...policies.configuration_policies import ConfigurationPolicy

        if not (isinstance(subclient_content[
                'archive_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content[
                    'cleanup_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content[
                    'retention_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content['mailboxNames'], list) and
                isinstance(subclient_content['is_auto_discover_user'], bool)):
            raise SDKException('Subclient', '101')

        if isinstance(subclient_content['archive_policy'], ConfigurationPolicy):
            archive_policy = subclient_content['archive_policy']
        elif isinstance(subclient_content['archive_policy'], basestring):
            archive_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['archive_policy'])

        if isinstance(subclient_content['cleanup_policy'], ConfigurationPolicy):
            cleanup_policy = subclient_content['cleanup_policy']
        elif isinstance(subclient_content['cleanup_policy'], basestring):
            cleanup_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['cleanup_policy'])

        if isinstance(subclient_content['retention_policy'], ConfigurationPolicy):
            retention_policy = subclient_content['retention_policy']
        elif isinstance(subclient_content['retention_policy'], basestring):
            retention_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['retention_policy'])

        try:
            discover_users = self.discover_users

            for mailbox_item in subclient_content['mailboxNames']:

                for mb_item in discover_users:

                    if mailbox_item.lower() == mb_item['aliasName'].lower():
                        mailbox_dict = {
                            'smtpAdrress': mb_item['smtpAdrress'],
                            'aliasName': mb_item['aliasName'],
                            'mailBoxType': mb_item['mailBoxType'],
                            'displayName': mb_item['displayName'],
                            'exchangeServer': mb_item['exchangeServer'],
                            'isAutoDiscoveredUser': mb_item['isAutoDiscoveredUser'],
                            "associated": False,
                            'databaseName': mb_item['databaseName'],
                            'user': {
                                '_type_': 13,
                                'userGUID': mb_item['user']['userGUID']
                            }
                        }
                        users.append(mailbox_dict)

        except KeyError as err:
            raise SDKException('Subclient', '102', '{} not given in content'.format(err))

        associations_json = {
            "emailAssociation": {
                "advanceOptions": {},
                "subclientEntity": self._subClientEntity,
                "emailDiscoverinfo": {
                    "discoverByType": 1,
                    "mailBoxes": users
                },
                "policies": {
                    "emailPolicies": [
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 1
                                }
                            },
                            "policyEntity": {
                                "policyId": int(archive_policy.configuration_policy_id),
                                "policyName": archive_policy.configuration_policy_name
                            }

                        },
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 2
                                }
                            },
                            "policyEntity": {
                                "policyId": int(cleanup_policy._configuration_policy_id),
                                "policyName": cleanup_policy._configuration_policy_name
                            }
                        },
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 3
                                }
                            },
                            "policyEntity": {
                                "policyId": int(retention_policy._configuration_policy_id),
                                "policyName": retention_policy._configuration_policy_name
                            }
                        }
                    ]
                }
            }
        }

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._SET_EMAIL_POLICY_ASSOCIATIONS, associations_json
        )

        if flag:
            try:
                if response.json():
                    if response.json()['resp']['errorCode'] != 0:
                        error_message = response.json()['errorMessage']
                        output_string = 'Failed to create user assocaition\nError: "{0}"'
                        raise SDKException(
                            'Exchange Mailbox', '102', output_string.format(error_message)
                        )
                    else:
                        self.refresh()
            except ValueError:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def set_database_assocaition(self, subclient_content):
        """Create Database assocaition for UserMailboxSubclient.

            Args:
                subclient_content   (dict)  --  dict of the databases to add to the subclient

                    subclient_content = {

                        'databaseNames' : ["SGDB-1"],

                        'is_auto_discover_user' : True,

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy',
                    }
        """
        databases = []

        if not isinstance(subclient_content, dict):
            raise SDKException('Subclient', '101')

        from ...policies.configuration_policies import ConfigurationPolicy

        if not (isinstance(subclient_content[
                'archive_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content[
                    'cleanup_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content[
                    'retention_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content['databaseNames'], list) and
                isinstance(subclient_content['is_auto_discover_user'], bool)):
            raise SDKException('Subclient', '101')

        if isinstance(subclient_content['archive_policy'], ConfigurationPolicy):
            archive_policy = subclient_content['archive_policy']
        elif isinstance(subclient_content['archive_policy'], basestring):
            archive_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['archive_policy'])

        if isinstance(subclient_content['cleanup_policy'], ConfigurationPolicy):
            cleanup_policy = subclient_content['cleanup_policy']
        elif isinstance(subclient_content['cleanup_policy'], basestring):
            cleanup_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['cleanup_policy'])

        if isinstance(subclient_content['retention_policy'], ConfigurationPolicy):
            retention_policy = subclient_content['retention_policy']
        elif isinstance(subclient_content['retention_policy'], basestring):
            retention_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['retention_policy'])

        try:
            discover_databases = self.discover_databases

            for database_item in subclient_content['databaseNames']:

                for db_item in discover_databases:

                    if database_item.lower() == db_item['databaseName'].lower():
                        database_dict = {
                            'exchangeServer': db_item['exchangeServer'],
                            "associated": False,
                            'databaseName': db_item['databaseName'],
                        }
                        databases.append(database_dict)

        except KeyError as err:
            raise SDKException('Subclient', '102', '{} not given in content'.format(err))

        associations_json = {
            "emailAssociation": {
                "advanceOptions": {
                    "enableAutoDiscovery": True,
                },
                "subclientEntity": self._subClientEntity,
                "emailDiscoverinfo": {
                    "discoverByType": 2,
                    "databases": databases
                },
                "policies": {
                    "emailPolicies": [
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 1
                                }
                            },
                            "policyEntity": {
                                "policyId": int(archive_policy.configuration_policy_id),
                                "policyName": archive_policy.configuration_policy_name
                            }

                        },
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 2
                                }
                            },
                            "policyEntity": {
                                "policyId": int(cleanup_policy.configuration_policy_id),
                                "policyName": cleanup_policy.configuration_policy_name
                            }
                        },
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 3
                                }
                            },
                            "policyEntity": {
                                "policyId": int(retention_policy.configuration_policy_id),
                                "policyName": retention_policy.configuration_policy_name
                            }
                        }
                    ]
                }
            }
        }

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._SET_EMAIL_POLICY_ASSOCIATIONS, associations_json
        )

        if flag:
            try:
                if response.json():
                    if response.json()['resp']['errorCode'] != 0:
                        error_message = response.json()['errorMessage']
                        output_string = 'Failed to create Database assocaition\nError: "{0}"'
                        raise SDKException(
                            'Subclient', '102', output_string.format(error_message)
                        )
                    else:
                        self.refresh()
            except ValueError:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def set_adgroup_associations(self, subclient_content):
        """Create Ad groups assocaition for UserMailboxSubclient.

            Args:
                subclient_content   (dict)  --  dict of the adgroups to add to the subclient

                    subclient_content = {

                        'adGroupNames' : ["_Man5_Man5_"],

                        'is_auto_discover_user' : True,

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy',
                    }

        """
        adgroups = []

        if not isinstance(subclient_content, dict):
            raise SDKException('Subclient', '101')

        from ...policies.configuration_policies import ConfigurationPolicy

        if not (isinstance(subclient_content[
                'archive_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content[
                    'cleanup_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content[
                    'retention_policy'], (ConfigurationPolicy, basestring)) and
                isinstance(subclient_content['adGroupNames'], list) and
                isinstance(subclient_content['is_auto_discover_user'], bool)):
            raise SDKException('Subclient', '101')

        if isinstance(subclient_content['archive_policy'], ConfigurationPolicy):
            archive_policy = subclient_content['archive_policy']
        elif isinstance(subclient_content['archive_policy'], basestring):
            archive_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['archive_policy'])

        if isinstance(subclient_content['cleanup_policy'], ConfigurationPolicy):
            cleanup_policy = subclient_content['cleanup_policy']
        elif isinstance(subclient_content['cleanup_policy'], basestring):
            cleanup_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['cleanup_policy'])

        if isinstance(subclient_content['retention_policy'], ConfigurationPolicy):
            retention_policy = subclient_content['retention_policy']
        elif isinstance(subclient_content['retention_policy'], basestring):
            retention_policy = ConfigurationPolicy(
                self._commcell_object, subclient_content['retention_policy'])

        try:
            discover_adgroups = self.discover_adgroups

            for adgroup_item in subclient_content['adGroupNames']:

                for ad_item in discover_adgroups:

                    if adgroup_item.lower() == ad_item['adGroupName'].lower():
                        adgroup_dict = {
                            "associated": False,
                            'adGroupName': ad_item['adGroupName'],
                        }
                        adgroups.append(adgroup_dict)

        except KeyError as err:
            raise SDKException('Subclient', '102', '{} not given in content'.format(err))

        associations_json = {
            "emailAssociation": {
                "advanceOptions": {
                    "enableAutoDiscovery": True,
                },
                "subclientEntity": self._subClientEntity,
                "emailDiscoverinfo": {
                    "discoverByType": 3,
                    "adGroups": adgroups
                },
                "policies": {
                    "emailPolicies": [
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 1
                                }
                            },
                            "policyEntity": {
                                "policyId": int(archive_policy.configuration_policy_id),
                                "policyName": archive_policy._configuration_policy_name
                            }

                        },
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 2
                                }
                            },
                            "policyEntity": {
                                "policyId": int(cleanup_policy.configuration_policy_id),
                                "policyName": cleanup_policy.configuration_policy_name
                            }
                        },
                        {
                            "policyType": 1,
                            "flags": 0,
                            "agentType": {
                                "appTypeId": 137
                            },
                            "detail": {
                                "emailPolicy": {
                                    "emailPolicyType": 3
                                }
                            },
                            "policyEntity": {
                                "policyId": int(retention_policy.configuration_policy_id),
                                "policyName": retention_policy.configuration_policy_name
                            }
                        }
                    ]
                }
            }
        }

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._SET_EMAIL_POLICY_ASSOCIATIONS, associations_json
        )

        if flag:
            try:
                if response.json():
                    if response.json()['resp']['errorCode'] != 0:
                        error_message = response.json()['errorMessage']
                        output_string = 'Failed to create Adgroup assocaition\nError: "{0}"'
                        raise SDKException(
                            'Subclient', '102', output_string.format(error_message)
                        )
                    else:
                        self.refresh()
            except ValueError:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def delete_user_assocaition(self, subclient_content):
        """delete User assocaition for UserMailboxSubclient.

            Args:
                subclient_content   (dict)  --  dict of the Users to add to the subclient

                    subclient_content = {

                        'mailboxNames' : ["AutoCi2"],

                        'is_auto_discover_user' : True,

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                    }

        """
        users = []

        if not isinstance(subclient_content, dict):
            raise SDKException('Subclient', '101')

        if not (isinstance(subclient_content['mailboxNames'], list)):
            raise SDKException('Subclient', '101')

        try:
            discover_users = self.discover_users

            for mailbox_item in subclient_content['mailboxNames']:

                for mb_item in discover_users:

                    if mailbox_item.lower() == mb_item['aliasName'].lower():
                        mailbox_dict = {
                            'smtpAdrress': mb_item['smtpAdrress'],
                            'aliasName': mb_item['aliasName'],
                            'mailBoxType': mb_item['mailBoxType'],
                            'displayName': mb_item['displayName'],
                            'exchangeServer': mb_item['exchangeServer'],
                            'isAutoDiscoveredUser': mb_item['isAutoDiscoveredUser'],
                            "associated": False,
                            'databaseName': mb_item['databaseName'],
                            'user': {
                                '_type_': 13,
                                'userGUID': mb_item['user']['userGUID']
                            }
                        }
                        users.append(mailbox_dict)

        except KeyError as err:
            raise SDKException('Subclient', '102', '{} not given in content'.format(err))

        associations_json = {
            "emailAssociation": {
                "emailStatus": 1,
                "advanceOptions": {},
                "subclientEntity": self._subClientEntity,
                "emailDiscoverinfo": {
                    "discoverByType": 1,
                    "mailBoxes": users
                },

            }
        }

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', self._SET_EMAIL_POLICY_ASSOCIATIONS, associations_json
        )

        if flag:
            try:
                if response.json():
                    if response.json()['resp']['errorCode'] != 0:
                        error_message = response.json()['errorMessage']
                        output_string = 'Failed to create user assocaition\nError: "{0}"'
                        raise SDKException(
                            'Exchange Mailbox', '102', output_string.format(error_message)
                        )
                    else:
                        self.refresh()
            except ValueError:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def refresh(self):
        """Refresh the User Mailbox Subclient."""
        self._get_subclient_properties()
        self._discover_users = self._get_discover_users()
        self._discover_databases = self._get_discover_database()
        self._discover_adgroups = self._get_discover_adgroups()
        self._users = self._get_user_assocaitions()
        self._databases = self._get_database_associations()
        self._adgroups = self._get_adgroup_assocaitions()
