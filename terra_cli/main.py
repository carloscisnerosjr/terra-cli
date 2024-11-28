import boto3
import click
import json
from pathlib import Path
from colorama import init, Fore, Back, Style
import questionary

# Initialize colorama
init(autoreset=True)

@click.group()
def cli():
    """TERRA CLI - Transform AWS Resources into Terraform with Style"""
    pass

def print_banner():
    banner = f"""
{Fore.CYAN}████████╗{Fore.BLUE}███████╗{Fore.MAGENTA}██████╗ {Fore.RED}██████╗  {Fore.YELLOW}█████╗     {Fore.GREEN}██████╗{Fore.CYAN}██╗     {Fore.BLUE}██╗
{Fore.CYAN}╚══██╔══╝{Fore.BLUE}██╔════╝{Fore.MAGENTA}██╔══██╗{Fore.RED}██╔══██╗{Fore.YELLOW}██╔══██╗    {Fore.GREEN}██╔════╝{Fore.CYAN}██║     {Fore.BLUE}██║
{Fore.CYAN}   ██║   {Fore.BLUE}█████╗  {Fore.MAGENTA}██████╔╝{Fore.RED}██████╔╝{Fore.YELLOW}███████║    {Fore.GREEN}██║     {Fore.CYAN}██║     {Fore.BLUE}██║
{Fore.CYAN}   ██║   {Fore.BLUE}██╔══╝  {Fore.MAGENTA}██╔══██╗{Fore.RED}██╔══██╗{Fore.YELLOW}██╔══██║    {Fore.GREEN}██║     {Fore.CYAN}██║     {Fore.BLUE}██║
{Fore.CYAN}   ██║   {Fore.BLUE}███████╗{Fore.MAGENTA}██║  ██║{Fore.RED}██║  ██║{Fore.YELLOW}██║  ██║    {Fore.GREEN}╚██████╗{Fore.CYAN}███████╗{Fore.BLUE}██║
{Fore.CYAN}   ╚═╝   {Fore.BLUE}╚══════╝{Fore.MAGENTA}╚═╝  ╚═╝{Fore.RED}╚═╝  ╚═╝{Fore.YELLOW}╚═╝  ╚═╝    {Fore.GREEN}╚═════╝{Fore.CYAN}╚══════╝{Fore.BLUE}╚═╝"""
    print(banner)
    print(f"\n{Fore.YELLOW}🌍 TERRA CLI - Your AWS Infrastructure, The Terraform Way 🌍{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Version 1.0.0 - Made with {Fore.RED}❤️{Style.RESET_ALL}")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════{Style.RESET_ALL}\n")

@cli.command()
@click.option('--region', default='us-east-1', help='AWS region to target')
@click.option('--output', default='terraform', help='Output directory for Terraform files')
@click.option('--profile', default='default', help='AWS profile to use')

def scan(region, output, profile):
    """Scan and import AWS resources into Terraform configuration"""
    print_banner()
    
    try:
        # Initialize AWS session with profile
        session = boto3.Session(profile_name=profile, region_name=region)
        
        # Create output directory if it doesn't exist
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Show interactive menu for service selection
        services = questionary.checkbox(
            'Select AWS services to import:',
            choices=[
                questionary.Choice('EC2 Instances', 'ec2'),
                questionary.Choice('EventBridge Rules', 'eventbridge'),
            ]
        ).ask()
        
        if not services:
            click.echo(f"{Fore.YELLOW}No services selected. Exiting...{Style.RESET_ALL}")
            return
        
        # Process selected services
        for service in services:
            if service == 'ec2':
                import_ec2_resources(session, output_dir)
            elif service == 'eventbridge':
                import_eventbridge_rules(session, output_dir)
        
        click.echo(f"\n{Fore.GREEN}✨ Import complete!{Style.RESET_ALL}")
        show_next_steps(output_dir)
        
    except Exception as e:
        click.echo(f"{Fore.RED}💥 Error: {str(e)}{Style.RESET_ALL}", err=True)
        raise click.Abort()

