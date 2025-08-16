# EC2 Setup Script for Homepage Article Scraper
param(
    [string]$Ip = "54.82.140.246",
    [string]$Key = "C:\Users\heman\Downloads\key-scraper.pem"
)

Write-Host "Setting up Homepage Article Scraper on EC2..." -ForegroundColor Cyan
Write-Host "EC2 IP: $Ip" -ForegroundColor Green
Write-Host "Key: $Key" -ForegroundColor Green
Write-Host ""

# Setup commands to run on EC2
$setupCommands = @(
    "cd ~/SCRAPER",
    "sudo yum update -y",
    "sudo yum install -y python3 python3-pip",
    "python3 -m venv venv",
    "source venv/bin/activate",
    "pip install --upgrade pip",
    "pip install -r requirements.txt",
    "echo 'Setup completed successfully!'",
    "python verify_project.py"
)

$fullCommand = $setupCommands -join " && "

Write-Host "Running setup commands on EC2..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

try {
    ssh -i $Key ec2-user@$Ip $fullCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "EC2 setup completed successfully!" -ForegroundColor Green
        Write-Host "You can now run the scraper with:" -ForegroundColor Cyan
        Write-Host ".\scripts\run_remote_simple.ps1 -Ip `"$Ip`" -Key `"$Key`" -Url `"https://www.bbc.com/news`"" -ForegroundColor White
    } else {
        Write-Host "Setup failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "Error during setup: $_" -ForegroundColor Red
}
