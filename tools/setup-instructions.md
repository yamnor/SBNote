# SBNote Multi-User Setup Instructions

This document provides step-by-step instructions for setting up a multi-user SBNote environment where each user has their own domain and isolated data.

> **Note**: This is the complete setup guide. For a quick overview, see [README.md](../README.md). For security best practices, see [Security Guide](security.md).

## Prerequisites

- Ubuntu/Debian server with Docker and Docker Compose installed
- Nginx installed and configured
- Domain names for each user (e.g., user1.sbnote.me, user2.sbnote.me)
- GitHub repository with the required secrets configured

## Initial Server Setup

### 1. Create Base Directory Structure

```bash
# Create the main application directory
mkdir -p ~/apps/sbnote
cd ~/apps/sbnote

# Create subdirectories
mkdir -p users backups
```

### 2. Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Important: Apply Docker group membership immediately
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y

# Install additional tools
sudo apt install curl net-tools openssl -y
```

### 3. Configure Nginx

```bash
# Create nginx log directories
sudo mkdir -p /var/log/nginx/sbnote

# Set proper permissions
sudo chown -R www-data:www-data /var/log/nginx/sbnote
```

## GitHub Repository Setup

### 1. Required GitHub Secrets

Configure the following secrets in your GitHub repository:

#### Basic Secrets (Required)
```
SSH_PRIVATE_KEY          # SSH private key for server access
DOCKERHUB_USERNAME       # Your Docker Hub username
DOCKERHUB_TOKEN          # Your Docker Hub access token
SERVER_USER              # Server username (e.g., ubuntu)
SERVER_HOST              # Server IP or hostname
```

#### User-Specific Secrets (Required for each user)
```
SBNOTE_DOMAIN_1          # Domain for user1 (e.g., user1.sbnote.me)
SBNOTE_PORT_1            # Port for user1 (e.g., 51000)
SBNOTE_PASSWORD_1        # Password for user1

SBNOTE_DOMAIN_2          # Domain for user2 (e.g., user2.sbnote.me)
SBNOTE_PORT_2            # Port for user2 (e.g., 50011)
SBNOTE_PASSWORD_2        # Password for user2

SBNOTE_DOMAIN_3          # Domain for user3 (e.g., user3.sbnote.me)
SBNOTE_PORT_3            # Port for user3 (e.g., 50012)
SBNOTE_PASSWORD_3        # Password for user3
```

### 2. Generate SSH Key for GitHub Actions

```bash
# Generate SSH key pair (using ed25519 for better security)
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions

# Add public key to server's authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Copy private key content for GitHub secret
cat ~/.ssh/github_actions
```

## Manual User Creation (Alternative to GitHub Actions)

If you prefer to create users manually instead of using GitHub Actions:

### 1. Upload Management Script

```bash
# Upload manage-users.sh to your server
scp manage-users.sh user@your-server:~/apps/sbnote/
chmod +x ~/apps/sbnote/manage-users.sh
```

### 2. Create Users Manually

```bash
cd ~/apps/sbnote

# Create user1 (script will use sudo internally for nginx operations)
./manage-users.sh create user1 user1.sbnote.me 51000

# Create user2
./manage-users.sh create user2 user2.sbnote.me 51001

# Create user3
./manage-users.sh create user3 user3.sbnote.me 51002
```

### 3. Set Passwords

```bash
# Edit each user's .env file to set secure passwords
nano users/user1/.env
nano users/user2/.env
nano users/user3/.env
```

### 4. Start Users

```bash
# Start all users
./manage-users.sh start

# Or start individual users
./manage-users.sh start user1
./manage-users.sh start user2
./manage-users.sh start user3
```

## DNS Configuration

### 1. Add DNS Records

Add A records for each user's domain pointing to your server IP:

```
user1.sbnote.me    A    YOUR_SERVER_IP
user2.sbnote.me    A    YOUR_SERVER_IP
user3.sbnote.me    A    YOUR_SERVER_IP
```

### 2. Verify DNS Propagation

```bash
# Check if DNS records are propagated
nslookup user1.sbnote.me
nslookup user2.sbnote.me
nslookup user3.sbnote.me
```

## Verification and Testing

### 1. Check User Status

```bash
# List all users and their status
./manage-users.sh list

# Check health of all users
./manage-users.sh health-check

# Check individual user health
./manage-users.sh health-check user1
```

### 2. Test Access

```bash
# Test direct port access
curl http://localhost:51000/health
curl http://localhost:51001/health
curl http://localhost:51002/health

# Test domain access (after DNS is configured)
curl http://user1.sbnote.me/health
curl http://user2.sbnote.me/health
curl http://user3.sbnote.me/health
```

### 3. Test Login

Access each user's domain in a web browser:
- http://user1.sbnote.me
- http://user2.sbnote.me
- http://user3.sbnote.me

Login with the credentials set in each user's `.env` file.

## Management Commands Reference

### User Management

```bash
# Create a new user
./manage-users.sh create username domain.com port [password]
# Example: ./manage-users.sh create user1 user1.sbnote.me 51000

# Delete a user
./manage-users.sh delete username domain.com
# Example: ./manage-users.sh delete user1 user1.sbnote.me

# List all users
./manage-users.sh list

# Add user to configuration (for deployment)
./manage-users.sh add-user username domain.com port password
# Example: ./manage-users.sh add-user user1 user1.sbnote.me 51000 mypassword123

