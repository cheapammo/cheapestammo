#!/usr/bin/env python3
"""
Email Monitor for Ammunition Deals
Monitors email inbox for deals from ammunition retailers
"""

import imaplib
import email
from email.header import decode_header
import re
import json
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional, Tuple
import html2text

from config import EMAIL_CONFIG, DEAL_CONFIG
from database import DatabaseManager, EmailDeal, EmailMonitorLog

class EmailMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = DatabaseManager()
        self.mail = None
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        
    def connect(self) -> bool:
        """Connect to email server"""
        try:
            self.logger.info(f"Connecting to {EMAIL_CONFIG['imap_server']}...")
            
            # Connect to the server
            self.mail = imaplib.IMAP4_SSL(
                EMAIL_CONFIG['imap_server'], 
                EMAIL_CONFIG['imap_port']
            )
            
            # Login
            self.mail.login(
                EMAIL_CONFIG['email_address'], 
                EMAIL_CONFIG['email_password']
            )
            
            self.logger.info("Successfully connected to email server")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to email server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except:
                pass
    
    def get_unprocessed_emails(self, folder: str = 'INBOX') -> List[str]:
        """Get list of unprocessed email IDs"""
        try:
            # Select the folder
            self.mail.select(folder)
            
            # Search for unread emails from known retailers
            search_criteria = self._build_search_criteria()
            result, data = self.mail.search(None, search_criteria)
            
            if result == 'OK':
                email_ids = data[0].split()
                self.logger.info(f"Found {len(email_ids)} unprocessed emails")
                return email_ids
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting emails: {e}")
            return []
    
    def _build_search_criteria(self) -> str:
        """Build IMAP search criteria for retailer emails"""
        # Start with unread emails
        criteria_parts = ['(UNSEEN']
        
        # Add OR conditions for each retailer domain
        if DEAL_CONFIG['retailer_domains']:
            from_parts = []
            for domain in DEAL_CONFIG['retailer_domains'].keys():
                from_parts.append(f'FROM "{domain}"')
            
            if from_parts:
                criteria_parts.append(' OR '.join(from_parts))
        
        criteria_parts.append(')')
        return ' '.join(criteria_parts)
    
    def process_email(self, email_id: str) -> Optional[Dict]:
        """Process a single email and extract deal information"""
        try:
            # Fetch the email
            result, data = self.mail.fetch(email_id, '(RFC822)')
            if result != 'OK':
                return None
            
            # Parse email
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract basic information
            email_data = self._extract_email_metadata(msg)
            
            # Extract email content
            email_data['html_content'], email_data['text_content'] = self._extract_content(msg)
            
            # Identify retailer
            email_data['retailer'] = self._identify_retailer(email_data['sender'])
            
            # Extract deal information
            if email_data['retailer']:
                deal_info = self._extract_deal_info(email_data)
                email_data.update(deal_info)
                
                # Calculate confidence score
                email_data['confidence_score'] = self._calculate_confidence(email_data)
                
                # Save to database if confidence is high enough
                if email_data['confidence_score'] >= 0.5:
                    self._save_deal(email_data)
                    
                    # Mark as read if configured
                    if EMAIL_CONFIG['mark_as_read']:
                        self.mail.store(email_id, '+FLAGS', '\\Seen')
                    
                    return email_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing email {email_id}: {e}")
            return None
    
    def _extract_email_metadata(self, msg) -> Dict:
        """Extract basic email metadata"""
        # Decode subject
        subject = ""
        if msg['Subject']:
            subject_parts = decode_header(msg['Subject'])
            subject = ' '.join([
                part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
                for part, encoding in subject_parts
            ])
        
        # Get sender
        sender = msg['From']
        
        # Get date
        date_str = msg['Date']
        try:
            # Parse various date formats
            from email.utils import parsedate_to_datetime
            received_date = parsedate_to_datetime(date_str)
        except:
            received_date = datetime.now()
        
        # Get message ID
        message_id = msg['Message-ID'] or f"no-id-{datetime.now().timestamp()}"
        
        return {
            'email_id': message_id,
            'subject': subject,
            'sender': sender,
            'received_date': received_date
        }
    
    def _extract_content(self, msg) -> Tuple[str, str]:
        """Extract HTML and text content from email"""
        html_content = ""
        text_content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                
                try:
                    body = part.get_payload(decode=True)
                    if body:
                        if content_type == "text/plain":
                            text_content = body.decode('utf-8', errors='ignore')
                        elif content_type == "text/html":
                            html_content = body.decode('utf-8', errors='ignore')
                except:
                    continue
        else:
            # Single part message
            content_type = msg.get_content_type()
            body = msg.get_payload(decode=True)
            
            if body:
                if content_type == "text/plain":
                    text_content = body.decode('utf-8', errors='ignore')
                elif content_type == "text/html":
                    html_content = body.decode('utf-8', errors='ignore')
        
        # Convert HTML to text if we only have HTML
        if html_content and not text_content:
            text_content = self.html_converter.handle(html_content)
        
        return html_content, text_content
    
    def _identify_retailer(self, sender: str) -> Optional[str]:
        """Identify retailer from sender email"""
        sender_lower = sender.lower()
        
        for domain, retailer_name in DEAL_CONFIG['retailer_domains'].items():
            if domain in sender_lower:
                return retailer_name
        
        return None
    
    def _extract_deal_info(self, email_data: Dict) -> Dict:
        """Extract deal information from email content"""
        content = email_data['text_content'] + ' ' + email_data['subject']
        
        deal_info = {
            'calibers': [],
            'prices': [],
            'discount_percent': None,
            'promo_code': None,
            'deal_urls': [],
            'deal_title': email_data['subject'],
            'deal_description': None
        }
        
        # Extract calibers
        deal_info['calibers'] = self._extract_calibers(content)
        
        # Extract prices
        deal_info['prices'] = self._extract_prices(content)
        
        # Extract discount percentage
        deal_info['discount_percent'] = self._extract_discount(content)
        
        # Extract promo codes
        deal_info['promo_code'] = self._extract_promo_code(content)
        
        # Extract URLs
        deal_info['deal_urls'] = self._extract_urls(email_data['html_content'])
        
        # Extract deal description (first paragraph or summary)
        deal_info['deal_description'] = self._extract_description(content)
        
        return deal_info
    
    def _extract_calibers(self, text: str) -> List[str]:
        """Extract ammunition calibers from text"""
        calibers_found = []
        text_upper = text.upper()
        
        # Check for each standardized caliber
        from config import DATA_CONFIG
        for standard_caliber, variations in DATA_CONFIG['caliber_mapping'].items():
            for variation in variations:
                if variation.upper() in text_upper:
                    if standard_caliber not in calibers_found:
                        calibers_found.append(standard_caliber)
                    break
        
        return calibers_found
    
    def _extract_prices(self, text: str) -> List[float]:
        """Extract prices from text"""
        prices = []
        
        for pattern in DEAL_CONFIG['parse_patterns']['price']:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    if 0.01 <= price <= 10000:  # Reasonable price range
                        prices.append(price)
                except:
                    continue
        
        return list(set(prices))  # Remove duplicates
    
    def _extract_discount(self, text: str) -> Optional[float]:
        """Extract discount percentage from text"""
        for pattern in DEAL_CONFIG['parse_patterns']['discount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        return None
    
    def _extract_promo_code(self, text: str) -> Optional[str]:
        """Extract promo codes from text"""
        # Common patterns for promo codes
        patterns = [
            r'(?:code|coupon|promo):\s*([A-Z0-9]{4,20})',
            r'use\s+code\s+([A-Z0-9]{4,20})',
            r'enter\s+([A-Z0-9]{4,20})',
            r'\b([A-Z]{2,}[0-9]{2,})\b'  # Generic pattern like SAVE20
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).upper()
                # Validate it looks like a promo code
                if 4 <= len(code) <= 20 and re.match(r'^[A-Z0-9]+$', code):
                    return code
        
        return None
    
    def _extract_urls(self, html_content: str) -> List[str]:
        """Extract URLs from HTML content"""
        urls = []
        
        if not html_content:
            return urls
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                url = link['href']
                
                # Filter for product/deal URLs
                if any(keyword in url.lower() for keyword in ['product', 'deal', 'ammo', 'ammunition']):
                    urls.append(url)
                
                # Limit to reasonable number
                if len(urls) >= 10:
                    break
        except:
            pass
        
        return urls
    
    def _extract_description(self, text: str) -> str:
        """Extract a brief description of the deal"""
        # Look for deal-related sentences
        sentences = text.split('.')
        deal_sentences = []
        
        for sentence in sentences[:10]:  # Check first 10 sentences
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in DEAL_CONFIG['keywords']):
                deal_sentences.append(sentence.strip())
                
                if len(deal_sentences) >= 3:
                    break
        
        description = '. '.join(deal_sentences)
        if description:
            description += '.'
        
        # Limit length
        if len(description) > 500:
            description = description[:497] + '...'
        
        return description or text[:500]
    
    def _calculate_confidence(self, email_data: Dict) -> float:
        """Calculate confidence score for deal quality"""
        score = 0.0
        factors = 0
        
        # Check if from known retailer
        if email_data.get('retailer'):
            score += 0.2
            factors += 1
        
        # Check for deal keywords in subject
        subject_lower = email_data['subject'].lower()
        keyword_count = sum(1 for keyword in DEAL_CONFIG['keywords'] if keyword in subject_lower)
        if keyword_count > 0:
            score += min(0.2, keyword_count * 0.05)
            factors += 1
        
        # Check for calibers
        if email_data.get('calibers'):
            score += 0.2
            factors += 1
        
        # Check for prices
        if email_data.get('prices'):
            score += 0.15
            factors += 1
        
        # Check for discount
        if email_data.get('discount_percent'):
            if email_data['discount_percent'] >= DEAL_CONFIG['minimum_discount_percent']:
                score += 0.15
            factors += 1
        
        # Check for URLs
        if email_data.get('deal_urls'):
            score += 0.1
            factors += 1
        
        # Normalize score
        if factors > 0:
            return min(1.0, score)
        
        return 0.0
    
    def _save_deal(self, email_data: Dict):
        """Save deal to database"""
        session = self.db.get_session()
        try:
            # Check if already exists
            existing = session.query(EmailDeal).filter_by(
                email_id=email_data['email_id']
            ).first()
            
            if existing:
                self.logger.info(f"Email {email_data['email_id']} already processed")
                return
            
            # Create new deal record
            deal = EmailDeal(
                email_id=email_data['email_id'],
                sender=email_data['sender'],
                subject=email_data['subject'],
                received_date=email_data['received_date'],
                retailer_name=email_data.get('retailer'),
                deal_title=email_data.get('deal_title'),
                deal_description=email_data.get('deal_description'),
                calibers=json.dumps(email_data.get('calibers', [])),
                prices=json.dumps(email_data.get('prices', [])),
                discount_percent=email_data.get('discount_percent'),
                promo_code=email_data.get('promo_code'),
                email_html=email_data.get('html_content', ''),
                email_text=email_data.get('text_content', ''),
                confidence_score=email_data.get('confidence_score', 0),
                deal_urls=json.dumps(email_data.get('deal_urls', []))
            )
            
            session.add(deal)
            session.commit()
            
            self.logger.info(f"Saved deal from {email_data.get('retailer')}: {email_data['subject']}")
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error saving deal: {e}")
        finally:
            session.close()
    
    def run_monitoring_cycle(self) -> Dict:
        """Run one monitoring cycle"""
        log_entry = {
            'started_at': datetime.now(),
            'emails_checked': 0,
            'deals_found': 0,
            'errors': []
        }
        
        try:
            # Connect to email
            if not self.connect():
                log_entry['errors'].append("Failed to connect to email server")
                log_entry['status'] = 'failed'
                return log_entry
            
            # Get unprocessed emails
            email_ids = self.get_unprocessed_emails()
            log_entry['emails_checked'] = len(email_ids)
            
            # Process each email
            for email_id in email_ids:
                result = self.process_email(email_id)
                if result:
                    log_entry['deals_found'] += 1
                
                # Small delay between emails
                time.sleep(1)
            
            log_entry['status'] = 'success'
            
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
            log_entry['errors'].append(str(e))
            log_entry['status'] = 'failed'
        
        finally:
            self.disconnect()
            log_entry['completed_at'] = datetime.now()
            
            # Log to database
            self._log_monitoring_cycle(log_entry)
        
        return log_entry
    
    def _log_monitoring_cycle(self, log_entry: Dict):
        """Log monitoring cycle to database"""
        session = self.db.get_session()
        try:
            log = EmailMonitorLog(
                started_at=log_entry['started_at'],
                completed_at=log_entry.get('completed_at'),
                emails_checked=log_entry['emails_checked'],
                deals_found=log_entry['deals_found'],
                errors=json.dumps(log_entry.get('errors', [])),
                status=log_entry.get('status', 'unknown')
            )
            session.add(log)
            session.commit()
        except Exception as e:
            self.logger.error(f"Error logging monitoring cycle: {e}")
        finally:
            session.close()
    
    def run_continuous(self):
        """Run continuous monitoring"""
        self.logger.info("Starting continuous email monitoring")
        
        while True:
            try:
                self.logger.info("Running monitoring cycle...")
                result = self.run_monitoring_cycle()
                
                self.logger.info(
                    f"Cycle complete: {result['emails_checked']} emails checked, "
                    f"{result['deals_found']} deals found"
                )
                
                # Wait for next cycle
                self.logger.info(f"Waiting {EMAIL_CONFIG['check_interval']} seconds until next check...")
                time.sleep(EMAIL_CONFIG['check_interval'])
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in continuous monitoring: {e}")
                time.sleep(60)  # Wait a minute before retrying


def main():
    """Main function for testing"""
    import logging
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create monitor
    monitor = EmailMonitor()
    
    # Run one cycle
    print("Running email monitoring cycle...")
    result = monitor.run_monitoring_cycle()
    
    print(f"\nResults:")
    print(f"- Emails checked: {result['emails_checked']}")
    print(f"- Deals found: {result['deals_found']}")
    print(f"- Status: {result['status']}")
    
    if result['errors']:
        print(f"- Errors: {result['errors']}")


if __name__ == "__main__":
    main()