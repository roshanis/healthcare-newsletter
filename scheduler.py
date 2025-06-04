#!/usr/bin/env python3
"""
Newsletter Scheduler
Handles automated weekly newsletter generation and distribution
"""

import schedule
import time
import logging
from datetime import datetime, timedelta
import os
import json
from newsletter_generator import NewsletterGenerator
from typing import Dict, Any
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('newsletter_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NewsletterScheduler:
    """Handles scheduling and automated execution of newsletter generation"""
    
    def __init__(self, config_path: str = "config.json"):
        load_dotenv()  # Load environment variables
        self.config = self.load_config(config_path)
        self.generator = NewsletterGenerator(config_path)
        self.is_running = False
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found. Using defaults.")
            return {
                "scheduling": {
                    "day_of_week": "monday",
                    "time": "09:00",
                    "timezone": "UTC"
                }
            }
    
    def generate_and_send_newsletter(self):
        """Generate newsletter and send via email"""
        try:
            logger.info("Starting scheduled newsletter generation...")
            
            # Generate newsletter content
            content = self.generator.create_newsletter()
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"healthcare_newsletter_{timestamp}.md"
            filepath = self.generator.save_newsletter(content, filename)
            
            # Send via email
            subject = f"Healthcare Weekly Newsletter - {datetime.now().strftime('%B %d, %Y')}"
            self.generator.send_email(content, subject)
            
            logger.info(f"Newsletter generation completed successfully. Saved to: {filepath}")
            
            # Log generation stats
            self.log_generation_stats(content)
            
        except Exception as e:
            logger.error(f"Error in scheduled newsletter generation: {e}")
            self.send_error_notification(str(e))
    
    def log_generation_stats(self, content: str):
        """Log statistics about the generated newsletter"""
        stats = {
            "generation_time": datetime.now().isoformat(),
            "content_length": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.split('\n'))
        }
        
        # Save stats to file
        stats_file = f"newsletters/stats_{datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs("newsletters", exist_ok=True)
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Newsletter stats: {stats}")
    
    def send_error_notification(self, error_message: str):
        """Send notification when newsletter generation fails"""
        error_subject = f"Newsletter Generation Error - {datetime.now().strftime('%Y-%m-%d')}"
        error_content = f"""
# Newsletter Generation Error

An error occurred during the scheduled newsletter generation:

**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Error:** {error_message}

Please check the logs for more details.

---
*Automated error notification from Healthcare Newsletter System*
"""
        
        try:
            self.generator.send_email(error_content, error_subject)
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    def setup_schedule(self):
        """Setup the weekly newsletter schedule"""
        scheduling_config = self.config.get("scheduling", {})
        day_of_week = scheduling_config.get("day_of_week", "monday").lower()
        time_str = scheduling_config.get("time", "09:00")
        
        # Map day names to schedule methods
        day_methods = {
            "monday": schedule.every().monday,
            "tuesday": schedule.every().tuesday,
            "wednesday": schedule.every().wednesday,
            "thursday": schedule.every().thursday,
            "friday": schedule.every().friday,
            "saturday": schedule.every().saturday,
            "sunday": schedule.every().sunday
        }
        
        if day_of_week not in day_methods:
            logger.error(f"Invalid day of week: {day_of_week}. Using Monday.")
            day_of_week = "monday"
        
        # Schedule the job
        day_methods[day_of_week].at(time_str).do(self.generate_and_send_newsletter)
        
        logger.info(f"Newsletter scheduled for every {day_of_week.title()} at {time_str}")
    
    def run_scheduler(self):
        """Run the scheduler (blocking)"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.setup_schedule()
        
        logger.info("Newsletter scheduler started. Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.is_running = False
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Newsletter scheduler stopped")
    
    def get_next_run_time(self) -> str:
        """Get the next scheduled run time"""
        jobs = schedule.get_jobs()
        if jobs:
            next_run = min(job.next_run for job in jobs)
            return next_run.strftime('%Y-%m-%d %H:%M:%S')
        return "No jobs scheduled"
    
    def manual_run(self):
        """Manually trigger newsletter generation"""
        logger.info("Manual newsletter generation triggered")
        self.generate_and_send_newsletter()
    
    def test_run(self) -> str:
        """Test run without sending emails - returns content"""
        logger.info("Test newsletter generation started")
        content = self.generator.create_newsletter()
        
        # Save test newsletter
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_newsletter_{timestamp}.md"
        filepath = self.generator.save_newsletter(content, filename)
        
        logger.info(f"Test newsletter saved to: {filepath}")
        return content

def main():
    """Main function for running the scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Healthcare Newsletter Scheduler')
    parser.add_argument('--config', default='config.json', 
                      help='Path to configuration file')
    parser.add_argument('--manual', action='store_true',
                      help='Run newsletter generation manually')
    parser.add_argument('--test', action='store_true',
                      help='Test newsletter generation without sending')
    parser.add_argument('--schedule', action='store_true',
                      help='Start the scheduler')
    parser.add_argument('--next', action='store_true',
                      help='Show next scheduled run time')
    
    args = parser.parse_args()
    
    scheduler = NewsletterScheduler(args.config)
    
    if args.test:
        content = scheduler.test_run()
        print("Test newsletter generated:")
        print("=" * 50)
        print(content[:1000] + "..." if len(content) > 1000 else content)
        print("=" * 50)
        
    elif args.manual:
        scheduler.manual_run()
        print("Manual newsletter generation completed")
        
    elif args.next:
        scheduler.setup_schedule()
        next_run = scheduler.get_next_run_time()
        print(f"Next scheduled run: {next_run}")
        
    elif args.schedule:
        scheduler.run_scheduler()
        
    else:
        print("Healthcare Newsletter Scheduler")
        print("Usage:")
        print("  --schedule    Start the automated scheduler")
        print("  --manual      Generate newsletter manually")
        print("  --test        Test newsletter generation")
        print("  --next        Show next scheduled run time")
        print("  --config      Specify config file path")

if __name__ == "__main__":
    main()