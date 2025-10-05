#!/usr/bin/env python3
# Weekly review script for Sapphire Connect
# Run in venv: source ~/Projects/sapphire-connect-venv/bin/activate

import os
from datetime import datetime

# Read summary
with open('../docs/summary_detailed.md', 'r') as f:
    summary = f.read()

# Generate simple review
review = f"Weekly Pulse - {datetime.now().strftime('%Y-%m-%d')}\n\nSummary: {summary[:500]}...\n\nIdeas: 1. Refine Pet Wellness FitBark integration. 2. Prototype Family Bond calendar PWA. 3. PoolSync aquaponics pivot.\nNext: Update PoolScoutPro expansion."

# Email output using mail command (aligned with Postfix)
with open('/tmp/innovation_pulse_email.txt', 'w') as f:
    f.write(review)
echo "Sending alert from Sapphire Connect" | mail -s "Sapphire Connect Weekly Pulse" brian -a /tmp/innovation_pulse_email.txt
os.remove('/tmp/innovation_pulse_email.txt')

print("Review sent!")
