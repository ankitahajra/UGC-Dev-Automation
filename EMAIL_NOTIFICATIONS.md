# Email Notifications Guide

## Overview

The Azure Function Auto-Diagnose and Auto-Fix Pipeline now includes **comprehensive email notifications** that keep your team informed at every stage of the automated failure resolution process.

## 📧 What Gets Sent

### 1. **Failure Detection Email** 🚨
**Sent when:** A function failure is detected

**Contains:**
- Function name
- Invocation/Operation ID
- Timestamp
- Exception message
- Stack trace (if available)
- Notification that automated diagnosis has been triggered

**Subject:** `🚨 Azure Function Failure: [Function Name]`

---

### 2. **Analysis Complete Email** ✅
**Sent when:** ICA completes root cause analysis

**Contains:**
- **Root Cause Analysis:**
  - Category (code/infrastructure/configuration)
  - Summary of the issue
  - Confidence level (percentage)
  
- **Recommended Fixes:**
  - Types of fixes available (code/infrastructure/config)
  - Brief description of each fix
  
- **Risk Assessment:**
  - Overall risk level (low/medium/high)
  - Impact scope
  - Testing requirements
  - Approval requirements
  
- **Next Steps:**
  - Detailed action items
  - What will happen next in the pipeline

**Subject:** `✅ Analysis Complete: [Function Name]`

---

### 3. **Pull Request Created Email** 🔀
**Sent when:** BOB automation creates a pull request

**Contains:**
- Function name
- Branch name
- Types of fixes applied
- **Pull Request URL** (clickable link)
- Call to action for review and approval

**Subject:** `🔀 Pull Request Created: [Function Name]`

---

### 4. **Rollback Notification Email** ⚠️
**Sent when:** Deployment fails and rollback is triggered

**Contains:**
- Function name
- Reason for rollback
- Timestamp
- Instructions for investigation

**Subject:** `⚠️ Rollback Triggered: [Function Name]`

---

## 🔧 Configuration

### Step 1: Configure SMTP Settings

Edit your `.env` file with your SMTP server details:

```bash
# Email Notifications
SMTP_SERVER=smtp.gmail.com          # Your SMTP server
SMTP_USERNAME=your-email@example.com # SMTP username
SMTP_PASSWORD=your-email-password    # SMTP password or app password
```

### Step 2: Configure Recipients

Edit `config.yaml` to set recipient email addresses:

```yaml
notifications:
  email:
    enabled: true
    smtp_server: "${SMTP_SERVER}"
    smtp_port: 587
    smtp_username: "${SMTP_USERNAME}"
    smtp_password: "${SMTP_PASSWORD}"
    from_address: "autofix@example.com"
    to_addresses:
      - "ankita.hajra@ibm.com"
      - "team@example.com"
      - "devops@example.com"
```

### Step 3: Enable/Disable Notifications

To disable email notifications, set `enabled: false` in `config.yaml`:

```yaml
notifications:
  email:
    enabled: false  # Disables all email notifications
```

---

## 📨 SMTP Provider Examples

### Gmail
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password, not regular password
```

**Note:** Enable "Less secure app access" or use an App Password for Gmail.

### Office 365 / Outlook
```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-password
```

### SendGrid
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

### AWS SES
```bash
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

---

## 🎨 Email Format

All emails are sent in **both plain text and HTML formats** for maximum compatibility:

- **Plain Text:** For email clients that don't support HTML
- **HTML:** Rich formatting with colors, sections, and styling for better readability

### HTML Email Features:
- ✅ Color-coded headers (red for failures, green for success, etc.)
- 📦 Organized sections with clear visual hierarchy
- 🔗 Clickable links (e.g., Pull Request URLs)
- 📊 Formatted data boxes for easy scanning
- 🎯 Clear call-to-action buttons

---

## 🔐 Security Best Practices

1. **Use App Passwords:** For Gmail and similar services, use app-specific passwords instead of your main password

2. **Environment Variables:** Never commit SMTP credentials to version control. Always use environment variables

3. **Encryption:** The system uses STARTTLS for secure email transmission

