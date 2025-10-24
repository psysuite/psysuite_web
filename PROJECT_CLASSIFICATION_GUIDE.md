# Project Classification System Guide

## Overview

The Project Classification System allows researchers to organize experiments by project, providing better data organization and analysis capabilities across different research initiatives.

## Features

### Android App Features
- **Project Selection**: Choose a project when starting each test
- **Project Management**: Create, edit, and delete projects via the top-right menu
- **Validation**: Ensures project selection before test submission
- **Local Storage**: Projects are stored locally using SharedPreferences

### Web Application Features
- **Admin Project Management**: Full CRUD operations for projects (admin only)
- **Project Filtering**: Filter experiments by project in the experiments view
- **Sortable Tables**: Sort experiments by any column including project
- **Project Statistics**: View experiment distribution across projects
- **Project Assignment**: Automatic project assignment during experiment upload

## Getting Started

### For Android App Users

#### 1. Managing Projects
1. Open the PsySuite Android app
2. Tap the menu button (⋮) in the top-right corner
3. Select "Manage Projects"
4. Use the dialog to:
   - **Add**: Enter a project name and tap "Add"
   - **Edit**: Tap the edit icon next to a project
   - **Delete**: Tap the delete icon (confirms before deletion)

#### 2. Selecting Projects During Tests
1. When starting any test, the subject dialog will appear
2. Fill in the required fields (Label, Age, Gender, Population, Session)
3. **Select a Project**: Choose from the dropdown (required field)
   - "Select project" - Default option (must change this)
   - "n.a." - No specific project
   - Your custom projects - Projects you've created
4. Complete the test as normal

#### 3. Project Validation
- The app will show a warning if you try to start a test without selecting a project
- This ensures all experiment data is properly categorized

### For Web Application Administrators

#### 1. Project Management
1. Log in to the web application as an admin
2. Click "Projects" in the navigation bar
3. Use the project management interface to:
   - **Create**: Enter a project name and click "Create Project"
   - **Edit**: Click the edit icon next to a project
   - **Delete**: Click the delete icon (handles existing experiments gracefully)

#### 2. Viewing Project Statistics
1. Navigate to Projects → Statistics
2. View:
   - Total projects and experiments
   - Average experiments per project
   - Most active project
   - Detailed breakdown by project

#### 3. Filtering Experiments by Project
1. Go to any test's experiments page
2. Use the "Filter by Project" dropdown to:
   - View all experiments
   - View experiments with no project
   - View experiments for a specific project

### For Researchers

#### 1. Viewing Experiment Data
- All experiment tables now include a "Project" column
- Click on column headers to sort by any field including project
- Use project filters to focus on specific research initiatives

#### 2. Data Export
- Exported experiment data includes project information
- Project data is included in all CSV exports and API responses

## Technical Details

### Data Storage

#### Android App
- Projects are stored in SharedPreferences (`psysuite_projects`)
- No automatic synchronization with web backend
- Manual coordination required between devices

#### Web Application
- Projects stored in `projects` table
- Experiments have `project_id` (foreign key) and `project_name` (denormalized)
- Indexes on project fields for performance

### Data Flow
1. User creates projects in Android app (stored locally)
2. User selects project when starting test
3. Project information included in JSON configuration
4. Experiment uploaded to web backend with project data
5. Web backend stores project information in database

### API Changes
The experiment upload API now accepts project information:
```json
{
  "exp_uid": "unique_experiment_id",
  "test_class_name": "TestBIS",
  "configuration": {
    "label": "Subject001",
    "age": 25,
    "project": "Project Alpha",
    // ... other fields
  },
  "trials": [...],
  "device_id": "device_123"
}
```

## Migration

### For Existing Installations

#### 1. Database Migration
Run the migration script to add project support to existing data:

```bash
# Dry run to see what would be changed
python scripts/db/migrate_projects.py --dry-run

# Perform the actual migration
python scripts/db/migrate_projects.py
```

The migration script:
- Creates the `projects` table
- Adds project columns to `experiments` table
- Creates a "Legacy Data" project
- Assigns existing experiments to "Legacy Data"

#### 2. Android App Updates
- Update to the latest version with project support
- Existing users will see the new project selection dialog
- No data migration needed on Android devices

### For New Installations
- Project support is included by default
- No migration needed

## Best Practices

### Project Naming
- Use descriptive, consistent names
- Avoid special characters
- Keep names under 100 characters
- Consider using prefixes for related projects (e.g., "Study2024_Baseline", "Study2024_Followup")

### Project Organization
- Create projects before starting data collection
- Coordinate project names between Android devices and web admin
- Use "n.a." for pilot tests or informal data collection
- Regularly review and clean up unused projects

### Data Management
- Use project filtering to focus analysis on specific studies
- Export data by project for separate analysis
- Monitor project statistics to track data collection progress

## Troubleshooting

### Common Issues

#### "Project is required" Error
- **Cause**: Trying to start test without selecting a project
- **Solution**: Select a project from the dropdown (not "Select project")

#### Project Not Appearing in Dropdown
- **Cause**: Project created on different device or not synced
- **Solution**: Manually create the project on the current device

#### Experiments Showing "No Project"
- **Cause**: Experiments uploaded before project system or with missing project data
- **Solution**: Normal behavior for legacy data; use migration script for bulk assignment

### Support
For technical issues or questions:
1. Check this guide first
2. Review the project statistics page for data validation
3. Contact your system administrator
4. Check application logs for detailed error messages

## API Reference

### Project Management Endpoints (Admin Only)
- `GET /admin/projects/` - List all projects
- `POST /admin/projects/create` - Create new project
- `POST /admin/projects/{id}/edit` - Update project
- `POST /admin/projects/{id}/delete` - Delete project
- `GET /admin/projects/api/list` - JSON list of projects

### Experiment Filtering
- `GET /experiments/{test_id}?project={project_name}` - Filter experiments by project
- `GET /experiments/{test_id}?project=none` - Show experiments without projects

### Data Export
All experiment export endpoints now include project information in the response data.