def import_ec2_resources(session, output_dir):
    """Import EC2 instances into Terraform configuration"""
    ec2_client = session.client('ec2')
    
    # Get all EC2 instances
    click.echo(f"{Fore.BLUE}🔍 Scanning EC2 instances...{Style.RESET_ALL}")
    response = ec2_client.describe_instances()
    
    terraform_config = []
    
    # Add AWS provider block
    provider_block = f'''
provider "aws" {{
  region  = "{session.region_name}"
  profile = "{session.profile_name if session.profile_name else 'default'}"
}}
'''
    terraform_config.append(provider_block)
    
    instance_count = 0
    # Process each EC2 instance
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_count += 1
            instance_id = instance['InstanceId']
            click.echo(f"{Fore.GREEN}⚡ Converting instance: {instance_id}{Style.RESET_ALL}")
            
            # Generate Terraform resource block
            resource_block = generate_instance_config(instance)
            terraform_config.append(resource_block)
    
    if instance_count > 0:
        # Write to ec2.tf file
        output_file = output_dir / 'ec2.tf'
        with open(output_file, 'w') as f:
            f.write('\n'.join(terraform_config))
        
        click.echo(f"\n{Fore.GREEN}✨ Successfully processed {instance_count} EC2 instances{Style.RESET_ALL}")
        click.echo(f"{Fore.GREEN}📁 Configuration written to: {output_file}{Style.RESET_ALL}")
    else:
        click.echo(f"{Fore.YELLOW}No EC2 instances found in the region.{Style.RESET_ALL}")

def show_next_steps(output_dir):
    """Display next steps for the user"""
    click.echo(f"\n{Fore.YELLOW}🚀 Next steps:{Style.RESET_ALL}")
    click.echo(f"{Fore.YELLOW}1. cd {output_dir}{Style.RESET_ALL}")
    click.echo(f"{Fore.YELLOW}2. terraform init{Style.RESET_ALL}")
    click.echo(f"{Fore.YELLOW}3. terraform plan{Style.RESET_ALL}")
    click.echo(f"\n{Fore.MAGENTA}Need help? Join our community at: github.com/terra-cli{Style.RESET_ALL}")

def generate_instance_config(instance):
    instance_id = instance['InstanceId']
    tags = get_instance_tags(instance.get('Tags', []))
    
    config = f'''
resource "aws_instance" "{instance_id}" {{
  ami           = "{instance['ImageId']}"
  instance_type = "{instance['InstanceType']}"'''

    if tags:
        config += "\n\n  tags = {\n"
        for key, value in tags.items():
            config += f'    "{key}" = "{value}"\n'
        config += "  }"
    
    # Add additional EBS block devices
    for block_device in instance.get('BlockDeviceMappings', []):
        if 'Ebs' in block_device and block_device['DeviceName'] != instance.get('RootDeviceName'):
            ebs = block_device['Ebs']
            config += f'''
  
  ebs_block_device {{
    device_name           = "{block_device['DeviceName']}"
    volume_type           = "{ebs.get('VolumeType', 'gp2')}"
    volume_size           = {ebs.get('VolumeSize', 8)}
    delete_on_termination = {str(ebs.get('DeleteOnTermination', True)).lower()}'''
            
            if 'Iops' in ebs:
                config += f"\n    iops                  = {ebs['Iops']}"
            if 'Encrypted' in ebs:
                config += f"\n    encrypted             = {str(ebs['Encrypted']).lower()}"
            if 'KmsKeyId' in ebs:
                config += f'\n    kms_key_id            = "{ebs["KmsKeyId"]}"'
            
            config += "\n  }"

    # Add IAM instance profile if present
    if 'IamInstanceProfile' in instance and instance['IamInstanceProfile']:
        profile_arn = instance['IamInstanceProfile']['Arn']
        profile_name = profile_arn.split('/')[-1]
        config += f'\n  iam_instance_profile = "{profile_name}"'

    # Add security groups if present
    if 'SecurityGroups' in instance:
        security_groups = [sg['GroupId'] for sg in instance['SecurityGroups']]
        if security_groups:
            config += '\n  vpc_security_group_ids = ['
            config += ', '.join(f'"{sg}"' for sg in security_groups)
            config += ']'

    # Add tags if present
    tags = get_instance_tags(instance.get('Tags', []))
    if tags:
        config += "\n\n  tags = {\n"
        for key, value in tags.items():
            config += f'    "{key}" = "{value}"\n'
        config += "  }"

    # Add any other mapped attributes that exist in the instance
    for api_attr, tf_attr in attribute_mapping.items():
        if isinstance(tf_attr, dict):
            if api_attr in instance:
                for sub_api_attr, sub_tf_attr in tf_attr.items():
                    if sub_api_attr in instance[api_attr]:
                        value = instance[api_attr][sub_api_attr]
                        if isinstance(value, bool):
                            config += f'\n  {sub_tf_attr} = {str(value).lower()}'
                        elif isinstance(value, (int, float)):
                            config += f'\n  {sub_tf_attr} = {value}'
                        else:
                            config += f'\n  {sub_tf_attr} = "{value}"'
        elif api_attr in instance:
            value = instance[api_attr]
            if isinstance(value, bool):
                config += f'\n  {tf_attr} = {str(value).lower()}'
            elif isinstance(value, (int, float)):
                config += f'\n  {tf_attr} = {value}'
            else:
                config += f'\n  {tf_attr} = "{value}"'

    config += "\n}"
    return config

