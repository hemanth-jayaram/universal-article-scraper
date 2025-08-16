# EC2 Setup Guide for Homepage Article Scraper

## Upload Project to EC2

### Method 1: Using SCP (Recommended)
```bash
# From your local machine, upload the entire project
scp -r -i "your-key.pem" D:\SCRAPER ec2-user@YOUR_EC2_IP:~/

# This uploads everything to ~/SCRAPER/ on EC2
```

### Method 2: Using Git
```bash
# On EC2 instance
ssh -i "your-key.pem" ec2-user@YOUR_EC2_IP
cd ~
git clone YOUR_REPO_URL SCRAPER
cd SCRAPER
```

## Install Dependencies on EC2

```bash
# Connect to EC2
ssh -i "your-key.pem" ec2-user@YOUR_EC2_IP

# Navigate to project
cd ~/SCRAPER

# Update system
sudo yum update -y
sudo yum install -y python3 python3-pip git

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python verify_project.py
```

## Test Local Scraper on EC2

```bash
# Still on EC2, test the scraper locally
source venv/bin/activate
python run.py "https://httpbin.org/html" --out test_output

# Should create test_output/ directory with results
ls -la test_output/
```

## Security Group Configuration

Ensure your EC2 security group allows:
- **SSH (port 22)** from your IP address
- **Optional: HTTP (port 8000)** if you want to use the web UI remotely

## Directory Structure on EC2 Should Be:
```
~/SCRAPER/
├── venv/              # Python virtual environment
├── run.py
├── requirements.txt
├── scraper/
├── app/
├── scripts/
└── tests/
```
