# 📧 Email Monitor Setup Guide

This guide will help you set up the email monitoring system to automatically capture ammunition deals from retailer emails.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Email Settings

Create a `.env` file in the project root and add your email credentials:

```env
# Email Monitoring Configuration
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password
```

### 3. Set Up Email Access

#### For Gmail:
1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the generated password
3. Use this app-specific password in your `.env` file

#### For Other Providers:
- **Outlook/Hotmail**: `EMAIL_IMAP_SERVER=outlook.office365.com`
- **Yahoo**: `EMAIL_IMAP_SERVER=imap.mail.yahoo.com`
- Most providers require app-specific passwords for security

### 4. Subscribe to Retailer Emails

Sign up for newsletters from these ammunition retailers:
- Bulk Ammo (bulkammo.com)
- SG Ammo (sgammo.com)
- Target Sports USA (targetsportsusa.com)
- Brownells (brownells.com)
- Palmetto State Armory (palmettostatearmory.com)
- MidwayUSA (midwayusa.com)
- Lucky Gunner (luckygunner.com)
- AmmoMan (ammoman.com)

## 🏃 Running the Email Monitor

### Test Run (Single Cycle)
```bash
python email_monitor.py
```

### Continuous Monitoring
```bash
python combined_monitor.py
```

This will run both email monitoring and web scraping continuously.

## 📊 Viewing Deals

Open `deals_dashboard.html` in your browser to view captured email deals.

## ⚙️ Configuration Options

Edit `config.py` to customize:

```python
EMAIL_CONFIG = {
    'check_interval': 300,  # Check every 5 minutes
    'mark_as_read': True,   # Mark processed emails as read
    'move_to_folder': 'Processed',  # Optional: move processed emails
}

DEAL_CONFIG = {
    'minimum_discount_percent': 10,  # Minimum discount to consider
    'keywords': [...],  # Deal detection keywords
    'retailer_domains': {...},  # Retailer email domains
}
```

## 🔍 How It Works

1. **Email Scanning**: Checks inbox for unread emails from known retailers
2. **Deal Detection**: Analyzes email content for:
   - Deal keywords (sale, discount, special, etc.)
   - Caliber mentions (9mm, .223, 5.56, etc.)
   - Prices and discounts
   - Promo codes
3. **Confidence Scoring**: Rates deal quality based on:
   - Retailer reliability
   - Keyword matches
   - Price information
   - Discount percentage
4. **Data Storage**: Saves deals to database with:
   - Full email content
   - Extracted deal information
   - Confidence score
   - Deal URLs

## 🛠️ Troubleshooting

### "Authentication Failed"
- Verify email address and password
- For Gmail, ensure you're using an app-specific password
- Check if IMAP is enabled in your email settings

### "No Emails Found"
- Verify you're subscribed to retailer newsletters
- Check spam/promotions folders
- Ensure emails are unread (or disable mark_as_read)

### "Deal Not Detected"
- Check confidence score threshold
- Add retailer domain to config
- Review deal keywords

## 📈 Advanced Features

### Email Filtering Rules
Create email filters to:
- Auto-label retailer emails
- Skip spam filtering
- Forward to dedicated inbox

### Deal Alerts
Set up notifications for:
- High-confidence deals (>90%)
- Specific calibers
- Large discounts (>25%)

### API Integration
The email deals can be accessed via API endpoints for integration with:
- Mobile apps
- Price alert systems
- Social media bots

## 🔒 Security Best Practices

1. **Use App-Specific Passwords**: Never use your main email password
2. **Dedicated Email**: Consider using a separate email for deal monitoring
3. **Environment Variables**: Keep credentials in `.env`, never commit to git
4. **Access Logs**: Monitor `email_monitor_logs` table for unusual activity

## 📝 Database Schema

The system creates two new tables:

### email_deals
- Stores all detected deals
- Links to retailer information
- Tracks deal validity periods
- Maintains full email content

### email_monitor_logs
- Records monitoring sessions
- Tracks emails processed
- Logs errors and issues

## 🚦 Monitoring Status

Check system health:
```sql
-- Recent monitoring activity
SELECT * FROM email_monitor_logs 
ORDER BY started_at DESC 
LIMIT 10;

-- Active deals
SELECT * FROM email_deals 
WHERE is_active = true 
ORDER BY confidence_score DESC;
```

## 📮 Adding New Retailers

To add a new retailer:

1. Add domain to `config.py`:
```python
'newretailer.com': 'New Retailer Name',
```

2. Subscribe to their newsletter

3. The system will automatically start processing their emails

## 🎯 Tips for Best Results

1. **Create Email Filters**: Set up Gmail filters to label retailer emails
2. **Monitor Spam**: Some deals might end up in spam - check regularly
3. **Optimize Keywords**: Add retailer-specific keywords if needed
4. **Regular Maintenance**: Clean up old emails monthly
5. **Track Performance**: Monitor which retailers send the best deals

## 🆘 Support

If you encounter issues:
1. Check `combined_monitor.log` for errors
2. Verify email connectivity with test script
3. Review database logs for processing history
4. Ensure all dependencies are installed

Happy deal hunting! 🎯