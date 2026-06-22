# Streamlit Configuration Files

This directory contains Streamlit configuration files for different environments.

## Files

### `config.toml` - Local Development Configuration
**Use this for local development on your machine.**

Key settings:
- `server.address = "localhost"` - Binds to localhost only
- `server.headless = false` - Opens browser automatically
- Optimized for development workflow

**To run locally:**
```bash
streamlit run app.py(if not working use - python -m streamlit run app.py)
```
App will open at: `http://localhost:8501`

### `config.production.toml` - Production Configuration Template
**Use this for production deployments (Docker, Cloud, etc.).**

Key settings:
- `server.address = "0.0.0.0"` - Accepts connections from all interfaces
- `server.headless = true` - Runs without opening browser
- Optimized for server environments

**To deploy to production:**
1. Copy production config:
   ```bash
   cp .streamlit/config.production.toml .streamlit/config.toml
   ```
2. Deploy your application

## Common Issues

### Issue: Browser shows "This site can't be reached" at 0.0.0.0:8501
**Cause:** Using production configuration (0.0.0.0) for local development.

**Solution:** Ensure `config.toml` has:
```toml
[server]
address = "localhost"
headless = false
```

### Issue: Docker container not accessible from host
**Cause:** Using localhost configuration in Docker.

**Solution:** Use production configuration with:
```toml
[server]
address = "0.0.0.0"
headless = true
```

## Configuration Differences

| Setting | Local Development | Production |
|---------|------------------|------------|
| `server.address` | `"localhost"` | `"0.0.0.0"` |
| `server.headless` | `false` | `true` |
| `client.showErrorDetails` | `true` | `false` |

## Why Different Configurations?

### localhost (127.0.0.1)
- Only accessible from your local machine
- Secure for development
- Browser can connect directly
- **Use for:** Local development

### 0.0.0.0
- Accepts connections from any network interface
- Required for Docker containers
- Required for cloud deployments
- Allows external access
- **Use for:** Production, Docker, Cloud platforms

## More Information

See [DEPLOYMENT_GUIDE.md](../docs/DEPLOYMENT_GUIDE.md) for detailed deployment instructions.