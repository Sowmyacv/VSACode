"""Service URLs for FUsion COmpute REST API operations.

SERVICES_DICT:  A python dictionary for holding all the API services endpoints.

get_services(web_service):  updates the SERVICES_DICT with the Fusion Compute API URL

"""


SERVICES_DICT_TEMPLATE = {
    'GET_VERSION': '{}/versions',
    'LOGIN': '{}/session',
    'GET_SITES': '{}/sites'
}

VM_SERVICES_DICT_TEMPLATE = {
    'GET_VMS': '{}/vms',
    'GET_DATASTORES': '{0}/datastores',
    'GET_HOSTS': '{0}/hosts'
}

VM_OPERATIONS_DICT_TEMPLATE = {
    'START_VM': '/action/start',
    'STOP_VM': '/action/stop',
    'RESTART_VM': '/action/reboot'
}


def get_vm_operation_services(vrm_service, vm_url):
    """
    get the VM services URL
    :param
        vrm_service  (str)   --  web service string for APIs
        site_url:      (str)URL for Sites from which VM url can be configured

    :return:
        dict    -   services dict consisting of all APIs
    """

    vm_op_services_dict = VM_OPERATIONS_DICT_TEMPLATE.copy()
    vm_site_url = 'http://{0}:7070/{1}'.format(vrm_service, vm_url)
    for service in vm_op_services_dict:
        vm_op_services_dict[service] = vm_op_services_dict[service].format(vm_site_url)

    return vm_op_services_dict


def get_vm_services(vrm_service, site_url):
    """
    get the VM services URL
    :param
        vrm_service  (str)   --  web service string for APIs
        site_url:      (str)URL for Sites from which VM url can be configured

    :return:
        dict    -   services dict consisting of all APIs
    """

    vm_services_dict = VM_SERVICES_DICT_TEMPLATE.copy()
    vm_site_url = 'http://{0}:7070/{1}'.format(vrm_service, site_url)
    for service in vm_services_dict:
        vm_services_dict[service] = vm_services_dict[service].format(vm_site_url)

    return vm_services_dict


def get_services(vrm_service):
    """Initializes the SERVICES DICT with the web service for APIs.

        Args:
            vrm_service     (str)   --  web service string for APIs

        Returns:
            dict    -   services dict consisting of all APIs
    """
    services_dict = SERVICES_DICT_TEMPLATE.copy()
    vrm_service_url = 'http://{0}:7070'.format(vrm_service)
    for service in services_dict:
        services_dict[service] = services_dict[service].format(vrm_service_url)

    return services_dict
