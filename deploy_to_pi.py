import os
import sys
import subprocess
import getpass

def deploy():
    pi_ip = "10.0.0.86"
    pi_user = "pi5"
    remote_path = "/home/pi5/Server"
    local_path = os.path.join("old_robot", "Server")

    print(f"--- Robot Tank Server Deployment ---")
    print(f"Deploying from: {os.path.abspath(local_path)}")
    print(f"Deploying to:   {pi_user}@{pi_ip}:{remote_path}")
    print("-" * 40)

    try:
        # Check if paramiko is available for smoother password handling
        import paramiko
        from scp import SCPClient

        password = getpass.getpass(f"Enter password for {pi_user}@{pi_ip}: ")
        
        print(f"Connecting to {pi_ip}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(pi_ip, username=pi_user, password=password)
        
        with SCPClient(ssh.get_transport()) as scp:
            print("Cleaning up remote directory...")
            ssh.exec_command(f"rm -rf {remote_path}/*")
            
            print("Uploading files...")
            # Upload all files in the local_path
            for item in os.listdir(local_path):
                source = os.path.join(local_path, item)
                scp.put(source, remote_path, recursive=True)
        
        ssh.close()
        print("\n✅ Deployment successful!")

    except ImportError:
        print("Note: 'paramiko' and 'scp' libraries not found.")
        print("Falling back to system 'scp' command.")
        print("You will be prompted for your password by the system.")
        print("-" * 40)
        
        # Fallback to system scp
        # On Windows, scp -r folder/* user@ip:path works
        try:
            # We use /* on the source to copy contents into the remote folder
            cmd = ["scp", "-r", f"{local_path}/*", f"{pi_user}@{pi_ip}:{remote_path}"]
            subprocess.run(cmd, check=True)
            print("\n✅ Deployment successful!")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Deployment failed with code {e.returncode}")
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    deploy()
