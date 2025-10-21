# Scripts Directory

This directory contains all development and maintenance scripts for PsySuite Web Manager.

## Directory Structure

```
scripts/
├── db/                 # Database management scripts
│   ├── clear_db.py     # Clear all database entries
│   ├── recreate_db.py  # Drop existing DB, recreate tables, add admin user and a dummy test
│   ├── export_data.py  # Export database to JSON
│   └── import_data.py  # Import database from JSON
├── tests/              # Test scripts
│   ├── run_tests.py    # Run all tests
│   ├── test_system.py  # System integration tests
│   └── test_android_integration_manual.py  # Android integration tests
├── debug.py            # Debug Flask app for PyCharm
└── run.py              # Convenient script runner
```

## Usage

### Database Management
```bash
# Clear all database entries
python scripts/db/clear_db.py

# Drop existing DB, recreate tables, add admin user and a dummy test
python scripts/db/recreate_db.py

# Export development data
python scripts/db/export_data.py backup.json

# Import data to production
python scripts/db/import_data.py backup.json production
```

### Development
```bash
# Run debug server (for PyCharm debugging)
python scripts/debug.py
```

### Testing
```bash
# Run all tests
python scripts/tests/run_tests.py

# Run system tests
python scripts/tests/test_system.py

# Run Android integration tests
python scripts/tests/test_android_integration_manual.py
```

### Convenient Runner
```bash
# Use the script runner for easier access
python scripts/run.py --help
python scripts/run.py db recreate
python scripts/run.py db clear
python scripts/run.py db dummy
python scripts/run.py test system
python scripts/run.py debug
```