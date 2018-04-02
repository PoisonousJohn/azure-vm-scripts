#/bin/python3

"""Script makes an image out of specified VM."""
import uuid
import sys
import argparse
import subprocess

def checkAzCLI():
    status, result = subprocess.getstatusoutput("az")
    return status == 0

def createVMImage(resourceGroup, imageName, vmName):
    return subprocess.getstatusoutput("az image create -g %(resourceGroup)s -n %(name)s --source %(vmName)s" % {'resourceGroup' : resourceGroup, 'name': imageName, 'vmName' : vmName})

def generalizeVM(resourceGroup, name):
    return subprocess.getstatusoutput("az vm generalize -g %(resourceGroup)s -n %(name)s" % {'resourceGroup' : resourceGroup, 'name': name})

def queryVmParam(resourceGroup, name, queryParam):
    status, output = subprocess.getstatusoutput("az vm show -d --query '%(queryParam)s' -g %(resourceGroup)s -n %(name)s" % {'resourceGroup' : resourceGroup, 'name': name, 'queryParam': queryParam})
    return (status, output.strip().replace('"', ''))

def deallocateVM(resourceGroup, name):
    return subprocess.getstatusoutput("az vm deallocate --resource-group %(resourceGroup)s --name %(name)s" % {'resourceGroup' : resourceGroup, 'name': name})

def main():

    if not checkAzCLI():
        print("Azure CLI required for this script. Please install it: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        return 1

    parser = argparse.ArgumentParser('Usage: template-vm')
    parser.add_argument("-g", "--resourceGroup", help="Resource group name where VM can be found", required=True)
    parser.add_argument("-n", "--vmName", help="The name of VM to be templated", required=True)
    parsedArgs = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()

    print("Checking VM state")
    status, output = queryVmParam(parsedArgs.resourceGroup, parsedArgs.vmName, 'powerState')
    if status != 0:
        print("Failed to check vm state: %s" % (output))
        sys.exit(1)
    if output != 'VM deallocated':
        print("Deallocating VM")
        status, output = deallocateVM(parsedArgs.resourceGroup, parsedArgs.vmName)
        if status != 0:
            print("VM Deallocation failed: %s" % (output))
            sys.exit(1)
        print("VM Deallocated")
    else:
        print("VM is already deallocated")

    print("Generalizing VM")
    status, output = generalizeVM(parsedArgs.resourceGroup, parsedArgs.vmName)
    if status != 0:
        print("Failed to generalize vm: %s" % (output))
        sys.exit(1)

    print("Creating image")
    imageName = "%s-image-%s" % (parsedArgs.vmName, str(uuid.uuid4()).replace('-', '')[:5])
    status, output = createVMImage(parsedArgs.resourceGroup, imageName, parsedArgs.vmName)

    if status != 0:
        print("Failed to create image: %s" % (output))
        sys.exit(1)

    print("Created image %s" % imageName)

if __name__ == "__main__":
    main()