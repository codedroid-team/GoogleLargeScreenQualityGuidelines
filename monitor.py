#!/usr/bin/env python3
"""
Webpage Monitoring Script

Monitors content changes on multiple webpages and sends consolidated email notifications via SMTP
when changes are detected.

Features:
- Fetches webpage content from multiple URLs using requests with appropriate headers
- Parses HTML with BeautifulSoup to extract main content from each page
- Comparse content using difflib and detects changes
- Sends consolidated email notifications when content differs from stored version
- Handles various edge cases and error conditions
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import difflib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path


class WebPageMonitor:
    """
    A webpage monitoring class that fetches content, extracts main article content,
    compares with existing content. This class is now used as a helper by MultiWebPageMonitor.
    """
    
    def __init__(self, target_url, content_file_path):
        """
        Initialize the monitor with a target URL and content file.
        
        Args:
            target_url (str): The URL to monitor for changes
            content_file_path (str): Path to the local content file for comparison
        """
        self.target_url = target_url
        self.content_file_path = content_file_path
        
    def _setup_logger(self):
        """
        Set up logging configuration for the monitor.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger

    def fetch_html_content(self):
        """
        Fetch HTML content from the target URL with appropriate headers.
        
        Returns:
            str: HTML content if successful, None if failed
            
        Raises:
            requests.RequestException: If the request fails
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"Fetching content from {self.target_url}")
            response = requests.get(self.target_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching content from {self.target_url}: {str(e)}")
            return None

    def extract_main_content(self, html_content):
        """
        Extract main article content from HTML, removing navigation, sidebar and footer elements.
        
        Args:
            html_content (str): Raw HTML content
            
        Returns:
            str: Extracted content as plain text
        """
        if not html_content:
            return ""
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        unwanted_selectors = [
            'nav',
            'script', 
            'form',
            '[class*="footer"]',
            '[class*="sidebar"]', 
            '.ad',
            '.advertisement', 
            '.cookie-consent',
        ]
        
        for selector in unwanted_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()
        
        main_tag = soup.find('main')
        content_element = main_tag or soup.find('article') or soup.find('div', {'role': 'main'}) or soup.find('body')
        
        if content_element:
            # Preserve heading structure with line breaks
            headings = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            for heading in headings:
                tags = content_element.find_all(heading)
                for tag in tags:
                    tag.insert_before('\n')
                    tag.insert_after('\n')
            
            # Add spacing around paragraphs
            paras = content_element.find_all('p')
            for p in paras:
                p.insert_before('\n')
                p.insert_after('\n')
                
            # Add spacing around divs that might contain text
            divs = content_element.find_all('div')
            for d in divs:
                d.insert_before('\n')
                d.insert_after('\n')
                    
            text = content_element.get_text(separator='\n')
            
            # Normalize whitespace and blank lines
            lines = [line.strip() for line in text.splitlines()]
            cleaned_lines = []
            prev_empty = False
            
            for line in lines:
                if line == '':
                    if not prev_empty:
                        cleaned_lines.append('')
                        prev_empty = True
                elif line.strip():
                    cleaned_lines.append(line.strip())
                    prev_empty = False
            
            result = '\n'.join(cleaned_lines).strip()
            
            # Limit consecutive blank lines to 2 max
            while '\n\n\n' in result:
                result = result.replace('\n\n\n', '\n\n')
                
            return result
        else:
            body = soup.find('body')
            if body:
                return body.get_text(separator='\n').strip()
            else:
                return soup.get_text(separator='\n').strip()

    def read_existing_content(self):
        """
        Read the content from the existing content file.
        
        Returns:
            str: Existing content if file exists, empty string if file doesn't exist
        """
        try:
            file_path = Path(self.content_file_path)
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                return content
            else:
                logger = logging.getLogger(__name__)
                logger.info(f"Content file {self.content_file_path} does not exist, assuming first run")
                return ""
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error reading content file {self.content_file_path}: {str(e)}")
            return ""

    def write_content(self, content):
        """
        Write content to the content file.
        
        Args:
            content (str): Content to write to the file
        """
        try:
            file_path = Path(self.content_file_path)
            file_path.write_text(content, encoding='utf-8')
            logger = logging.getLogger(__name__)
            logger.info(f"Content saved to {self.content_file_path}")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error writing to content file {self.content_file_path}: {str(e)}")

    def compare_content(self, current_content, existing_content):
        """
        Compare current content with existing content using difflib.
        
        Args:
            current_content (str): New content to compare
            existing_content (str): Existing content to compare against
            
        Returns:
            bool: True if content differs, False otherwise
            str: Diff string showing the changes
        """
        if not existing_content.strip():
            logger = logging.getLogger(__name__)
            logger.info("First run: no existing content to compare")
            return True, f"First run - New content:\n\n{current_content[:500]}..."
        
        current_lines = current_content.splitlines(keepends=True)
        existing_lines = existing_content.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(
            existing_lines,
            current_lines,
            fromfile=f"Previous content ({len(existing_lines)} lines)",
            tofile=f"New content ({len(current_lines)} lines)",
            n=0,
            lineterm='\n'
        ))
        
        diff_str = ''.join(diff)
        has_changes = len(diff) > 0
        
        if has_changes:
            logger = logging.getLogger(__name__)
            logger.info(f"Content changes detected for {self.target_url}!")
        else:
            logger = logging.getLogger(__name__)
            logger.info(f"No content changes detected for {self.target_url}")
        
        return has_changes, diff_str


class MultiWebPageMonitor:
    """
    A multi webpage monitoring class that handles multiple URLs simultaneously.
    """
    
    def __init__(self):
        """
        Initialize the multi monitor with a list of target URLs and content files.
        """
        self.url_file_map = [
            {
                "url": "https://developer.android.com/docs/quality-guidelines/adaptive-app-quality",
                "file": "content.md"
            },
            {
                "url": "https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/tier-3",
                "file": "tier-3.md"
            },
            {
                "url": "https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/tier-2",
                "file": "tier-2.md"
            },
            {
                "url": "https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/tier-1",
                "file": "tier-1.md"
            },
            {
                "url": "https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/experiences/desktop",
                "file": "desktop.md"
            },
            {
                "url": "https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/experiences/foldables",
                "file": "foldables.md"
            },
            {
                "url": "https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/experiences/camera-audio",
                "file": "camera-audio.md"
            },
            {
                "url": "https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/experiences/stylus", 
                "file": "stylus.md"
            }
        ]
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """
        Set up logging configuration for the monitor.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    def send_email_notification(self, all_diffs):
        """
        Send consolidated email notification with all diff content via SMTP.
        
        Args:
            all_diffs (list): List of tuples containing URL, file name, and diff content
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        gmail_user = os.getenv('GMAIL_USER')
        gmail_pass = os.getenv('GMAIL_PASS')
        gmail_to = os.getenv('GMAIL_TO')
        
        if not gmail_user or not gmail_pass:
            self.logger.error("Email credentials not found in environment variables")
            self.logger.error("Please set GMAIL_USER and GMAIL_PASS environment variables")
            return False
        
        recipients = []
        if gmail_to:
            recipients = [email.strip() for email in gmail_to.split(',') if email.strip()]
        else:
            recipients = [gmail_user]
        
        subject = "Webpage Content Change Detected: Multiple Adaptive App Quality Guidelines"
        
        email_body_parts = ["Webpage Monitor has detected changes in the monitored content.\n"]
        urls_changed = [entry[0] for entry in all_diffs]
        email_body_parts.append(f"Changes detected in {len(urls_changed)} URLs:")
        
        for url, filename, diff_content in all_diffs:
            email_body_parts.append(f"\n{'='*50}")
            email_body_parts.append(f"URL: {url}")
            email_body_parts.append(f"File: {filename}")
            email_body_parts.append("="*50)
            email_body_parts.append(diff_content)
        
        email_body_parts.append("\n" + "="*50)
        email_body_parts.append("Automated message from WebPage Monitor.")
        
        email_body = "\n".join(email_body_parts)
        
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(email_body, 'plain'))
        
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(gmail_user, gmail_pass)
            
            text = msg.as_string()
            server.sendmail(gmail_user, recipients, text)
            
            server.quit()
            
            self.logger.info(f"Email notification sent successfully to {len(recipients)} recipients")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def run_monitor(self):
        """
        Execute the complete monitoring process for all URLs.
        
        Returns:
            bool: True if process completed successfully, False otherwise
        """
        try:
            all_results = []
            changes_detected = []
            first_runs_count = 0
        
            for entry in self.url_file_map:
                url = entry["url"]
                filename = entry["file"]
                
                self.logger.info(f"Processing URL: {url}")
                
                monitor = WebPageMonitor(url, filename)
                
                html_content = monitor.fetch_html_content()
                if html_content is None:
                    self.logger.error(f"Failed to fetch HTML content from {url}")
                    continue
                
                extracted_content = monitor.extract_main_content(html_content)
                if not extracted_content.strip():
                    self.logger.error(f"Extracted content is empty for {url}")
                    continue
                
                existing_content = monitor.read_existing_content()
                
                has_changes, diff_content = monitor.compare_content(extracted_content, existing_content)
                
                if has_changes:
                    is_first_run = not existing_content.strip()
                    all_results.append((url, filename, extracted_content))
                    
                    if is_first_run:
                        monitor.write_content(extracted_content)
                        self.logger.info(f"Initial content saved for {url} - first run complete")
                        first_runs_count += 1
                    else:
                        changes_detected.append((url, filename, diff_content))
                else:
                    self.logger.info(f"No changes detected for {url}, monitoring completed")
            
            if changes_detected:
                self.logger.info(f"Sending email notification for {len(changes_detected)} URLs with changes...")
                email_sent = self.send_email_notification(changes_detected)
                if email_sent:
                    for url, filename, diff_content in changes_detected:
                        for stored_url, stored_filename, stored_content in all_results:
                            if stored_url == url and stored_filename == filename:
                                monitor = WebPageMonitor(url, filename)
                                monitor.write_content(stored_content)
                                break
                    
                    self.logger.info(f"Content updated for {len(changes_detected)} URLs and notification sent")
                else:
                    self.logger.error("Failed to send notification, content not updated")
                    return False
            elif first_runs_count > 0:
                self.logger.info(f"Completed processing - {first_runs_count} initial content saves performed")
            else:
                self.logger.info("No changes to save across all URLs, monitoring completed")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Unexpected error during monitoring: {str(e)}")
            return False


def main():
    """
    Main entry point for the script.
    
    Monitors multiple Android developer pages for content changes.
    """
    monitor = MultiWebPageMonitor()
    
    success = monitor.run_monitor()
    
    if success:
        print("Monitoring completed successfully")
        return 0
    else:
        print("Monitoring failed")
        return 1


if __name__ == "__main__":
    exit(main())