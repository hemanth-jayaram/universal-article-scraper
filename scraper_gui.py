#!/usr/bin/env python3
"""
Modern Scraper GUI

A beautiful, modern GUI interface for the article scraper and summarizer.
Integrates with existing scripts without modifying core functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import shutil
from pathlib import Path
import time
import re
import queue
import json

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_variables()
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        
        # Queue for thread communication
        self.output_queue = queue.Queue()
        self.setup_output_monitor()
        
    def setup_window(self):
        """Setup main window properties."""
        self.root.title("🚀 Article Scraper & Summarizer")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"900x700+{x}+{y}")
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def setup_variables(self):
        """Initialize tkinter variables."""
        self.url_var = tk.StringVar(value="https://timesofindia.indiatimes.com/sports")
        self.articles_var = tk.StringVar(value="20")
        self.status_var = tk.StringVar(value="Ready")
        
        # Progress variables
        self.scrape_progress = tk.DoubleVar()
        self.filter_progress = tk.DoubleVar()
        self.summary_progress = tk.DoubleVar()
        self.convert_progress = tk.DoubleVar()
        
        # State variables
        self.scraping = False
        self.filtering = False
        self.summarizing = False
        self.converting = False
        
    def setup_styles(self):
        """Setup modern styling."""
        style = ttk.Style()
        
        # Configure modern button style
        style.configure(
            "Modern.TButton",
            padding=(20, 10),
            font=("Segoe UI", 10),
        )
        
        # Configure action button style
        style.configure(
            "Action.TButton", 
            padding=(25, 12),
            font=("Segoe UI", 11, "bold"),
        )
        
        # Configure danger button style
        style.configure(
            "Danger.TButton",
            padding=(20, 10),
            font=("Segoe UI", 10),
        )
        
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="🚀 Article Scraper & Summarizer",
            font=("Segoe UI", 16, "bold")
        )
        
        # Description
        self.description_label = ttk.Label(
            self.main_frame,
            text="🔄 NEW FLOW: Scrape → Filter → Download | Only valid articles are downloaded",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        
        # Input section
        self.input_frame = ttk.LabelFrame(self.main_frame, text="📝 Scraping & Filtering Configuration", padding="15")
        
        self.url_label = ttk.Label(self.input_frame, text="Website URL:")
        self.url_entry = ttk.Entry(self.input_frame, textvariable=self.url_var, font=("Segoe UI", 10), width=60)
        
        self.articles_label = ttk.Label(self.input_frame, text="Number of Articles:")
        self.articles_entry = ttk.Entry(self.input_frame, textvariable=self.articles_var, font=("Segoe UI", 10), width=15)
        
        # Action buttons section
        self.actions_frame = ttk.LabelFrame(self.main_frame, text="⚡ Actions", padding="15")
        
        self.scrape_btn = ttk.Button(
            self.actions_frame,
            text="🔍 Scrape & Filter",
            command=self.start_scraping,
            style="Action.TButton"
        )
        

        
        self.summarize_btn = ttk.Button(
            self.actions_frame,
            text="📝 Summarize Articles",
            command=self.start_summarizing,
            style="Action.TButton",
            state='disabled'
        )
        
        self.convert_btn = ttk.Button(
            self.actions_frame,
            text="📄 Convert to TXT",
            command=self.start_converting,
            style="Action.TButton",
            state='disabled'
        )
        
        # Utility buttons section
        self.utils_frame = ttk.LabelFrame(self.main_frame, text="🗂️ File Management", padding="15")
        
        self.clear_results_btn = ttk.Button(
            self.utils_frame,
            text="🗑️ Clear Results",
            command=self.clear_results,
            style="Danger.TButton"
        )
        

        
        self.clear_summary_btn = ttk.Button(
            self.utils_frame,
            text="🗑️ Clear Summary",
            command=self.clear_summary,
            style="Danger.TButton"
        )
        
        self.open_results_btn = ttk.Button(
            self.utils_frame,
            text="📁 Open Results",
            command=self.open_results_folder,
            style="Modern.TButton"
        )
        

        
        self.open_summary_btn = ttk.Button(
            self.utils_frame,
            text="📁 Open Summary",
            command=self.open_summary_folder,
            style="Modern.TButton"
        )
        
        self.clear_converted_btn = ttk.Button(
            self.utils_frame,
            text="🗑️ Clear Converted",
            command=self.clear_converted,
            style="Danger.TButton"
        )
        
        self.open_converted_btn = ttk.Button(
            self.utils_frame,
            text="📁 Open Converted",
            command=self.open_converted_folder,
            style="Modern.TButton"
        )
        
        # Progress section
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="📊 Progress", padding="15")
        
        self.scrape_progress_label = ttk.Label(self.progress_frame, text="Scraping Progress:")
        self.scrape_progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.scrape_progress,
            maximum=100,
            length=300,
            mode='determinate'
        )
        
        self.filter_progress_label = ttk.Label(self.progress_frame, text="Filtering Progress:")
        self.filter_progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.filter_progress,
            maximum=100,
            length=300,
            mode='determinate'
        )
        
        self.summary_progress_label = ttk.Label(self.progress_frame, text="Summary Progress:")
        self.summary_progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.summary_progress,
            maximum=100,
            length=300,
            mode='determinate'
        )
        
        self.convert_progress_label = ttk.Label(self.progress_frame, text="Convert Progress:")
        self.convert_progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.convert_progress,
            maximum=100,
            length=300,
            mode='determinate'
        )
        
        # Status and output section
        self.output_frame = ttk.LabelFrame(self.main_frame, text="📋 Status & Output", padding="15")
        

        
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame,
            height=15,
            width=80,
            font=("Consolas", 9),
            background="#f8f9fa",
            foreground="#212529"
        )
        
    def setup_layout(self):
        """Setup widget layout."""
        # Main frame
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Title
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Description
        self.description_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Input section
        self.input_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.input_frame.grid_columnconfigure(1, weight=1)
        
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.url_entry.grid(row=0, column=1, sticky="ew", pady=(0, 10), padx=(10, 0))
        
        self.articles_label.grid(row=1, column=0, sticky="w")
        self.articles_entry.grid(row=1, column=1, sticky="w", padx=(10, 0))
        
        # Actions section
        self.actions_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15), padx=(0, 10))
        
        self.scrape_btn.grid(row=0, column=0, padx=(0, 10))
        self.summarize_btn.grid(row=0, column=1, padx=(0, 10))
        self.convert_btn.grid(row=0, column=2)
        
        # Utils section
        self.utils_frame.grid(row=3, column=1, sticky="ew", pady=(0, 15))
        
        self.clear_results_btn.grid(row=0, column=0, padx=(0, 5))
        self.clear_summary_btn.grid(row=0, column=1, padx=(0, 5))
        self.clear_converted_btn.grid(row=0, column=2, padx=(0, 5))
        self.open_results_btn.grid(row=1, column=0, padx=(0, 5), pady=(10, 0))
        self.open_summary_btn.grid(row=1, column=1, padx=(0, 5), pady=(10, 0))
        self.open_converted_btn.grid(row=1, column=2, padx=(0, 5), pady=(10, 0))
        
        # Progress section
        self.progress_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.progress_frame.grid_columnconfigure(1, weight=1)
        
        self.scrape_progress_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.scrape_progress_bar.grid(row=0, column=1, sticky="ew", pady=(0, 5), padx=(10, 0))
        
        self.filter_progress_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.filter_progress_bar.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(10, 0))
        
        self.summary_progress_label.grid(row=2, column=0, sticky="w", pady=(5, 0))
        self.summary_progress_bar.grid(row=2, column=1, sticky="ew", pady=(5, 0), padx=(10, 0))
        
        self.convert_progress_label.grid(row=3, column=0, sticky="w", pady=(5, 0))
        self.convert_progress_bar.grid(row=3, column=1, sticky="ew", pady=(5, 0), padx=(10, 0))
        
        # Output section
        self.output_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(0, 0))
        self.output_frame.grid_rowconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)
        
        self.output_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure main frame grid weights
        self.main_frame.grid_rowconfigure(5, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
    def setup_output_monitor(self):
        """Setup output monitoring from background processes."""
        self.root.after(100, self.check_output_queue)
        
    def check_output_queue(self):
        """Check for new output from background processes."""
        try:
            while True:
                message = self.output_queue.get_nowait()
                self.add_output(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_output_queue)
            
    def add_output(self, message):
        """Add message to output text widget."""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_status(self, message):
        """Update status by adding message to output."""
        self.add_output(f"🔄 {message}")
        self.root.update_idletasks()
        
    def start_scraping(self):
        """Start scraping in background thread."""
        if self.scraping:
            return
            
        url = self.url_var.get().strip()
        articles = self.articles_var.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a website URL")
            return
            
        if not articles or not articles.isdigit():
            messagebox.showerror("Error", "Please enter a valid number of articles")
            return
            
        self.scraping = True
        self.scrape_btn.config(state='disabled')
        self.summarize_btn.config(state='disabled')
        self.scrape_progress.set(0)
        self.filter_progress.set(0)
        
        self.update_status("Starting scraper...")
        self.add_output("🚀 Starting article scraping...")
        self.add_output(f"📍 URL: {url}")
        self.add_output(f"📊 Articles: {articles}")
        self.add_output("🔄 NEW FLOW: Scrape → Filter → Download")
        self.add_output("-" * 50)
        
        # Start scraping thread
        thread = threading.Thread(
            target=self.run_scraper,
            args=(url, int(articles)),
            daemon=True
        )
        thread.start()
        
    def run_scraper(self, url, articles):
        """Run scraper script in background."""
        try:
            # Use the existing remote scraping script
            script_path = Path("scripts/run_remote_simple.ps1")
            
            if script_path.exists():
                # Run PowerShell script
                cmd = [
                    "powershell.exe",
                    "-ExecutionPolicy", "Bypass",
                    "-File", str(script_path),
                    "-Ip", "54.82.140.246",
                    "-Key", "C:\\Users\\heman\\Downloads\\key-scraper.pem",
                    "-Url", url,
                    "-MaxArticles", str(articles)
                ]
                
                self.output_queue.put(f"💻 Running command: {' '.join(cmd[4:])}")
                
            else:
                # Fallback to local scraping
                cmd = [
                    sys.executable, "run.py", url,
                    "--out", f"output_{int(time.time())}",
                    "--max-articles", str(articles),
                    "--verbose"
                ]
                
                self.output_queue.put(f"💻 Running local scraper: {' '.join(cmd[1:])}")
            
            # Run process and capture output in real-time
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=0,  # Unbuffered
                cwd=os.getcwd()
            )
            
            articles_found = 0
            total_articles = articles
            
            # Track download progress
            total_files = 0
            
            # NEW: Track filtering progress
            filtering_started = False
            filtering_complete = False
            
            # Monitor output in real-time
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.output_queue.put(line.strip())
                    
                    # Progress tracking for scraping phase
                    if "Starting Homepage Article Scraper" in line:
                        self.scrape_progress.set(5)
                        self.update_status("Starting scraper...")
                    elif any(phrase in line for phrase in ["Saved article:", "Processing article"]):
                        articles_found += 1
                        progress = min((articles_found / total_articles) * 40, 40)
                        self.scrape_progress.set(progress)
                        self.update_status(f"Processing articles... ({articles_found})")
                    elif "Found" in line and "files in remote output directory" in line:
                        # Extract total file count
                        match = re.search(r'Found (\d+) files', line)
                        if match:
                            total_files = int(match.group(1))
                    elif "Checking remote output" in line:
                        self.scrape_progress.set(42)
                        self.update_status("Checking remote output...")
                    elif "Downloading results" in line:
                        self.scrape_progress.set(45)
                        if total_files > 0:
                            self.update_status(f"Downloading {total_files} files from EC2...")
                        else:
                            self.update_status("Downloading results from EC2...")
                    elif "Download completed" in line:
                        self.scrape_progress.set(50)
                        self.update_status("Download completed - Starting filtering...")
                    elif "JSON articles:" in line:
                        # Extract final article count
                        match = re.search(r'JSON articles: (\d+)', line)
                        if match:
                            json_count = int(match.group(1))
                            self.scrape_progress.set(50)
                            self.update_status(f"Downloaded {json_count} articles - Starting filtering...")
                    
                    # NEW: Progress tracking for filtering phase (integrated into scraping)
                    elif "SCRAPING COMPLETE - STARTING FILTERING" in line:
                        filtering_started = True
                        self.scrape_progress.set(60)
                        self.filter_progress.set(10)
                        self.update_status("Scraping complete - Starting filtering...")
                    elif "🔍 Starting article filtering" in line:
                        self.filter_progress.set(20)
                        self.update_status("Starting article filtering...")
                    elif "🔍 Filtering" in line and "scraped articles" in line:
                        # Extract article count for filtering progress
                        match = re.search(r'Filtering (\d+) scraped articles', line)
                        if match:
                            total_to_filter = int(match.group(1))
                            self.filter_progress.set(30)
                            self.update_status(f"Filtering {total_to_filter} articles...")
                    elif "🔍 Filtering complete:" in line:
                        filtering_complete = True
                        self.filter_progress.set(70)
                        # Extract final filtered count
                        match = re.search(r'🔍 Filtering complete: (\d+)/(\d+) articles passed filter', line)
                        if match:
                            filtered_count = int(match.group(1))
                            total_count = int(match.group(2))
                            self.update_status(f"Filtering complete: {filtered_count}/{total_count} articles passed")
                    elif "✅ Filtering complete:" in line and "articles passed filter" in line:
                        # Alternative pattern: "✅ Filtering complete: X articles passed filter"
                        self.filter_progress.set(75)
                        match = re.search(r'✅ Filtering complete: (\d+) articles passed filter', line)
                        if match:
                            filtered_count = int(match.group(1))
                            self.update_status(f"Filtering complete: {filtered_count} articles passed")
                    
                    # NEW: Progress tracking for saving phase (integrated into scraping)
                    elif "💾 Saving filtered articles" in line:
                        self.filter_progress.set(80)
                        self.update_status("Saving filtered articles...")
                    elif "💾 Saving" in line and "filtered articles" in line:
                        # Extract count for saving progress
                        match = re.search(r'💾 Saving (\d+) filtered articles', line)
                        if match:
                            to_save = int(match.group(1))
                            self.filter_progress.set(85)
                            self.update_status(f"Saving {to_save} filtered articles...")
                    elif "💾 Saving complete:" in line and ("articles saved successfully" in line or "articles saved" in line):
                        # Extract final saved count
                        match = re.search(r'💾 Saving complete: (\d+) articles saved', line)
                        if match:
                            saved_count = int(match.group(1))
                            self.filter_progress.set(100)
                            self.scrape_progress.set(100)
                            self.update_status(f"Completed: {saved_count} articles saved after filtering")
                    elif "Articles saved:" in line and "FINAL RESULTS" in line:
                        # This catches the final summary from spider
                        match = re.search(r'Articles saved: (\d+)', line)
                        if match:
                            saved_count = int(match.group(1))
                            self.filter_progress.set(100)
                            self.scrape_progress.set(100)
                            self.update_status(f"Completed: {saved_count} articles saved after filtering")
                    elif "Articles scraped:" in line and "Articles filtered:" in line and "Articles saved:" in line:
                        # This catches the spider's final results summary line
                        self.filter_progress.set(100)
                        self.scrape_progress.set(100)
                        self.update_status("Scraping and filtering completed successfully!")
                    
                    # Final completion indicators
                    elif "FINAL RESULTS" in line:
                        self.scrape_progress.set(85)
                        self.filter_progress.set(90)
                        self.update_status("Finalizing results...")
                    elif "Spider closed (finished)" in line:
                        # Scrapy completion indicator
                        self.scrape_progress.set(100)
                        self.filter_progress.set(100)
                        self.update_status("Scraping and filtering completed successfully!")
                    elif "✅ Scraping completed successfully!" in line:
                        # Remote script final completion
                        self.scrape_progress.set(100)
                        self.filter_progress.set(100)
                        self.update_status("Scraping and filtering completed successfully!")
            
            process.wait()
            
            if process.returncode == 0:
                self.output_queue.put("✅ Scraping and filtering completed successfully!")
                # Ensure progress bars reach 100% on successful completion
                self.scrape_progress.set(100)
                self.filter_progress.set(100)
                self.update_status("Scraping and filtering completed - Ready to summarize")
                self.summarize_btn.config(state='normal')
                self.convert_btn.config(state='normal')
            else:
                self.output_queue.put("❌ Scraping failed!")
                self.update_status("Scraping failed")
                
        except Exception as e:
            self.output_queue.put(f"❌ Error: {str(e)}")
            self.update_status("Scraping error")
            
        finally:
            self.scraping = False
            self.scrape_btn.config(state='normal')
            
    def start_filtering(self):
        """Start filtering in background thread - for manual filtering of already-downloaded files."""
        if self.filtering:
            return
            
        if not Path("results").exists():
            messagebox.showwarning("Warning", "No results folder found. Please scrape articles first.")
            return
            
        self.filtering = True
        self.summarize_btn.config(state='disabled')
        self.filter_progress.set(0)
        
        self.update_status("Starting manual article filtering...")
        self.add_output("🔍 Starting manual article filtering...")
        self.add_output("ℹ️ This filters already-downloaded files (separate from automatic filtering)")
        self.add_output("-" * 50)
        
        # Start filtering thread
        thread = threading.Thread(target=self.run_filter, daemon=True)
        thread.start()
        
    def run_filter(self):
        """Run filter script in background."""
        try:
            cmd = [sys.executable, "filter_articles.py", "--input", "results", "--output", "filter"]
            
            self.output_queue.put(f"💻 Running filter: {' '.join(cmd[1:])}")
            
            # Run process and capture output with unbuffered mode
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                universal_newlines=True,
                bufsize=1,  # Line buffered
                cwd=os.getcwd(),
                env=dict(os.environ, PYTHONUNBUFFERED='1')
            )
            
            articles_processed = 0
            total_articles = 0
            
            # Monitor output
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.output_queue.put(line.strip())
                    
                    # Update progress based on output
                    if "Found" in line and "JSON files" in line:
                        match = re.search(r'Found (\d+) JSON files', line)
                        if match:
                            total_articles = int(match.group(1))
                            self.filter_progress.set(10)
                            
                    elif "Articles identified:" in line:
                        match = re.search(r'Articles identified: (\d+)', line)
                        if match:
                            articles_identified = int(match.group(1))
                            self.filter_progress.set(50)
                            self.update_status(f"Identified {articles_identified} articles for filtering")
                            
                    elif "✅ Copied:" in line:
                        articles_processed += 1
                        if total_articles > 0:
                            progress = 50 + min((articles_processed / total_articles) * 45, 45)
                            self.filter_progress.set(progress)
                            self.update_status(f"Copying articles... ({articles_processed})")
                            
                    elif "Articles copied:" in line:
                        match = re.search(r'Articles copied: (\d+)', line)
                        if match:
                            final_count = int(match.group(1))
                            self.filter_progress.set(100)
                            self.update_status(f"Filtering completed: {final_count} articles")
            
            process.wait()
            
            if process.returncode == 0:
                self.output_queue.put("✅ Filtering completed successfully!")
                self.update_status("Filtering completed - Ready to summarize")
                self.summarize_btn.config(state='normal')
            else:
                self.output_queue.put("❌ Filtering failed!")
                self.update_status("Filtering failed")
                
        except Exception as e:
            self.output_queue.put(f"❌ Error: {str(e)}")
            self.update_status("Filtering error")
            
        finally:
            self.filtering = False
    
    def start_summarizing(self):
        """Start summarization in background thread."""
        if self.summarizing:
            return
            
        if not Path("filter").exists():
            messagebox.showwarning("Warning", "No filter folder found. Please filter articles first.")
            return
            
        self.summarizing = True
        self.summarize_btn.config(state='disabled')
        self.summary_progress.set(0)
        
        self.update_status("Starting summarization...")
        self.add_output("📝 Starting article summarization...")
        self.add_output("-" * 50)
        
        # Start summarization thread
        thread = threading.Thread(target=self.run_summarizer, daemon=True)
        thread.start()
        
    def run_summarizer(self):
        """Run summarizer script in background."""
        try:
            cmd = [sys.executable, "summarize_articles_simple_fast.py", "--input", "filter", "--batch-size", "4", "--skip-filtering"]
            
            self.output_queue.put(f"💻 Running summarizer: {' '.join(cmd[1:])}")
            
            # Run process and capture output with unbuffered mode
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                universal_newlines=True,
                bufsize=1,  # Line buffered
                cwd=os.getcwd(),
                env=dict(os.environ, PYTHONUNBUFFERED='1')
            )
            
            articles_processed = 0
            total_articles = 0
            
            # Monitor output
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.output_queue.put(line.strip())
                    
                    # Update progress based on output
                    if "Articles to summarize:" in line:
                        match = re.search(r'Articles to summarize: (\d+)', line)
                        if match:
                            total_articles = int(match.group(1))
                            
                    elif "Article 1 summarized" in line or "✅ Saved:" in line:
                        articles_processed += 1
                        if total_articles > 0:
                            progress = min((articles_processed / total_articles) * 100, 100)
                            self.summary_progress.set(progress)
                            self.update_status(f"Summarized {articles_processed}/{total_articles} articles")
                            
                    elif "Articles processed:" in line:
                        match = re.search(r'Articles processed: (\d+)', line)
                        if match:
                            final_count = int(match.group(1))
                            self.summary_progress.set(100)
                            self.update_status(f"Summarization completed: {final_count} articles")
            
            process.wait()
            
            if process.returncode == 0:
                self.output_queue.put("✅ Summarization completed successfully!")
                self.update_status("Summarization completed")
            else:
                self.output_queue.put("❌ Summarization failed!")
                self.update_status("Summarization failed")
                
        except Exception as e:
            self.output_queue.put(f"❌ Error: {str(e)}")
            self.update_status("Summarization error")
            
        finally:
            self.summarizing = False
            self.summarize_btn.config(state='normal')
    
    def start_converting(self):
        """Start conversion in background thread."""
        if self.converting:
            return
            
        if not Path("results").exists():
            messagebox.showwarning("Warning", "No results folder found. Please scrape articles first.")
            return
            
        self.converting = True
        self.convert_btn.config(state='disabled')
        self.convert_progress.set(0)
        
        self.update_status("Starting JSON to TXT conversion...")
        self.add_output("📄 Starting JSON to TXT conversion...")
        self.add_output("-" * 50)
        
        # Start conversion thread
        thread = threading.Thread(target=self.run_converter, daemon=True)
        thread.start()
        
    def run_converter(self):
        """Run converter script in background."""
        try:
            cmd = [sys.executable, "convert_json_to_txt.py", "--input", "results", "--output", "converted"]
            
            self.output_queue.put(f"💻 Running converter: {' '.join(cmd[1:])}")
            
            # Run process and capture output with unbuffered mode
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                universal_newlines=True,
                bufsize=1,  # Line buffered
                cwd=os.getcwd(),
                env=dict(os.environ, PYTHONUNBUFFERED='1')
            )
            
            files_processed = 0
            total_files = 0
            
            # Monitor output
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.output_queue.put(line.strip())
                    
                    # Update progress based on output
                    if "Found" in line and "JSON files to convert" in line:
                        match = re.search(r'Found (\d+) JSON files to convert', line)
                        if match:
                            total_files = int(match.group(1))
                            self.convert_progress.set(10)
                            self.update_status(f"Found {total_files} JSON files to convert")
                            
                    elif "Converting" in line and "files with" in line:
                        self.convert_progress.set(20)
                        self.update_status("Starting conversion process...")
                            
                    elif "✅ Converted:" in line:
                        files_processed += 1
                        if total_files > 0:
                            progress = 20 + min((files_processed / total_files) * 70, 70)
                            self.convert_progress.set(progress)
                            self.update_status(f"Converting files... ({files_processed}/{total_files})")
                            
                    elif "Files converted:" in line:
                        match = re.search(r'Files converted: (\d+)', line)
                        if match:
                            final_count = int(match.group(1))
                            self.convert_progress.set(100)
                            self.update_status(f"Conversion completed: {final_count} files converted")
            
            process.wait()
            
            if process.returncode == 0:
                self.output_queue.put("✅ Conversion completed successfully!")
                self.convert_progress.set(100)
                self.update_status("Conversion completed")
            else:
                self.output_queue.put("❌ Conversion failed!")
                self.update_status("Conversion failed")
                
        except Exception as e:
            self.output_queue.put(f"❌ Error: {str(e)}")
            self.update_status("Conversion error")
            
        finally:
            self.converting = False
            self.convert_btn.config(state='normal')
            
    def clear_results(self):
        """Clear results folder."""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all results?"):
            try:
                results_path = Path("results")
                if results_path.exists():
                    shutil.rmtree(results_path)
                    results_path.mkdir()
                    
                self.add_output("🗑️ Results folder cleared")
                self.update_status("Results cleared")
                self.summarize_btn.config(state='disabled')
                self.scrape_progress.set(0)
                self.filter_progress.set(0)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear results: {str(e)}")
                
    def clear_filter(self):
        """Clear filter folder."""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all filtered articles?"):
            try:
                filter_path = Path("filter")
                if filter_path.exists():
                    shutil.rmtree(filter_path)
                    filter_path.mkdir()
                    
                self.add_output("🗑️ Filter folder cleared")
                self.update_status("Filter cleared")
                self.summarize_btn.config(state='disabled')
                self.filter_progress.set(0)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear filter: {str(e)}")
                
    def clear_summary(self):
        """Clear summary folder."""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all summaries?"):
            try:
                summary_path = Path("summary")
                if summary_path.exists():
                    shutil.rmtree(summary_path)
                    summary_path.mkdir()
                    
                self.add_output("🗑️ Summary folder cleared")
                self.update_status("Summary cleared")
                self.summary_progress.set(0)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear summary: {str(e)}")
                
    def open_results_folder(self):
        """Open results folder in file explorer."""
        try:
            results_path = Path("results").absolute()
            if not results_path.exists():
                results_path.mkdir()
                
            if sys.platform == "win32":
                os.startfile(results_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", results_path])
            else:
                subprocess.run(["xdg-open", results_path])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open results folder: {str(e)}")
            
    def open_filter_folder(self):
        """Open filter folder in file explorer."""
        try:
            filter_path = Path("filter").absolute()
            if not filter_path.exists():
                filter_path.mkdir()
                
            if sys.platform == "win32":
                os.startfile(filter_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", filter_path])
            else:
                subprocess.run(["xdg-open", filter_path])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open filter folder: {str(e)}")
            
    def open_summary_folder(self):
        """Open summary folder in file explorer."""
        try:
            summary_path = Path("summary").absolute()
            if not summary_path.exists():
                summary_path.mkdir()
                
            if sys.platform == "win32":
                os.startfile(summary_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", summary_path])
            else:
                subprocess.run(["xdg-open", summary_path])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open summary folder: {str(e)}")
    
    def clear_converted(self):
        """Clear converted folder."""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all converted files?"):
            try:
                converted_path = Path("converted")
                if converted_path.exists():
                    shutil.rmtree(converted_path)
                    converted_path.mkdir()
                    
                self.add_output("🗑️ Converted folder cleared")
                self.update_status("Converted cleared")
                self.convert_progress.set(0)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear converted: {str(e)}")
                
    def open_converted_folder(self):
        """Open converted folder in file explorer."""
        try:
            converted_path = Path("converted").absolute()
            if not converted_path.exists():
                converted_path.mkdir()
                
            if sys.platform == "win32":
                os.startfile(converted_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", converted_path])
            else:
                subprocess.run(["xdg-open", converted_path])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open converted folder: {str(e)}")

def main():
    """Main function to run the GUI."""
    try:
        root = tk.Tk()
        app = ScraperGUI(root)
        
        # Handle window closing
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                root.destroy()
                
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the GUI
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        messagebox.showerror("Error", f"Failed to start GUI: {str(e)}")

if __name__ == "__main__":
    main()