def get_instance_tags(tags):
    if not tags:
        return {}
    return {tag['Key']: tag['Value'] for tag in tags}

def generate_eventbridge_rule_config(rule, targets, region):
    """Generate Terraform config for an EventBridge rule"""
    # Clean rule name for Terraform resource naming
    resource_name = rule['Name'].replace('-', '_').replace('.', '_')
    
    config = f'''
resource "aws_cloudwatch_event_rule" "{resource_name}" {{
  name                = "{rule['Name']}"
  description         = "{rule.get('Description', '')}"
  schedule_expression = "{rule.get('ScheduleExpression', '')}"
  event_pattern       = {json.dumps(json.loads(rule['EventPattern'])) if 'EventPattern' in rule else 'null'}
  is_enabled          = {str(rule['State'] == 'ENABLED').lower()}'''

    if 'EventBusName' in rule and rule['EventBusName'] != 'default':
        config += f'\n  event_bus_name = "{rule["EventBusName"]}"'

    if 'RoleArn' in rule:
        config += f'\n  role_arn = "{rule["RoleArn"]}"'

    config += "\n}"

    # Add targets
    for idx, target in enumerate(targets):
        target_name = f"{resource_name}_target_{idx}"
        config += f'''

resource "aws_cloudwatch_event_target" "{target_name}" {{
  rule      = aws_cloudwatch_event_rule.{resource_name}.name
  target_id = "{target['Id']}"
  arn       = "{target['Arn']}"'''

        if 'RoleArn' in target:
            config += f'\n  role_arn = "{target["RoleArn"]}"'

        if 'Input' in target:
            config += f'\n  input = {json.dumps(target["Input"])}'
        elif 'InputPath' in target:
            config += f'\n  input_path = "{target["InputPath"]}"'

        if 'InputTransformer' in target:
            config += '''
  input_transformer {'''
            if 'InputPathsMap' in target['InputTransformer']:
                config += f'\n    input_paths = {json.dumps(target["InputTransformer"]["InputPathsMap"])}'
            if 'InputTemplate' in target['InputTransformer']:
                config += f'\n    input_template = {json.dumps(target["InputTransformer"]["InputTemplate"])}'
            config += '\n  }'

        config += "\n}"

    return config

def import_eventbridge_rules(session, output_dir):
    """Import EventBridge rules into Terraform configuration"""
    click.echo(f"{Fore.BLUE}🔍 Scanning EventBridge rules...{Style.RESET_ALL}")
    
    events_client = session.client('events')
    
    # Get all rules
    rules = []
    paginator = events_client.get_paginator('list_rules')
    
    for page in paginator.paginate():
        rules.extend(page['Rules'])
    
    if not rules:
        click.echo(f"{Fore.YELLOW}No EventBridge rules found.{Style.RESET_ALL}")
        return
    
    terraform_config = []
    rule_count = 0
    
    # Add AWS provider block if not already present
    if not (output_dir / 'ec2.tf').exists():
        provider_block = f'''
provider "aws" {{
  region  = "{session.region_name}"
  profile = "{session.profile_name if session.profile_name else 'default'}"
}}
'''
        terraform_config.append(provider_block)
    
    for rule in rules:
        rule_count += 1
        click.echo(f"{Fore.GREEN}⚡ Converting rule: {rule['Name']}{Style.RESET_ALL}")
        
        # Get targets for the rule
        targets_response = events_client.list_targets_by_rule(Rule=rule['Name'])
        targets = targets_response['Targets']
        
        # Generate Terraform configuration
        rule_config = generate_eventbridge_rule_config(rule, targets, session.region_name)
        terraform_config.append(rule_config)
    
    # Write to eventbridge.tf file
    output_file = output_dir / 'eventbridge.tf'
    with open(output_file, 'w') as f:
        f.write('\n'.join(terraform_config))
    
    click.echo(f"\n{Fore.GREEN}✨ Successfully processed {rule_count} EventBridge rules{Style.RESET_ALL}")
    click.echo(f"{Fore.GREEN}📁 Configuration written to: {output_file}{Style.RESET_ALL}")

if __name__ == '__main__':
    cli() 