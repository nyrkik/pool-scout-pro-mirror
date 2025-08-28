#!/usr/bin/env python3
"""
Address Migration Script - Pool Scout Pro
Clean up malformed address data from PDF extraction

Fixes addresses like:
"2330 Hurley Way Facility City Sacramento Facility ZIP" 
to:
street_address: "2330 Hurley Way"
city: "Sacramento" 
address: "2330 Hurley Way, Sacramento"
"""

import sqlite3
import re
import sys
import os

# Add project path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def parse_messy_address(messy_address):
    """Parse address with 'Facility City' and 'Facility ZIP' artifacts"""
    if not messy_address or messy_address == 'Unknown':
        return None, None, None, None
    
    # Sacramento County PDF pattern
    pattern = r'^(.+?)\s*Facility City\s*(.+?)\s*Facility ZIP\s*(\d{5}(?:-\d{4})?)?.*$'
    match = re.match(pattern, messy_address.strip(), re.IGNORECASE)
    
    if match:
        street = match.group(1).strip()
        city = match.group(2).strip()
        zip_code = match.group(3).strip() if match.group(3) else None
        
        # Build clean full address
        full_address = street
        if city:
            full_address += f", {city}"
        if zip_code:
            full_address += f" {zip_code}"
        
        return street, city, zip_code, full_address
    
    # If no pattern match, return original as street address
    return messy_address, None, None, messy_address

def migrate_addresses():
    """Migrate all facility addresses"""
    db_path = 'data/reports.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all facilities with addresses
        cursor.execute("""
            SELECT id, name, address, street_address, city, zip_code 
            FROM facilities 
            WHERE address IS NOT NULL AND address != 'Unknown'
        """)
        
        facilities = cursor.fetchall()
        print(f"🔍 Found {len(facilities)} facilities to process")
        
        updated_count = 0
        unchanged_count = 0
        
        for facility in facilities:
            facility_id, name, current_address, current_street, current_city, current_zip = facility
            
            # Check if this looks like a messy address that needs cleaning
            if 'Facility City' in current_address or 'Facility ZIP' in current_address:
                # Parse the messy address
                street, city, zip_code, clean_address = parse_messy_address(current_address)
                
                # Update the database
                cursor.execute("""
                    UPDATE facilities 
                    SET street_address = ?, city = ?, zip_code = ?, address = ?
                    WHERE id = ?
                """, (street, city, zip_code, clean_address, facility_id))
                
                print(f"✅ {name[:30]:30} | {current_address[:50]:50} → {clean_address}")
                updated_count += 1
            else:
                # Address seems clean already
                unchanged_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 Migration Summary:")
        print(f"   ✅ Updated: {updated_count}")
        print(f"   ➖ Unchanged: {unchanged_count}")
        print(f"   📁 Total: {len(facilities)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting address migration...")
    success = migrate_addresses()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
