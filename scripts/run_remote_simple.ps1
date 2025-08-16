param(
    [Parameter(Mandatory=$true, HelpMessage="EC2 Public IP address")]
    [string]$Ip,
    
    [Parameter(Mandatory=$true, HelpMessage="Path to SSH private key (.pem file)")]
    [string]$Key,
    
    [Parameter(Mandatory=$true, HelpMessage="Target website homepage URL")]
    [string]$Url,
    
    [Parameter(HelpMessage="Output directory name on remote server")]
    [string]$OutDir = "output",
    
    [Parameter(HelpMessage="Local directory to save downloaded results")]
    [string]$LocalResultsDir = "results",
    
    [Parameter(HelpMessage="Maximum number of articles to scrape")]
    [int]$MaxArticles = 40,
    
    [Parameter(HelpMessage="SSH username for EC2 connection")]
    [string]$Username = "ec2-user"
)

# Set error action preference
$ErrorActionPreference = "Stop"

try {
    Write-Host "Homepage Article Scraper - Remote Execution" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Target URL: $Url" -ForegroundColor Green
    Write-Host "EC2 Instance: $Username@$Ip" -ForegroundColor Green
    Write-Host "SSH Key: $Key" -ForegroundColor Green
    Write-Host "Remote Output: $OutDir" -ForegroundColor Green
    Write-Host "Local Results: $LocalResultsDir" -ForegroundColor Green
    Write-Host "Max Articles: $MaxArticles" -ForegroundColor Green
    Write-Host ""

    # Verify prerequisites
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    if (-not (Get-Command "ssh" -ErrorAction SilentlyContinue)) {
        throw "SSH client not found. Please install OpenSSH client."
    }
    
    if (-not (Get-Command "scp" -ErrorAction SilentlyContinue)) {
        throw "SCP client not found. Please install OpenSSH client."
    }
    
    if (-not (Test-Path $Key -PathType Leaf)) {
        throw "SSH key file not found: $Key"
    }
    
    # Get absolute path for key
    $KeyPath = (Resolve-Path $Key).Path
    Write-Host "Key file verified: $KeyPath" -ForegroundColor Green

    # Create local results directory
    if (-not (Test-Path $LocalResultsDir)) {
        New-Item -ItemType Directory -Path $LocalResultsDir -Force | Out-Null
        Write-Host "Created local results directory: $LocalResultsDir" -ForegroundColor Green
    }

    # Test SSH connection
    Write-Host "Testing SSH connection..." -ForegroundColor Yellow
    $testCommand = "echo 'Connection successful'"
    
    try {
        $testResult = ssh -i $KeyPath -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$Username@$Ip" $testCommand 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "SSH connection test failed: $testResult"
        }
        Write-Host "SSH connection successful!" -ForegroundColor Green
    } catch {
        throw "Failed to connect to EC2 instance. Check IP address, key file, and security groups."
    }

    # Prepare the remote command
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $remoteOutputDir = "${OutDir}_${timestamp}"
    
    $remoteCommand = "cd ~/SCRAPER && if [ ! -d 'venv' ]; then echo 'ERROR: Virtual environment not found at ~/SCRAPER/venv'; exit 1; fi && source venv/bin/activate && export MAX_ARTICLES=$MaxArticles && echo 'Starting Homepage Article Scraper...' && python run.py '$Url' --out '$remoteOutputDir' --verbose && echo 'Scraping completed!' && ls -la '$remoteOutputDir/' || echo 'No output directory created'"

    # Execute the scraper on remote server
    Write-Host "Running scraper on remote EC2 instance..." -ForegroundColor Yellow
    Write-Host "Command: cd ~/SCRAPER && source venv/bin/activate && python run.py '$Url' --out '$remoteOutputDir'" -ForegroundColor Gray
    Write-Host ""

    try {
        ssh -i $KeyPath -o StrictHostKeyChecking=no "$Username@$Ip" $remoteCommand
        $remoteExitCode = $LASTEXITCODE
        
        if ($remoteExitCode -ne 0) {
            throw "Remote scraper execution failed with exit code: $remoteExitCode"
        }
        
        Write-Host ""
        Write-Host "Scraper execution completed successfully!" -ForegroundColor Green
        
    } catch {
        throw "Failed to execute scraper on remote server: $_"
    }

    # Check if remote output directory exists and has files
    Write-Host "Checking remote output..." -ForegroundColor Yellow
    $checkOutputCommand = "ls -la ~/SCRAPER/$remoteOutputDir/ 2>/dev/null | wc -l"
    
    try {
        $fileCount = ssh -i $KeyPath -o StrictHostKeyChecking=no "$Username@$Ip" $checkOutputCommand
        $fileCount = [int]$fileCount.Trim()
        
        if ($fileCount -le 1) {
            throw "No output files found in remote directory"
        }
        
        Write-Host "Found $($fileCount - 1) files in remote output directory" -ForegroundColor Green
        
    } catch {
        Write-Host "Warning: Could not verify remote output files" -ForegroundColor Yellow
    }

    # Download results from remote server
    Write-Host "Downloading results from EC2..." -ForegroundColor Yellow
    
    # Create timestamped local directory
    $localOutputPath = Join-Path $LocalResultsDir "${remoteOutputDir}_$(Get-Date -Format 'HHmmss')"
    New-Item -ItemType Directory -Path $localOutputPath -Force | Out-Null
    
    # Download all files from remote output directory
    $remoteSourcePath = "${Username}@${Ip}:~/SCRAPER/${remoteOutputDir}/*"
    
    try {
        scp -i $KeyPath -o StrictHostKeyChecking=no -r $remoteSourcePath $localOutputPath
        
        if ($LASTEXITCODE -ne 0) {
            throw "SCP download failed with exit code: $LASTEXITCODE"
        }
        
        # Verify downloaded files
        $downloadedFiles = Get-ChildItem -Path $localOutputPath -File
        $jsonFiles = $downloadedFiles | Where-Object { $_.Extension -eq ".json" }
        $csvFiles = $downloadedFiles | Where-Object { $_.Extension -eq ".csv" }
        
        Write-Host ""
        Write-Host "Download completed successfully!" -ForegroundColor Green
        Write-Host "Local results directory: $localOutputPath" -ForegroundColor Cyan
        Write-Host "JSON articles: $($jsonFiles.Count)" -ForegroundColor Green
        Write-Host "CSV files: $($csvFiles.Count)" -ForegroundColor Green
        
        # Display file details
        if ($downloadedFiles.Count -gt 0) {
            Write-Host ""
            Write-Host "Downloaded files:" -ForegroundColor Cyan
            foreach ($file in $downloadedFiles) {
                $sizeKB = [math]::Round($file.Length / 1KB, 2)
                Write-Host "  - $($file.Name) ($sizeKB KB)" -ForegroundColor Gray
            }
        }
        
    } catch {
        throw "Failed to download results: $_"
    }

    # Final success message
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "REMOTE SCRAPING COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "Summary:" -ForegroundColor Cyan
    Write-Host "   - Homepage scraped: $Url" -ForegroundColor White
    Write-Host "   - Articles saved: $($jsonFiles.Count)" -ForegroundColor White
    Write-Host "   - Results location: $localOutputPath" -ForegroundColor White
    Write-Host "   - CSV summary: $(if ($csvFiles.Count -gt 0) { 'Available' } else { 'Not found' })" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "   - Review articles: Get-ChildItem '$localOutputPath\*.json'" -ForegroundColor Gray
    Write-Host "   - Open CSV: '$localOutputPath\all_articles.csv'" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Remote scraping failed. Please check the error above." -ForegroundColor Red
    
    # Provide troubleshooting tips
    Write-Host ""
    Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "   - Verify EC2 instance is running and accessible" -ForegroundColor Gray
    Write-Host "   - Check security group allows SSH (port 22)" -ForegroundColor Gray
    Write-Host "   - Ensure key file has correct permissions" -ForegroundColor Gray
    Write-Host "   - Verify scraper project exists at ~/SCRAPER on EC2" -ForegroundColor Gray
    Write-Host "   - Check that Python virtual environment is set up" -ForegroundColor Gray
    
    exit 1
}

# Exit successfully
exit 0
