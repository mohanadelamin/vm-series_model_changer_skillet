#!/usr/bin/env python
"""
vSphere Python SDK program for shutting down VMs
"""
from __future__ import print_function

from pyVim.connect import SmartConnect, Disconnect
from pyVim.task import WaitForTask
from pyVmomi import vim, vmodl
from pandevice.base import PanDevice
from pandevice.errors import PanDeviceError

import argparse
import atexit
import getpass
import ssl
import time


def GetArgs():
    """
    Supports the command-line arguments listed below.
    """

    parser = argparse.ArgumentParser(description='Process args for shutting down a Virtual Machine')
    parser.add_argument('--host', required=True, action='store', help='Remote ESXi host or vCenter to connect to')
    parser.add_argument('--port', type=int, default=443, action='store', help='Port to connect on')
    parser.add_argument('--user', required=True, action='store', help='User name to use when connecting to host')
    parser.add_argument('--password', required=False, action='store', help='Password to use when connecting to host')
    parser.add_argument('--vmname', required=True, action='store', help='Names of the Virtual Machines to shutdown')
    parser.add_argument('--model', required=True, action='store', help='Target VM-Series Model')
    parser.add_argument('--pan_host', required=True, action='store', help='PAN-OS device IP or FQDN')
    parser.add_argument('--pan_user', required=True, action='store', help='PAN-OS device username')
    parser.add_argument('--pan_pass', required=True, action='store', help='PAN-OS device password')
    parser.add_argument('--api_key', required=True, action='store', help='Support portal API Key')
    parser.add_argument('--auth_code', required=True, action='store', help='New device model Auth_code')

    args = parser.parse_args()
    return args


def get_service_instance(host,user,password,port,context):
    try:
        service_instance = SmartConnect(host=host,
                                                user=user,
                                                pwd=password,
                                                port=int(port),
                                                sslContext=context)

        atexit.register(Disconnect, service_instance)

        if not service_instance:
            print("Could not connect to the specified host using specified "
                  "username and password")
            return -1
        else:
            return service_instance

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0


def get_vm(service_instance,vm):
    try:
        print("Searching for VM %s in the environment." % vmobj.name)
        content = service_instance.RetrieveContent()
        # Search for all VMs
        objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.VirtualMachine],
                                                          True)
        vmList = objview.view
        objview.Destroy()

        for vmobj in vmList:
            if vmobj.name == vm:
                print("VM %s Found." % vmobj.name)
                return vmobj

        print("VM %s Not Found." % vm)
        return 0

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0


def shutdown_vm(vmobj):
    try:
        print("Shutting down VM: %s" % vmobj.name)
        task = vmobj.PowerOff()
        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            time.sleep(1)

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0


def poweron_vm(vmobj):
    try:
        print("Powering on VM: %s" % vmobj.name)
        task = vmobj.PowerOn()
        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            time.sleep(1)

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0


def change_vcpu(vm, vcpu_nu):
    vcpu_nu = int(vcpu_nu)
    cspec = vim.vm.ConfigSpec()
    cspec.numCPUs = vcpu_nu
    cspec.numCoresPerSocket = 1
    WaitForTask(vm.Reconfigure(cspec))
    print("number of vCPU changed to %s" %vcpu_nu)


def change_memory(vm, mem_size):
    mem_size = int(mem_size)
    cspec = vim.vm.ConfigSpec()
    cspec.memoryMB = mem_size
    WaitForTask(vm.Reconfigure(cspec))
    print("Memory size changed to %s" % mem_size)


def wait_for_panos(device, timeout):
    while time.time() < timeout:
        try:
            element_response = device.op(cmd="show jobs all")
        except PanDeviceError as msg:
            print("PAN-OS is not ready trying again!")
            time.sleep(5)
            pass
        else:
            jobs = element_response.findall('.//job')
            if check_jobs(jobs):
                print("PAN-OS is ready!")
                return True
    return False


def check_jobs(jobs):
    for j in jobs:
        status = j.find('.//status')
        if status is None or status.text != 'FIN':
            return False

    return True


def apply_api_key(device, api_key):
    try:
        device.op(cmd='<request><license><api-key><set><key>%s</key></set></api-key></license></request>' % api_key, cmd_xml=False)
        print("API Key applied")
    except PanDeviceError as msg:
        print(msg)
    return True


def deactivate_license(device):
    try:
        device.op(cmd='<request><license><deactivate><VM-Capacity><mode>auto</mode></VM-Capacity></deactivate></license></request>', cmd_xml=False)
        print("License deactivated!")
        # Give license API 10 seconds to finish before moving forward.
        time.sleep(15)
    except PanDeviceError as msg:
        print(msg)
    return


def activate_license(device, auth_code):
    try:
        device.op(cmd='<request><license><fetch><auth-code>%s</auth-code></fetch></license></request>' % auth_code, cmd_xml=False)
        print("License activated!")
        # Give license API 10 seconds to finish before moving forward.
        time.sleep(15)
    except PanDeviceError as msg:
        pass
    return


def main():
    """
   Simple command-line program for shutting down virtual machines on a system.
   """

    args = GetArgs()
    if args.password:
      password = args.password
    else:
      password = getpass.getpass(prompt='Enter password for host %s and user %s: ' % (args.host,args.user))

    context = ssl._create_unverified_context()

    host = args.host
    user = args.user
    password = args.password
    port = int(args.port)
    vm = args.vmname

    # Set # of CPU cores and memory based on the model.
    if args.model == "50":
        vcpu = 2
        memory = 5632
    elif args.model == "100":
        vcpu = 2
        memory = 6656
    elif args.model == "300":
        vcpu = 4
        memory = 9216
    elif args.model == "500":
        vcpu = 8
        memory = 16384
    elif args.model == "700":
        vcpu = 16
        memory = 57344

    # PAN-OS info:
    pan_hostname = args.pan_host
    pan_username = args.pan_user
    pan_password = args.pan_pass
    auth_code = args.auth_code
    api_key = args.api_key

    service_instance = get_service_instance(host, user, password, port, context)

    vmobj = get_vm(service_instance, vm)

    if vmobj:
        # Create PAN-OS device am make sure connection can be created. Wait for 5 minutes
        timeout = time.time() + 60 * 5  # 5 min from now
        ready = False
        while time.time() < timeout:
            try:
                device = PanDevice.create_from_device(pan_hostname, api_username=pan_username, api_password=pan_password)
            except PanDeviceError as msg:
                print("PAN-OS is not ready trying again!")
                time.sleep(5)
                pass
            else:
                print("PAN-OS device connection created!")
                ready = True
                break

        if ready:
            # Make sure PAN-OS is ready to accept commands. wait for 5 minutes
            timeout = time.time() + 60 * 5
            if wait_for_panos(device, timeout):
                # De active the current license.
                apply_api_key(device, api_key)
                deactivate_license(device)
                shutdown_vm(vmobj)
                change_vcpu(vmobj,vcpu)
                change_memory(vmobj,memory)
                poweron_vm(vmobj)
                timeout = time.time() + 60 * 5
                # Make sure PAN-OS is ready to accept commands. wait for 5 minutes
                if wait_for_panos(device, timeout):
                    activate_license(device, auth_code)
                    print("Model upgraded to %s successfully!" % args.model)
        else:
            exit(1)


# Start program
if __name__ == "__main__":
    main()
