#!/usr/bin/env python
"""
Node Manager - Simplified management of Docker-based QKD nodes
Usage: python node_manager.py <command> [options]
"""

import sys
import os
import subprocess
import json
from datetime import datetime
from typing import List, Optional

class NodeManager:
    """Manage QKD network nodes using Docker"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.node_info_file = os.path.join(self.project_root, '.nodes.json')
        self.nodes = self._load_nodes()
    
    def _load_nodes(self) -> dict:
        """Load node information from file"""
        if os.path.exists(self.node_info_file):
            try:
                with open(self.node_info_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_nodes(self):
        """Save node information to file"""
        with open(self.node_info_file, 'w') as f:
            json.dump(self.nodes, f, indent=2)
    
    def _run_cmd(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command"""
        try:
            return subprocess.run(cmd, check=check, cwd=self.project_root,
                                capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")
            sys.exit(1)
    
    def start_infrastructure(self):
        """Start Mosquitto broker and admin node"""
        print("Starting infrastructure...")
        print("  - Starting Mosquitto broker")
        print("  - Starting admin control center")
        self._run_cmd(['docker-compose', 'up', '-d'])
        print("✓ Infrastructure started")
        self.status()
    
    def stop_infrastructure(self):
        """Stop all services"""
        print("Stopping all services...")
        self._run_cmd(['docker-compose', 'down'])
        print("✓ All services stopped")
    
    def start_node(self, node_id: str, sensor_type: str, eavesdrop: bool = False, 
                  noise: float = 0.0):
        """Start a user node"""
        
        if sensor_type not in ['traffic_flow', 'water_flow', 'surveillance']:
            print(f"✗ Invalid sensor type: {sensor_type}")
            print("  Valid types: traffic_flow, water_flow, surveillance")
            sys.exit(1)
        
        print(f"Starting node: {node_id} (type: {sensor_type})...")
        
        cmd = [
            'docker-compose', 'run', '-d',
            '--name', node_id,
            '-e', 'BROKER_HOST=mosquitto',
            '-e', 'BROKER_PORT=1883',
            '-v', './docker/shared_keystore:/app/network/shared_keystore_data',
            'user-node-template',
            'python', '-m', 'network.sensor_node',
            '--id', node_id,
            '--type', sensor_type
        ]
        
        if eavesdrop:
            cmd.append('--eavesdrop')
        
        if noise > 0:
            cmd.extend(['--noise', str(noise)])
        
        result = self._run_cmd(cmd, check=False)
        
        if result.returncode == 0:
            self.nodes[node_id] = {
                'type': sensor_type,
                'eavesdrop': eavesdrop,
                'noise': noise,
                'started': datetime.now().isoformat()
            }
            self._save_nodes()
            print(f"✓ Node '{node_id}' started")
        else:
            print(f"✗ Failed to start node: {result.stderr}")
            sys.exit(1)
    
    def stop_node(self, node_id: str):
        """Stop a user node"""
        print(f"Stopping node: {node_id}...")
        
        # Stop container
        result = self._run_cmd(['docker', 'stop', node_id], check=False)
        
        if result.returncode == 0:
            if node_id in self.nodes:
                del self.nodes[node_id]
                self._save_nodes()
            print(f"✓ Node '{node_id}' stopped")
        else:
            print(f"✗ Node not found or already stopped: {node_id}")
    
    def stop_all_nodes(self):
        """Stop all user nodes"""
        result = self._run_cmd(['docker', 'ps', '-q', '--filter', 
                               'label=com.docker.compose.service=user-node'], 
                              check=False)
        
        if result.stdout.strip():
            containers = result.stdout.strip().split('\n')
            for container in containers:
                self._run_cmd(['docker', 'stop', container])
            print(f"✓ Stopped {len(containers)} node(s)")
        else:
            print("No user nodes running")
        
        self.nodes.clear()
        self._save_nodes()
    
    def status(self):
        """Show status of all services"""
        print("\n" + "="*60)
        print("QKD Network Status")
        print("="*60)
        
        result = self._run_cmd(['docker-compose', 'ps'], check=False)
        print(result.stdout)
        
        if self.nodes:
            print("\nManaged User Nodes:")
            print("-" * 60)
            for node_id, info in self.nodes.items():
                print(f"  {node_id}")
                print(f"    Type: {info['type']}")
                if info.get('eavesdrop'):
                    print(f"    Eavesdrop: Yes")
                if info.get('noise', 0) > 0:
                    print(f"    Noise: {info['noise']}")
                print()
    
    def logs(self, service: Optional[str] = None):
        """Show logs"""
        if service is None:
            service = 'admin-node'
        
        self._run_cmd(['docker-compose', 'logs', '-f', service])
    
    def rebuild(self):
        """Rebuild Docker images"""
        print("Rebuilding Docker images...")
        self._run_cmd(['docker-compose', 'build', '--no-cache'])
        print("✓ Rebuild complete")
    
    def cleanup(self):
        """Clean up stopped containers and unused images"""
        print("Cleaning up Docker resources...")
        self._run_cmd(['docker', 'container', 'prune', '-f'])
        self._run_cmd(['docker', 'image', 'prune', '-f'])
        print("✓ Cleanup complete")

def show_help():
    """Show help message"""
    help_text = """
QKD Smart City Network - Node Manager

Usage: python node_manager.py <command> [options]

Commands:
    start                   Start infrastructure (broker + admin node)
    stop                    Stop all services
    
    add-node               Add a new user node
                           Usage: add-node <node-id> <sensor-type> [--eavesdrop] [--noise N]
                           Types: traffic_flow, water_flow, surveillance
    
    remove-node            Remove a user node
                           Usage: remove-node <node-id>
    
    remove-all             Remove all user nodes
    
    status                 Show status of all services and nodes
    logs                   Show logs for a service
                           Usage: logs [service-name] (default: admin-node)
    
    rebuild                Rebuild Docker images
    cleanup                Clean up Docker resources

Examples:
    python node_manager.py start
    python node_manager.py add-node traffic-1 traffic_flow
    python node_manager.py add-node camera-1 surveillance --eavesdrop
    python node_manager.py add-node water-1 water_flow --noise 0.05
    python node_manager.py status
    python node_manager.py logs admin-node
    python node_manager.py remove-node traffic-1
    python node_manager.py stop

"""
    print(help_text)

def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    manager = NodeManager()
    command = sys.argv[1]
    
    try:
        if command == 'start':
            manager.start_infrastructure()
        
        elif command == 'stop':
            manager.stop_infrastructure()
        
        elif command == 'add-node':
            if len(sys.argv) < 4:
                print("Usage: add-node <node-id> <sensor-type> [--eavesdrop] [--noise N]")
                sys.exit(1)
            
            node_id = sys.argv[2]
            sensor_type = sys.argv[3]
            eavesdrop = '--eavesdrop' in sys.argv
            noise = 0.0
            
            if '--noise' in sys.argv:
                idx = sys.argv.index('--noise')
                if idx + 1 < len(sys.argv):
                    noise = float(sys.argv[idx + 1])
            
            manager.start_node(node_id, sensor_type, eavesdrop, noise)
        
        elif command == 'remove-node':
            if len(sys.argv) < 3:
                print("Usage: remove-node <node-id>")
                sys.exit(1)
            manager.stop_node(sys.argv[2])
        
        elif command == 'remove-all':
            manager.stop_all_nodes()
        
        elif command == 'status':
            manager.status()
        
        elif command == 'logs':
            service = sys.argv[2] if len(sys.argv) > 2 else None
            manager.logs(service)
        
        elif command == 'rebuild':
            manager.rebuild()
        
        elif command == 'cleanup':
            manager.cleanup()
        
        else:
            print(f"Unknown command: {command}")
            show_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\nCancelled")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
