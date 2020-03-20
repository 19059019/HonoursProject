import os
import sys
import json

COMMANDS = {
    "createvm": "VBoxManage createvm --name {} --ostype {} --register",
    "modifyvm": "VBoxManage modifyvm {} --cpus {} --memory {} --vram {}",
    "createhdd": "VBoxManage createmedium disk --filename {} --size {} --variant Standard",
    "createSATA": "VBoxManage storagectl {} --name SATAController --add sata --bootable on",
    "attachSATA": "VBoxManage storageattach {} --storagectl SATAController --port 0 --device 0 --type hdd --medium {}",
    "createISO": "VBoxManage storagectl {} --name IDEController --add ide",
    "attachISO": "VBoxManage storageattach {} --storagectl IDEController --port 0  --device 0 --type dvddrive --medium {}",
    "sharedfolder": "VBoxManage sharedfolder add {} --name sharedFolder --hostpath {} --automount",
    "startvm": "VBoxManage startvm {}",
}


def gen_vm(setup_file_name="setup.json"):
    """Sets up and starts a vm according to the inserted setup.json"""

    print("Building VM from {}".format(setup_file_name))
    with open(setup_file_name) as json_data:
        data = json.loads(json_data.read())
        vm_name = data["Title"]
        vm_properties = data["VMProperties"]
        try:
            vmpath = vm_properties["vmpath"]
            path_to_vdi = f"{vmpath}{vm_name}.vdi"
            command = COMMANDS["createvm"].format(vm_name, vm_properties["ostype"])
            os.system(f"{command}")
            command = COMMANDS["modifyvm"].format(
                vm_name,
                vm_properties["cpus"],
                vm_properties["memory"],
                vm_properties["vram"],
            )
            os.system(f"{command}")
            command = COMMANDS["createhdd"].format(path_to_vdi, "10240")
            os.system(f"{command}")
            command = COMMANDS["createSATA"].format(vm_name)
            os.system(f"{command}")
            command = COMMANDS["attachSATA"].format(vm_name, path_to_vdi)
            os.system(f"{command}")
            command = COMMANDS["createISO"].format(vm_name)
            os.system(f"{command}")
            command = COMMANDS["attachISO"].format(vm_name,vm_properties["isopath"])
            os.system(f"{command}")
            if (vm_properties["sharedfolder"]["include"] == "true"):
                command = COMMANDS["sharedFolder"].format(vm_name, vm_properties["sharedfolder"]["path"])
                os.system(f"{command}")
        except:
            print("Issues Encountered")
            return

if __name__ == "__main__":
    args = sys.argv
    gen_vm(args[1])

