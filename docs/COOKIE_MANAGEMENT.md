# Cookie Management System

The Edge Weekly scraper now features an automated cookie management system that eliminates the need for manual cookie copying and pasting from the browser's network tab.

## How It Works

The system automatically:
1. **Saves cookies** after successful login
2. **Loads cookies** on subsequent runs to avoid re-login
3. **Validates cookies** to ensure they're still valid
4. **Falls back to manual login** when cookies expire or are invalid

## Benefits

- ✅ **Zero manual intervention** - No more copying cookies from browser
- ✅ **Docker-friendly** - Works seamlessly in containerized environments
- ✅ **Persistent sessions** - Maintains authentication across runs
- ✅ **Self-healing** - Automatically re-authenticates when needed
- ✅ **Secure** - Cookies stored separately from configuration

## File Structure

```
session/                          # Session data directory (Docker volume)
├── edge_cookies.json            # Saved authentication cookies
└── session_state.json           # Login timestamps and state tracking
```

## Configuration Changes

The manual `cookie` field has been removed from `config.yaml`:

**Before:**
```yaml
edge:
    url: 'https://digital.theedgemalaysia.com/'
    username: 'your_username'
    password: 'your_password'
    cookie: 'vn=7FYPt42dJ8Q%3D; extvn=bNhDAnhWzF8%3D; ...'  # Manual cookie
```

**After:**
```yaml
edge:
    url: 'https://digital.theedgemalaysia.com/'
    username: 'your_username'
    password: 'your_password'
    # Cookies now managed automatically
```

## Docker Integration

The `docker-compose.yml` now includes a session volume:

```yaml
volumes:
  - ./session:/app/session    # Cookie storage
```

This ensures cookies persist across container restarts while keeping them out of the container filesystem.

## Cookie Management Utility

Use the included utility script for cookie management:

```bash
# Show current session information
python scripts/cookie_manager.py info

# Test authentication with current cookies
python scripts/cookie_manager.py test

# Force fresh login and save new cookies
python scripts/cookie_manager.py login

# Clear all saved cookies
python scripts/cookie_manager.py clear
```

## How Authentication Works

### First Run (No Cookies)
1. Navigate to Edge Weekly website
2. Attempt to load cookies (none found)
3. Perform manual login with username/password
4. Save cookies after successful authentication
5. Continue with scraping

### Subsequent Runs (Cookies Exist)
1. Navigate to Edge Weekly website
2. Load saved cookies
3. Validate cookies by checking for login indicator
4. If valid: Continue with scraping
5. If invalid: Fall back to manual login and save new cookies

## Troubleshooting

### Issue: "Cookies appear to be invalid"
**Solution:** Run `python scripts/cookie_manager.py login` to force fresh authentication

### Issue: "No cookies found"
**Solution:** This is normal for first run. The system will automatically login and save cookies.

### Issue: Authentication fails repeatedly
**Solution:** 
1. Check your username/password in `config.yaml`
2. Clear cookies: `python scripts/cookie_manager.py clear`
3. Run fresh login: `python scripts/cookie_manager.py login`

### Issue: Docker container can't save cookies
**Solution:** Ensure the session volume is properly mounted in `docker-compose.yml`

## Security Considerations

- **Cookie Storage**: Cookies are stored in JSON format in the `session/` directory
- **Gitignore**: The `session/` directory is excluded from version control
- **Docker Volumes**: Cookies persist in host filesystem, not in container
- **Expiration**: Cookies automatically expire after 7 days and trigger re-authentication

## Migration from Manual Cookies

If you were previously using manual cookies:

1. **Remove the cookie field** from your `config.yaml`
2. **Run the scraper** - it will automatically login and save cookies
3. **Verify functionality** with `python scripts/cookie_manager.py test`

The system will work exactly the same but without any manual intervention required.

## Docker Deployment

For production Docker deployment:

```bash
# Build and run with persistent session
docker-compose up --build

# Check cookie status (from host)
python scripts/cookie_manager.py info

# Clear cookies if needed
python scripts/cookie_manager.py clear
```

The session data persists across container recreations, ensuring seamless operation in production environments.
