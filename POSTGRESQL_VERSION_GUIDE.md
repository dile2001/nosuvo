# PostgreSQL Version Compatibility Guide

## 📋 Version Requirements

### PostgreSQL Versions
- **Minimum**: PostgreSQL 9.6+ (required for SQLAlchemy compatibility)
- **Recommended**: PostgreSQL 17.x (stable, well-tested in production)
- **Latest**: PostgreSQL 18.x (newest features, but less production-tested)
- **Python**: 3.6+ (required for Alembic 1.13.1)

### Compatibility Matrix

| PostgreSQL Version | psycopg2-binary | SQLAlchemy | Alembic | Status |
|-------------------|-----------------|------------|---------|---------|
| 9.6+              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Supported |
| 10.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Supported |
| 11.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Supported |
| 12.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Supported |
| 13.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Supported |
| 14.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Supported |
| 15.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Supported |
| 16.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Supported |
| 17.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | **Recommended** |
| 18.x              | ✅ 2.9.9        | ✅ 2.0.23  | ✅ 1.13.1 | Latest |

## 🚀 Installation Commands

### macOS (Homebrew)
```bash
# Install PostgreSQL 17 (recommended)
brew install postgresql@17

# Install PostgreSQL 18 (latest)
brew install postgresql@18

# Start service
brew services start postgresql@17
```

### Ubuntu/Debian
```bash
# Install PostgreSQL 17 (recommended)
sudo apt-get install postgresql-17 postgresql-client-17 postgresql-contrib-17

# Install PostgreSQL 18 (latest)
sudo apt-get install postgresql-18 postgresql-client-18 postgresql-contrib-18

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### CentOS/RHEL
```bash
# Install PostgreSQL 17 (recommended)
sudo dnf install postgresql17-server postgresql17

# Install PostgreSQL 18 (latest)
sudo dnf install postgresql18-server postgresql18

# Initialize and start
sudo postgresql-17-setup initdb
sudo systemctl start postgresql-17
sudo systemctl enable postgresql-17
```

## 🔍 Version Checking

### Check Installed Version
```bash
# Check PostgreSQL version
psql --version

# Check if service is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS
```

### Test Connection
```bash
# Test connection to default database
psql -U postgres -h localhost

# Test connection to specific database
psql -U postgres -h localhost -d nosuvo_db
```

## ⚠️ Important Notes

1. **PostgreSQL 9.6+ Required**: SQLAlchemy 2.0+ requires PostgreSQL 9.6 or later
2. **Python 3.6+ Required**: Alembic 1.13.1 requires Python 3.6 or later
3. **Extension Support**: All versions support the extensions used by NoSubvo
4. **Performance**: PostgreSQL 17+ offers significant performance improvements
5. **Security**: Newer versions have better security features

## 🔧 Migration Considerations

### From Older PostgreSQL Versions
- **9.6 → 17**: Major upgrade, test thoroughly
- **10+ → 17**: Generally smooth, minor configuration updates
- **15+ → 18**: Should be seamless

### Downgrade Considerations
- **Not recommended**: Newer features may not work on older versions
- **Data compatibility**: Generally backward compatible
- **Extension compatibility**: Check extension versions

## 📊 Performance Recommendations

### For Production
- **PostgreSQL 17.x**: Best balance of features and stability
- **Connection pooling**: Use PgBouncer for high concurrency
- **Memory tuning**: Adjust `shared_buffers` and `work_mem`
- **Monitoring**: Use `pg_stat_statements` extension

### For Development
- **Any supported version**: 9.6+ is fine for development
- **Local installation**: Use Docker for easy version switching
- **Minimal configuration**: Default settings usually sufficient
