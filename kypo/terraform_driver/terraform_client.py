import os
import shutil
import subprocess
import json
from enum import Enum

from kypo.topology_definition.models import TopologyDefinition

from kypo.commons import KypoCloudClientBase, TopologyInstance, TransformationConfiguration
# Available cloud clients
from kypo.openstack_driver import KypoOpenStackClient

STACKS_DIR = '/var/tmp/kypo/terraform-stacks/'
TEMPLATE_FILE_NAME = 'deploy.tf'
TERRAFORM_STATE_FILE_NAME = 'terraform.tfstate'


class AvailableCloudLibraries(Enum):
    OPENSTACK = KypoOpenStackClient


class KypoTerraformClient:
    """
    Client used as an interface providing functions of this Terraform library
    """

    def __init__(self, cloud_client: AvailableCloudLibraries, trc: TransformationConfiguration,
                 stacks_dir: str = None, template_file_name: str = None, *args, **kwargs):
        self.cloud_client: KypoCloudClientBase = cloud_client.value(trc=trc, *args, **kwargs)
        self.stacks_dir = stacks_dir if stacks_dir else STACKS_DIR
        self.template_file_name = template_file_name if template_file_name else TEMPLATE_FILE_NAME
        self._create_directories(self.stacks_dir)
        self.trc = trc

    @staticmethod
    def _create_directories(dir_path: str) -> None:
        os.makedirs(dir_path, exist_ok=True)

    @staticmethod
    def _create_file(file_path: str, content: str) -> None:
        with open(file_path, 'w') as file:
            file.write(content)
            file.flush()

    @staticmethod
    def _remove_directory(dir_path: str) -> None:
        shutil.rmtree(dir_path)

    @staticmethod
    def _init_terraform(stack_dir: str) -> None:
        print('init of terraform', stack_dir)
        subprocess.run('terraform init', cwd=stack_dir, shell=True)

    def _get_stack_dir(self, stack_name: str) -> str:
        return os.path.join(self.stacks_dir, stack_name)

    # create_stack
    def create_stack(self, stack_name: str, topology_definition: TopologyDefinition,
                     key_pair_name_ssh: str, key_pair_name_cert: str = None, dry_run: bool = False,
                     *args, **kwargs):
        terraform_template = self.create_terraform_template(topology_definition,
                                                            key_pair_name_ssh=key_pair_name_ssh,
                                                            key_pair_name_cert=key_pair_name_cert,
                                                            resource_prefix=stack_name, *args,
                                                            **kwargs)
        stack_dir = self._get_stack_dir(stack_name)
        self._create_directories(stack_dir)
        self._create_file(os.path.join(stack_dir, self.template_file_name), terraform_template)
        self._init_terraform(stack_dir)
        command = subprocess.Popen(['terraform', 'apply', '-auto-approve'], cwd=stack_dir,
                                   stdout=subprocess.PIPE)

        while command.poll() is None:
            print(command.stdout.readline().rstrip().decode())

    def create_terraform_template(self, topology_definition: TopologyDefinition, *args, **kwargs):
        return self.cloud_client.create_terraform_template(topology_definition, *args, **kwargs)

    def delete_stack(self, stack_name):
        stack_dir = self._get_stack_dir(stack_name)
        command = subprocess.Popen(['terraform', 'destroy', '-auto-approve'], cwd=stack_dir,
                                   stdout=subprocess.PIPE)
        while command.poll() is None:
            print(command.stdout.readline().rstrip().decode())

        if command.returncode:
            raise Exception(f"Return code of destroy was {command.returncode}")

        self._remove_directory(stack_dir)

    def list_images(self):
        return self.cloud_client.list_images()

    def list_stacks(self):
        return os.listdir(self.stacks_dir)

    def get_stack_status(self, stack_name: str):
        pass  # TODO: not used by sandbox-service

    def get_topology_instance(self, topology_definition: TopologyDefinition) -> TopologyInstance:
        return TopologyInstance(topology_definition, self.trc)

    def get_enriched_topology_instance(self, stack_name: str,
                                       topology_definition: TopologyDefinition) -> TopologyInstance:
        topology_instance = self.get_topology_instance(topology_definition)
        topology_instance.name = stack_name

        list_or_resources = self.list_stack_resources(stack_name)
        resources_dict = {res['name']: res for res in list_or_resources}

        man_out_port_dict = resources_dict[f'{stack_name}-{self.trc.man_out_port}']
        topology_instance.ip = man_out_port_dict['instances'][0]['attributes']['all_fixed_ips'][0]

        for link in topology_instance.get_links():
            port_dict = resources_dict[f'{stack_name}-{link.name}']
            link.ip = port_dict['instances'][0]['attributes']['all_fixed_ips'][0]
            link.mac = port_dict['instances'][0]['attributes']['mac_address']

        return topology_instance

    def suspend_node(self, stack_name, node_name, *args, **kwargs):
        # get resource id and call nova
        pass

    def resume_node(self, stack_name, node_name, *args, **kwargs):
        # get resource id and call nova
        pass

    def reboot_node(self, stack_name, node_name, *args, **kwargs):
        # get resource id and call nova
        pass

    def get_node(self, stack_name, node_name, *args, **kwargs):
        # get resource id and call nova
        pass

    def get_console_url(self, stack_name, node_name, *args, **kwargs):
        # get resource id and call nova
        pass

    # list stack events
    def list_stack_events(self, stack_name, *args, **kwargs):
        pass

    def list_stack_resources(self, stack_name: str):
        stack_dir = self._get_stack_dir(stack_name)
        with open(os.path.join(stack_dir, TERRAFORM_STATE_FILE_NAME), 'r') as file:
            return list(filter(lambda res: res['mode'] == 'managed', json.load(file)['resources']))

    def create_keypair(self, name: str, public_key: str = None, key_type: str = 'ssh'):
        return self.cloud_client.create_keypair(name, public_key, key_type)

    def get_keypair(self, name: str):
        return self.cloud_client.get_keypair(name)

    def delete_keypair(self, name: str):
        return self.cloud_client.delete_keypair(name)

    def get_quota_set(self):
        return self.cloud_client.get_quota_set()  # TODO: create QuotaSet here

    def get_project_name(self):
        return self.cloud_client.get_project_name()

    # TODO: both hardware usage methods should be implemented in this project
    def validate_hardware_usage_of_stacks(self, topology_instance: TopologyInstance, count: int):
        return self.cloud_client.validate_hardware_usage_of_stacks(topology_instance, count)

    def get_hardware_usage(self, topology_instance: TopologyInstance):
        return self.cloud_client.get_hardware_usage(topology_instance)

    def get_project_limits(self, *args, **kwargs):
        return self.cloud_client.get_project_limits()
