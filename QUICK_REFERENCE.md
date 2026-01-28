# Quick Reference Guide: Login System Changes

## Before vs After

### Login Screen

**BEFORE:**
```
┌─────────────────────────────────────┐
│  Please enter your license key to  │
│  activate CourseSmith AI            │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ CS-XXXX-XXXX                │   │
│  └─────────────────────────────┘   │
│                                     │
│       [🔓 Activate License]        │
└─────────────────────────────────────┘
```

**AFTER:**
```
┌─────────────────────────────────────┐
│  Please enter your email and       │
│  license key to activate            │
│                                     │
│  Email Address                      │
│  ┌─────────────────────────────┐   │
│  │ your@email.com              │   │
│  └─────────────────────────────┘   │
│                                     │
│  License Key                        │
│  ┌─────────────────────────────┐   │
│  │ CS-XXXX-XXXX                │   │
│  └─────────────────────────────┘   │
│                                     │
│       [🔓 Activate License]        │
└─────────────────────────────────────┘
```

### Validation Flow

**BEFORE:**
```
1. User enters license key
2. Query database: WHERE license_key = ?
3. Check if HWID in used_hwids array
4. Add HWID to array if space available
5. Return success or "Device Limit Reached"
```

**AFTER:**
```
1. User enters email + license key
2. Validate email format (@, domain)
3. Query database: WHERE email = ? AND license_key = ?
4. If not found → "Invalid Credentials"
5. Check HWID scenarios:
   - A: stored == current → ALLOW
   - B: stored is NULL → UPDATE + ALLOW
   - C: stored != current → "Device Limit Reached"
```

### Database Schema

**BEFORE:**
```sql
licenses {
  email: text
  license_key: text
  used_hwids: jsonb[]  -- Array of HWIDs
  max_devices: integer
}
```

**AFTER:**
```sql
licenses {
  email: text
  license_key: text
  hwid: text (nullable)  -- Single HWID
  device_limit: integer (default 1)
}
```

### Admin Panel - Reset HWID

**BEFORE:**
```python
# Reset used_hwids array
client.table("licenses").update({
    "used_hwids": []
}).eq("license_key", key).execute()
```

**AFTER:**
```python
# Set hwid to NULL
client.table("licenses").update({
    "hwid": None
}).eq("license_key", key).execute()
```

## Key Improvements

### 1. Security
- ✅ Validates BOTH email AND license key
- ✅ Case-insensitive HWID comparison
- ✅ Email format validation
- ✅ Consistent error messages ("Invalid Credentials")

### 2. User Experience
- ✅ Two-field login (email + key)
- ✅ Return key works from both fields
- ✅ Clear validation error messages
- ✅ Clipboard support (Ctrl+C/V/A)

### 3. Admin Control
- ✅ Right-click "Reset HWID" on any license
- ✅ Sets HWID to NULL (clean state)
- ✅ Confirmation dialog before reset
- ✅ Automatic list refresh after reset

### 4. Code Quality
- ✅ Module-level imports
- ✅ No unused variables
- ✅ Security documentation
- ✅ Case-insensitive comparisons

## Testing Scenarios

### Scenario A: Same Device Re-login
```
User logs in with email + key
HWID matches stored HWID
✅ Result: "License is valid and activated on this device"
```

### Scenario B: First Activation
```
User logs in with email + key
HWID is NULL in database
✅ Result: HWID updated, "License activated successfully"
```

### Scenario C: Different Device
```
User tries to log in with email + key
HWID doesn't match stored HWID
❌ Result: "Device Limit Reached"
```

### Admin Reset Flow
```
1. Right-click on license row
2. Select "Reset HWID"
3. Confirm in dialog
4. HWID set to NULL
5. User can now activate on new device
```

## Error Messages

| Situation | Old Message | New Message |
|-----------|-------------|-------------|
| No email entered | N/A | "Please enter your email address" |
| Invalid email format | N/A | "Please enter a valid email address" |
| No license key | "Please enter a license key" | Same |
| Wrong email/key combo | "Invalid license key" | "Invalid Credentials" |
| Different device | "Device Limit Reached. Max: X..." | "Device Limit Reached" |
| Same device | "License is valid..." | Same |
| First activation | "License activated successfully! Device X/Y..." | "License activated successfully on this device" |

## Migration Notes

If upgrading from the old system:

1. **Database Migration Required**:
   ```sql
   -- Add hwid column
   ALTER TABLE licenses ADD COLUMN hwid TEXT;
   
   -- Migrate first HWID from used_hwids array
   UPDATE licenses 
   SET hwid = used_hwids[1] 
   WHERE jsonb_array_length(used_hwids) > 0;
   
   -- Optional: Remove old columns
   -- ALTER TABLE licenses DROP COLUMN used_hwids;
   -- ALTER TABLE licenses DROP COLUMN max_devices;
   ```

2. **Existing Users**: Will need to re-activate with email + license key
3. **Admin Panel**: Can reset HWIDs to allow re-activation

## Support Contacts

For issues:
- Login problems → Verify email matches database exactly
- Device limit → Admin can reset HWID via right-click menu
- HWID mismatch → Case-insensitive comparison should handle variations