4. **Restricted Access:** Only configure SMTP credentials for authorized personnel

---

## 🧪 Testing Email Notifications

### Test Email Configuration

You can test your email configuration by running:

```python
from src.email_notifier import EmailNotifier
from src.config_manager import get_config

config = get_config('config.yaml')
notifier = EmailNotifier(config)

# Test with a sample failure
test_failure = {
    'function_name': 'TestFunction',
    'operation_id': 'test-123',
    'timestamp': '2026-05-18T10:00:00Z',
    'error': {
        'message': 'Test error message',
        'stack_trace': 'Test stack trace'
    }
}

success = notifier.send_failure_notification(test_failure)
print(f"Email sent: {success}")
```

---

## 📋 Email Notification Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Failure Detected                          │
│                          ↓                                   │
│              📧 Email 1: Failure Alert                       │
│                          ↓                                   │
│                  Collect Diagnostics                         │
│                          ↓                                   │
│                   ICA Analysis                               │
│                          ↓                                   │
│         📧 Email 2: Analysis Complete                        │
│                          ↓                                   │
│                  BOB Automation                              │
│                          ↓                                   │
│           📧 Email 3: PR Created                             │
│                          ↓                                   │
│              Manual Review & Approval                        │
│                          ↓                                   │
│                    Deployment                                │
│                          ↓                                   │
│         ✅ Success  OR  ⚠️ Failure                           │
│                          ↓                                   │
│              (If failure: Rollback)                          │
│                          ↓                                   │
│         📧 Email 4: Rollback Alert                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Customization

### Custom Email Templates

You can customize email templates by modifying the methods in `src/email_notifier.py`:

- `send_failure_notification()` - Failure alert template
- `send_analysis_complete_notification()` - Analysis results template
- `send_pr_created_notification()` - PR creation template
- `send_rollback_notification()` - Rollback alert template

### Adding More Recipients

Add more email addresses to the `to_addresses` list in `config.yaml`:

```yaml
to_addresses:
  - "ankita.hajra@ibm.com"
  - "team-lead@example.com"
  - "devops-team@example.com"
  - "on-call@example.com"
```

### Conditional Notifications

You can configure which events trigger emails by modifying the pipeline orchestrator logic in `src/pipeline_orchestrator.py`.

---

## 🐛 Troubleshooting

### Email Not Sending

1. **Check SMTP credentials:**
   ```bash
   python -c "from src.email_notifier import EmailNotifier; from src.config_manager import get_config; print(EmailNotifier(get_config('config.yaml')).enabled)"
   ```

2. **Verify SMTP server connectivity:**
   ```bash
   telnet smtp.gmail.com 587
   ```

3. **Check logs:**
   ```bash
   grep "email" logs/pipeline.log
   ```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Authentication failed" | Use app password instead of regular password |
| "Connection timeout" | Check firewall rules and SMTP server address |
| "Email not received" | Check spam folder, verify recipient addresses |
| "SSL/TLS error" | Ensure SMTP port is correct (usually 587 for STARTTLS) |

---

## 📊 Email Metrics

The system logs all email sending attempts. You can track:

- Number of emails sent
- Success/failure rates
- Delivery times
- Recipient engagement (if using email tracking services)

Check logs at: `logs/pipeline.log`

---

## 🔄 Integration with Workflow

The email notifications are fully integrated with the workflow defined in `workflow.yaml`:

```yaml
notifications:
  email:
    enabled: true
    recipients:
      - ankita.hajra@ibm.com
    triggers:
      - jobFailure          # ✅ Implemented
      - analysisCompleted   # ✅ Implemented
    contents:
      include:
        - functionName      # ✅ Included
        - invocationId      # ✅ Included
        - exceptionMessage  # ✅ Included
        - rootCauseSummary  # ✅ Included
        - recommendedFix    # ✅ Included
```

---

## 📚 Related Documentation

- [README.md](README.md) - Main project documentation
- [workflow.yaml](workflow.yaml) - Complete workflow specification
- [config.yaml](config.yaml) - Configuration reference
- [SETUP.md](SETUP.md) - Setup instructions

---

**Made with Bob 🤖**