import argparse
import docker
import yaml
import sys

def get_container_details(container):
    container_dict = container.attrs

    # Extract relevant information from container
    image_name = container_dict['Config']['Image']
    volumes_dict = container_dict['Mounts']
    ports_dict = container_dict['NetworkSettings']['Ports']
    env_vars = container_dict['Config']['Env']

    # Generate Docker Compose service
    service = {
        'image': image_name,
        'volumes': {v['Destination']: v.get('Source', {"source": v['Name']}) for v in volumes_dict},
        'ports': [f"{p.split('/')[0]}:{ports_dict[p][0]['HostPort']}" for p in ports_dict if ports_dict[p]],
        'environment': [f"{e}" for e in env_vars]
    }

    return service

def generate_compose_file(containers, output_file, compose_version):
    # Generate Docker Compose file
    compose_dict = {
        'version': compose_version,
        'services': {}
    }

    # Add container services
    for container in containers:
        service = get_container_details(container)
        compose_dict['services'][container.name] = service

    # Write Docker Compose file to disk
    try:
        with open(output_file, 'w') as f:
            yaml.dump(compose_dict, f)
        print(f"Docker Compose file written to {output_file}")
    except IOError as e:
        print(f"Could not write Docker Compose file: {e}")
        sys.exit(1)

def main(container_ids, output_file, compose_version):
    # Connect to Docker API
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        print(f"Error connecting to Docker API: {e}")
        sys.exit(1)

    containers = []
    for container_id in container_ids:
        try:
            container = client.containers.get(container_id)
            containers.append(container)
        except docker.errors.NotFound:
            print(f"Container {container_id} not found")
        except docker.errors.APIError as e:
            print(f"Error communicating with Docker API: {e}")

    # Generate Docker Compose file
    generate_compose_file(containers, output_file, compose_version)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a Docker Compose file from one or more containers.')
    parser.add_argument('container_ids', nargs='+', help='IDs of the containers to inspect')
    parser.add_argument('-o', '--output-file', default='docker-compose.yml',
                        help='Name of output file (default: docker-compose.yml)')
    parser.add_argument('-v', '--compose-version', default='3',
                        help='Version of Docker Compose file to generate (default: 3)')
    args = parser.parse_args()

    main(args.container_ids, args.output_file, args.compose_version)