# Remove user from configuration
./manage-users.sh remove-user username
```

### Container Management

```bash
# Start all users
./manage-users.sh start

# Start specific user
./manage-users.sh start user1

# Stop all users
./manage-users.sh stop

# Stop specific user
./manage-users.sh stop user1

# Restart all users
./manage-users.sh restart

# Restart specific user
./manage-users.sh restart user1
```

### Monitoring and Logs

```bash
# Check health of all users
./manage-users.sh health-check

# Check health of specific user
./manage-users.sh health-check user1

# View logs for specific user
./manage-users.sh logs user1

# Show container status for all users
./manage-users.sh status

# Show status of specific user
./manage-users.sh status user1
```

### Backup and Maintenance

```bash
# Backup specific user
./manage-users.sh backup user1

# Backup to specific directory
./manage-users.sh backup user1 /path/to/backup/dir

# Update user password
./manage-users.sh update-password username newpassword
# Example: ./manage-users.sh update-password user1 mynewpassword123

# Deploy all users from configuration
./manage-users.sh deploy

# View management script logs
tail -f manage-users.log
```

### Complete Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `create` | Create new user | `./manage-users.sh create user1 user1.sbnote.me 51000` |
| `delete` | Delete user | `./manage-users.sh delete user1 user1.sbnote.me` |
| `start` | Start user(s) | `./manage-users.sh start` or `./manage-users.sh start user1` |
| `stop` | Stop user(s) | `./manage-users.sh stop` or `./manage-users.sh stop user1` |
| `restart` | Restart user(s) | `./manage-users.sh restart` or `./manage-users.sh restart user1` |
| `health-check` | Check health | `./manage-users.sh health-check` or `./manage-users.sh health-check user1` |
| `logs` | View logs | `./manage-users.sh logs user1` |
| `status` | Show status | `./manage-users.sh status` or `./manage-users.sh status user1` |
| `list` | List all users | `./manage-users.sh list` |
| `backup` | Backup user data | `./manage-users.sh backup user1` |
| `update-password` | Update password | `./manage-users.sh update-password user1 newpass` |
| `deploy` | Deploy all from config | `./manage-users.sh deploy` |
| `add-user` | Add to config | `./manage-users.sh add-user user1 user1.sbnote.me 51000 pass` |
| `remove-user` | Remove from config | `./manage-users.sh remove-user user1` |

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
sudo ss -tulp | grep :51000

# Kill the process if necessary
sudo kill -9 <PID>
```

#### 2. Nginx Configuration Error

```bash
# Test nginx configuration
sudo nginx -t

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log
```

#### 3. Container Won't Start

```bash
# Check container logs
./manage-users.sh logs user1

# Check container status
./manage-users.sh status user1

# Check if image exists
docker images | grep sbnote
```

#### 4. Permission Issues

```bash
# Fix permissions
sudo chown -R $USER:$USER ~/apps/sbnote
chmod +x ~/apps/sbnote/manage-users.sh
```

#### 5. Docker Permission Denied Error

If you encounter the error `permission denied while trying to connect to the Docker daemon socket`, follow these steps:

**Error Message:**
```
unable to get image 'yamnor/sbnote:latest': permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

**Solution 1: Add User to Docker Group**
```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run this command to apply changes immediately
newgrp docker

# Verify the user is in the docker group
groups $USER
```

**Solution 2: Start Docker Daemon**
```bash
# Start Docker daemon
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Check Docker status
sudo systemctl status docker
```

**Solution 3: Verify Docker Installation**
```bash
# Check Docker version
docker --version

# Test Docker access
docker ps
```

**Note:** After adding the user to the docker group, you may need to log out and log back in for the changes to take effect. Alternatively, use `newgrp docker` to apply the changes immediately.

### Log Locations

- **Management Script Logs**: `~/apps/sbnote/manage-users.log`
- **Nginx Access Logs**: `/var/log/nginx/sbnote-*-access.log`
- **Nginx Error Logs**: `/var/log/nginx/sbnote-*-error.log`
- **Container Logs**: `./manage-users.sh logs <username>`

## Security Considerations

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (if using SSL)
sudo ufw enable
```

### 2. Regular Updates

```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Update Docker images
./manage-users.sh stop
docker pull yamnor/sbnote:latest
./manage-users.sh start
```

### 3. Backup Strategy

```bash
# Create daily backups
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * cd ~/apps/sbnote && ./manage-users.sh backup user1 && ./manage-users.sh backup user2 && ./manage-users.sh backup user3
```

## Scaling Considerations

### Adding More Users

1. **Update GitHub Secrets**: Add new user secrets (SBNOTE_DOMAIN_4, SBNOTE_PORT_4, etc.)
2. **Update deploy.yml**: Add new user creation logic
3. **Configure DNS**: Add A record for new domain
4. **Deploy**: Push to main branch to trigger automatic deployment

### Resource Monitoring

```bash
# Monitor resource usage
docker stats

# Monitor disk usage
df -h ~/apps/sbnote

# Monitor memory usage
free -h
```

## Support

For issues and questions:
1. Check the logs: `./manage-users.sh logs <username>`
2. Verify configuration: `./manage-users.sh list`
3. Test connectivity: `./manage-users.sh health-check`
4. Review this documentation

The management script provides comprehensive logging and error handling to help diagnose and resolve issues quickly. 