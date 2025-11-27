# LDAP/AD Integration - Quick Start Guide

## 🚀 Quick Installation (5 Minutes)

### Step 1: Install Packages

```bash
cd C:\trae\User-Access-Management-System
venv\Scripts\activate
pip install ldap3==2.9.1 pyasn1==0.6.0
```

### Step 2: Run Migrations

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

### Step 3: Restart Server

```bash
# Press CTRL+C to stop current server
python manage.py runserver
```

### Step 4: Access Configuration

1. Open browser: http://127.0.0.1:8000
2. Login as superuser
3. Navigate to: **Admin Menu** → **LDAP/AD Configuration**
   - Or go directly to: http://127.0.0.1:8000/accounts/ldap/configuration/

---

## ⚡ Quick Configuration

### For Active Directory:

```
✅ LDAP Integration Enabled
✅ Active Directory
✅ Cache LDAP Passwords

LDAP Server: ldap://your-dc.domain.com:389
Bind Username: CN=ServiceAccount,CN=Users,DC=domain,DC=com
Bind Password: your-password
Base DN: DC=domain,DC=com

LDAP Filter: (&(objectClass=user)(objectCategory=person))

Field Mapping (use lowercase):
- Username Field: samaccountname
- First Name Field: givenname
- Last Name Field: sn
- Email Field: mail
- Display Name Field: displayname
```

Click **Save LDAP Configuration**

### For OpenLDAP:

```
✅ LDAP Integration Enabled
⬜ Active Directory
✅ Cache LDAP Passwords

LDAP Server: ldap://ldap.example.com:389
Bind Username: cn=admin,dc=example,dc=com
Bind Password: your-password
Base DN: ou=users,dc=example,dc=com

LDAP Filter: (objectClass=inetOrgPerson)

Field Mapping:
- Username Field: uid
- First Name Field: givenName
- Last Name Field: sn
- Email Field: mail
```

Click **Save LDAP Configuration**

---

## 🧪 Quick Test

### Test Connection
```
Click: "Test Connection" button
Expected: ✓ LDAP connection successful
```

### Test Login
```
Username: [enter LDAP username]
Password: [enter LDAP password]
Click: "Test Login"
Expected: ✓ LDAP login successful for user: username (Full Name)
```

### Sync Users (Optional)
```
Click: "Sync All Users"
Expected: ✓ Synced XX users successfully, 0 errors
```

---

## 📝 Common Field Names Reference

### Active Directory (use lowercase):
- `samaccountname` - Username
- `givenname` - First Name
- `sn` - Last Name
- `displayname` - Display Name
- `mail` - Email
- `department` - Department
- `title` - Job Title
- `telephonenumber` - Phone
- `mobile` - Mobile
- `manager` - Manager DN
- `streetaddress` - Address
- `l` - City
- `st` - State
- `postalcode` - Postal Code
- `co` - Country
- `useraccountcontrol` - Active Flag

### OpenLDAP:
- `uid` - Username
- `givenName` - First Name
- `sn` - Last Name
- `displayName` - Display Name
- `mail` - Email
- `ou` - Department
- `title` - Job Title
- `telephoneNumber` - Phone
- `mobile` - Mobile

---

## 🔧 Troubleshooting

### Can't Connect?
```bash
# Test network connectivity
telnet your-dc.domain.com 389

# If using LDAPS:
telnet your-dc.domain.com 636
```

### Wrong Credentials?
- Verify service account username format
- Check account is not locked/disabled
- Ensure account has read permissions

### Users Can't Login?
- Check Base DN includes user location
- Verify LDAP filter matches users
- Test with known working credentials
- Check logs: Look for errors in terminal

### Fields Not Syncing?
- Use lowercase for AD field names
- Verify field exists in LDAP: `ldapsearch -x -b "CN=User,DC=domain,DC=com" -s base`
- Check service account can read attributes

---

## 📚 Full Documentation

For complete documentation, see:
- `doc/LDAP_AD_INTEGRATION.md` - Comprehensive guide
- `LDAP_IMPLEMENTATION_SUMMARY.md` - Technical details

---

## 🎯 Next Steps After Setup

1. ✅ Test connection
2. ✅ Test login with your account
3. ✅ Verify field mapping works
4. ✅ Optionally sync all users
5. ✅ Test user login from login page
6. ✅ Monitor for any errors
7. ✅ Update documentation with your specific settings

---

## 💡 Pro Tips

- **Always save before testing** - Configuration must be saved first
- **Use TLS in production** - Enable "Use TLS" or use ldaps://
- **Cache passwords** - Keeps working if LDAP server is down
- **Start simple** - Get basic login working, then add field mapping
- **Test incrementally** - Test connection → Test login → Test sync
- **Monitor logs** - Watch terminal for detailed error messages

---

## 🆘 Quick Help

**Configuration not saving?**
- Check you're logged in as superuser
- Look for error messages at top of page

**Can't see LDAP menu?**
- Must be superuser (is_superuser=True)
- Check URL directly: /accounts/ldap/configuration/

**Want to disable LDAP?**
- Uncheck "LDAP Integration Enabled"
- Save configuration
- Users will use local database authentication

**Reset to local auth?**
- Keep LDAP disabled
- Users with cached passwords can still login
- Or reset passwords using: `python manage.py changepassword username`

---

## ✅ Success Indicators

You've configured LDAP correctly when:
- ✓ Test Connection succeeds
- ✓ Test Login succeeds  
- ✓ User fields populated correctly
- ✓ Can login from main login page
- ✓ User account created/updated automatically

---

**Need Help?** Check the full documentation in `doc/LDAP_AD_INTEGRATION.md`

