#Requires -Version 5.1
<#
.SYNOPSIS
    Remote Homepage Article Scraper for AWS EC2 instances.

.DESCRIPTION
    Connects to an EC2 instance via SSH, runs the Homepage Article Scraper,
    and automatically downloads the results back to the local machine.

.PARAMETER Ip
    The public IP address of the EC2 instance.

.PARAMETER Key
    Path to the SSH private key (.pem file) for EC2 authentication.

.PARAMETER Url
    The target website homepage URL to scrape.

.PARAMETER OutDir
    Optional output directory name on the remote server (default: "output").

.PARAMETER LocalResultsDir
    Local directory to download results to (default: "results").

.PARAMETER MaxArticles
    Maximum number of articles to scrape (default: 40).

.PARAMETER Username
    SSH username for EC2 connection (default: "ec2-user").

.EXAMPLE
    .\scripts\run_remote.ps1 -Ip "54.201.123.45" -Key "mykey.pem" -Url "https://www.bbc.com/news"

.EXAMPLE
    .\scripts\run_remote.ps1 -Ip "54.201.123.45" -Key "mykey.pem" -Url "https://techcrunch.com" -OutDir "tech_articles" -MaxArticles 20

.NOTES
    Requires OpenSSH client (available by default on Windows 10/11).
    Ensures the scraper project is located at ~/SCRAPER on the EC2 instance.
#>

param(
    [Parameter(Mandatory=$true, HelpMessage="EC2 Public IP address")]
    [ValidatePattern("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")]
    [string]$Ip,
    
    [Parameter(Mandatory=$true, HelpMessage="Path to SSH private key (.pem file)")]
    [ValidateScript({Test-Path $_ -PathType Leaf})]
    [string]$Key,
    
    [Parameter(Mandatory=$true, HelpMessage="Target website homepage URL")]
    [ValidatePattern("^https?://")]
    [string]$Url,
    
    [Parameter(HelpMessage="Output directory name on remote server")]
    [string]$OutDir = "output",
    
    [Parameter(HelpMessage="Local directory to save downloaded results")]
    [string]$LocalResultsDir = "results",
    
    [Parameter(HelpMessage="Maximum number of articles to scrape")]
    [ValidateRange(1, 100)]
    [int]$MaxArticles = 40,
    
    [Parameter(HelpMessage="SSH username for EC2 connection")]
    [string]$Username = "ec2-user"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to display colored messages
function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color = "White",
        [string]$Emoji = ""
    )
    if ($Emoji) {
        Write-Host "$Emoji $Message" -ForegroundColor $Color
    } else {
        Write-Host $Message -ForegroundColor $Color
    }
}

