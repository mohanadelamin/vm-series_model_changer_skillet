## Deploying Standalone VM-Series in vSphere ##
Skillet to upgrade or downgrade the VM-Series model in vSphere environment. for example moving from VM-50 to VM-100 or vice versa.
 
This skillet is using PANDevice Python framework as well as VMware vSphere API Python binding 
pyvmomi in order to interact with both vSphere infrastructure and PAN-OS to execute the scaling up or Down event. (For example moving from VM-50 to VM-100)
  

The skillet will execute the following tasks:
- Deactivate the current PAN-OS licenses.
- Power off the VM on vSphere.
- Change the vCPU and Memory allocation in order to match the target VM model.
- Power on the VM on vSphere.
- Activate the license for the new model.

## prerequisites ##

To run this skillet you will need
1. The license API key for you account (Can be found in the support portal under assets > License API Key).
2. Licensing Auth code for the target model. 


## Usage ##

1- Import this repo into your panhandler.

2- Run the skillet and fill the following fields and click submit (Make sure to add quotes if the value will contain space):
  - name: host
    description: vCenter IP or FQDN
  - name: user
    description: vCenter admin user name
  - name: password
    description: vCenter admin password
  - name: vmname
    description: VM-Series VM name in vCenter
  - name: pan_host
    description: VM-Series management IP or FQDN
  - name: pan_user
    description: VM-Series user name
  - name: pan_pass
    description: VM-Series user password
  - name: api_key
    description: Licensing API Key (From support portal)
  - name: model
    description: VM-Series target model.
  - name: auth_code
    description: VM-Series Licensing Authcode

3- Wait for the skillet to download the required Python modules (pyvmomi and pandevice).

4- Finally the skillet will provision the changes. 


## Support Policy ##

The code and templates in the repo are released under an as-is, best effort,
support policy. These scripts should be seen as community supported and
Palo Alto Networks will contribute our expertise as and when possible.
We do not provide technical support or help in using or troubleshooting the
components of the project through our normal support options such as
Palo Alto Networks support teams, or ASC (Authorized Support Centers)
partners and backline support options. The underlying product used
(the VM-Series firewall) by the scripts or templates are still supported,
but the support is only for the product functionality and not for help in
deploying or using the template or script itself. Unless explicitly tagged,
all projects or work posted in our GitHub repository
(at https://github.com/PaloAltoNetworks) or sites other than our official
Downloads page on https://support.paloaltonetworks.com are provided under