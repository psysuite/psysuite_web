# Scripts Directory

This directory contains development and maintenance scripts for PsySuite Web Manager.

## Directory Structure

```
scripts/
├── db/                 # Database management scripts
│   ├── clear_db.py     # Clear all database entries
│   ├── recreate_db.py  # Drop existing DB, recreate tables, add admin user
│   ├── init_db.py      # Initialize database with proper schema
│   ├── export_data.py  # Export database to JSON
│   └── import_data.py  # Import database from JSON
├── tests/              # Development test scripts
│   ├── run_tests.py    # Run all tests with coverage
│   └── test_system.py  # System integration tests (for deployment validation)
├── debug.py            # Debug Flask app for PyCharm
└── run.py              # Convenient script runner
```

## Usage

### Database Management
```bash
# Initialize database (recommended for fresh setup)
python scripts/db/init_db.py

# Clear all database entries (development only)
python scripts/db/dev_clear_db.py

# Recreate database with fresh schema (development only)
python scripts/db/dev_recreate_db.py

# Export development data
python scripts/db/dev_export_data.py backup.json

# Import data to production
python scripts/db/dev_import_data.py backup.json production
```

### Development
```bash
# Run debug server (for PyCharm debugging)
python scripts/run_debug.py
```

### Testing
```bash
# Run all tests with coverage
python scripts/tests/run_tests.py

# Run system integration tests (useful for deployment validation)
python scripts/tests/test_system.py

# Run system tests against specific URL
python scripts/tests/test_system.py https://your-domain.com
```

### Convenient Runner
```bash
# Use the script runner for easier access
python scripts/run.py --help
python scripts/run.py db recreate
python scripts/run.py db clear
python scripts/run.py test all
python scripts/run.py test system
python scripts/run.py debug
```

## Notes

- **Main test suite** is in the `tests/` directory (root level)
- **Scripts tests** are for development and deployment validation
- **Database scripts** should only be used in development environment
- **For production deployment**, use the main `init_db.py` script in the root directory