# Function to check if a command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Main execution
try {
    Write-ColorMessage "Homepage Article Scraper - Remote Execution" "Cyan" "🌐"
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-ColorMessage "Target URL: $Url" "Green"
    Write-ColorMessage "EC2 Instance: $Username@$Ip" "Green"
    Write-ColorMessage "SSH Key: $Key" "Green"
    Write-ColorMessage "Remote Output: $OutDir" "Green"
    Write-ColorMessage "Local Results: $LocalResultsDir" "Green"
    Write-ColorMessage "Max Articles: $MaxArticles" "Green"
    Write-Host ""

    # Verify prerequisites
    Write-ColorMessage "Checking prerequisites..." "Yellow" "🔍"
    
    if (-not (Test-Command "ssh")) {
        throw "SSH client not found. Please install OpenSSH client."
    }
    
    if (-not (Test-Command "scp")) {
        throw "SCP client not found. Please install OpenSSH client."
    }
    
    # Verify key file exists and has correct permissions
    if (-not (Test-Path $Key -PathType Leaf)) {
        throw "SSH key file not found: $Key"
    }
    
    # Get absolute path for key
    $KeyPath = (Resolve-Path $Key).Path
    Write-ColorMessage "Key file verified: $KeyPath" "Green" "🔑"

    # Create local results directory
    if (-not (Test-Path $LocalResultsDir)) {
        New-Item -ItemType Directory -Path $LocalResultsDir -Force | Out-Null
        Write-ColorMessage "Created local results directory: $LocalResultsDir" "Green" "📁"
    }

    # Test SSH connection
    Write-ColorMessage "Testing SSH connection..." "Yellow" "🔗"
    $testCommand = "echo 'Connection successful'"
    $sshArgs = @("-i", $KeyPath, "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=no", "$Username@$Ip", $testCommand)
    
    try {
        $testResult = & ssh @sshArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "SSH connection test failed: $testResult"
        }
        Write-ColorMessage "SSH connection successful!" "Green" "✅"
    } catch {
        throw "Failed to connect to EC2 instance. Check IP address, key file, and security groups."
    }

    # Prepare the remote command
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $remoteOutputDir = "${OutDir}_${timestamp}"
    
    $remoteCommands = @(
        "cd ~/SCRAPER",
        "if [ ! -d 'venv' ]; then echo '❌ Virtual environment not found at ~/SCRAPER/venv'; exit 1; fi",
        "source venv/bin/activate",
        "export MAX_ARTICLES=$MaxArticles",
        "echo '🚀 Starting Homepage Article Scraper...'",
        "python run.py '$Url' --out '$remoteOutputDir' --verbose",
        "echo '📊 Scraping completed!'",
        "ls -la '$remoteOutputDir/' || echo 'No output directory created'"
    )
    
    $fullRemoteCommand = $remoteCommands -join " && "

    # Execute the scraper on remote server
    Write-ColorMessage "Running scraper on remote EC2 instance..." "Yellow" "🚀"
    Write-ColorMessage "Command: cd ~/SCRAPER && source venv/bin/activate && python run.py '$Url' --out '$remoteOutputDir'" "Gray"
    Write-Host ""

    $sshExecArgs = @("-i", $KeyPath, "-o", "StrictHostKeyChecking=no", "$Username@$Ip", $fullRemoteCommand)
    
    try {
        & ssh @sshExecArgs
        $remoteExitCode = $LASTEXITCODE
        
        if ($remoteExitCode -ne 0) {
            throw "Remote scraper execution failed with exit code: $remoteExitCode"
        }
        
        Write-Host ""
        Write-ColorMessage "Scraper execution completed successfully!" "Green" "✅"
        
    } catch {
        throw "Failed to execute scraper on remote server: $_"
    }

    # Check if remote output directory exists and has files
    Write-ColorMessage "Checking remote output..." "Yellow" "📋"
    $checkOutputCommand = "ls -la ~/SCRAPER/$remoteOutputDir/ 2>/dev/null | wc -l"
    $checkArgs = @("-i", $KeyPath, "-o", "StrictHostKeyChecking=no", "$Username@$Ip", $checkOutputCommand)
    
    try {
        $fileCount = & ssh @checkArgs
        $fileCount = [int]$fileCount.Trim()
        
        if ($fileCount -le 1) {  # Only . and .. directories
            throw "No output files found in remote directory"
        }
        
        Write-ColorMessage "Found $($fileCount - 1) files in remote output directory" "Green" "📄"
        
    } catch {
        Write-ColorMessage "Warning: Could not verify remote output files" "Yellow" "⚠️"
    }

    # Download results from remote server
    Write-ColorMessage "Downloading results from EC2..." "Yellow" "📥"
    
    # Create timestamped local directory
    $localOutputPath = Join-Path $LocalResultsDir "${remoteOutputDir}_$(Get-Date -Format 'HHmmss')"
    New-Item -ItemType Directory -Path $localOutputPath -Force | Out-Null
    
    # Download all files from remote output directory
    $remoteSourcePath = "${Username}@${Ip}:~/SCRAPER/${remoteOutputDir}/*"
    $scpArgs = @("-i", $KeyPath, "-o", "StrictHostKeyChecking=no", "-r", $remoteSourcePath, $localOutputPath)
    
    try {
        & scp @scpArgs
        
        if ($LASTEXITCODE -ne 0) {
            throw "SCP download failed with exit code: $LASTEXITCODE"
        }
        
        # Verify downloaded files
        $downloadedFiles = Get-ChildItem -Path $localOutputPath -File
        $jsonFiles = $downloadedFiles | Where-Object { $_.Extension -eq ".json" }
        $csvFiles = $downloadedFiles | Where-Object { $_.Extension -eq ".csv" }
        
        Write-Host ""
        Write-ColorMessage "Download completed successfully!" "Green" "✅"
        Write-ColorMessage "Local results directory: $localOutputPath" "Cyan" "📁"
        Write-ColorMessage "JSON articles: $($jsonFiles.Count)" "Green" "📄"
        Write-ColorMessage "CSV files: $($csvFiles.Count)" "Green" "📊"
        
        # Display file details
        if ($downloadedFiles.Count -gt 0) {
            Write-Host ""
            Write-ColorMessage "Downloaded files:" "Cyan" "📋"
            foreach ($file in $downloadedFiles) {
                $sizeKB = [math]::Round($file.Length / 1KB, 2)
                Write-Host "  • $($file.Name) ($sizeKB KB)" -ForegroundColor Gray
            }
        }
        
    } catch {
        throw "Failed to download results: $_"
    }

    # Optional: Clean up remote files (commented out for safety)
    # Write-ColorMessage "Cleaning up remote files..." "Yellow" "🧹"
    # $cleanupCommand = "rm -rf ~/SCRAPER/$remoteOutputDir"
    # $cleanupArgs = @("-i", $KeyPath, "-o", "StrictHostKeyChecking=no", "$Username@$Ip", $cleanupCommand)
    # & ssh @cleanupArgs | Out-Null

    # Final success message
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Green
    Write-ColorMessage "🎉 REMOTE SCRAPING COMPLETED SUCCESSFULLY!" "Green"
    Write-Host "=" * 60 -ForegroundColor Green
    Write-ColorMessage "✨ Summary:" "Cyan"
    Write-ColorMessage "   • Homepage scraped: $Url" "White"
    Write-ColorMessage "   • Articles saved: $($jsonFiles.Count)" "White"
    Write-ColorMessage "   • Results location: $localOutputPath" "White"
    Write-ColorMessage "   • CSV summary: $(if ($csvFiles.Count -gt 0) { 'Available' } else { 'Not found' })" "White"
    Write-Host ""
    Write-ColorMessage "Next steps:" "Yellow"
    Write-ColorMessage "   • Review articles: Get-ChildItem '$localOutputPath\*.json'" "Gray"
    Write-ColorMessage "   • Open CSV: '$localOutputPath\all_articles.csv'" "Gray"
    Write-Host ""

} catch {
    Write-Host ""
    Write-ColorMessage "❌ Error: $($_.Exception.Message)" "Red"
    Write-ColorMessage "Remote scraping failed. Please check the error above." "Red"
    
    # Provide troubleshooting tips
    Write-Host ""
    Write-ColorMessage "💡 Troubleshooting tips:" "Yellow"
    Write-ColorMessage "   • Verify EC2 instance is running and accessible" "Gray"
    Write-ColorMessage "   • Check security group allows SSH (port 22)" "Gray"
    Write-ColorMessage "   • Ensure key file has correct permissions" "Gray"
    Write-ColorMessage "   • Verify scraper project exists at ~/SCRAPER on EC2" "Gray"
    Write-ColorMessage "   • Check that Python virtual environment is set up" "Gray"
    
    exit 1
}

# Exit successfully
exit 0
