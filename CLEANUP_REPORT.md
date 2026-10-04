# CLEANUP_REPORT - AI SOC Web Application Upgrade

## Overview
This report documents files and folders proposed for removal during the upgrade of the AI SOC web application to a production-quality dark navy SOC design system.

## Files Proposed for Removal (CONFIRMED UNUSED)

### Generated/Build Outputs
- `frontend\node_modules\**` - Node modules will be retained; added to .gitignore if needed
- `backend\*.pyc` files under `__pycache__` - Python cache files, not source
- `output_files.txt`, `output.txt`, `captured_output.txt`, `captured_output.txt` - Temporary output files
- `temp_vars.txt` - Temporary variables file
- `start_and_validate.py`, `start_backend.py`, `start_server*.py`, `start_server*.bat` - Redundant startup scripts
- `be_log.log`, `be_main.txt`, `validation*.log` - Backend log files
- `database\**` - Migration/cache databases (verify if active)
- `sample_logs\**` - Sample log data (may be retained as test data)

### Duplicate/Redundant Source Files
- `AI-Based-SOC-with-Automated-Firewall-Response\**` - Duplicate project folder
- `ai-soc-firewall-response\**` - Duplicate project folder
- `ai_soc.db` - Database file (verify if still in use)
- `exploration_output.txt`, `diagnostic_result.txt`, `validate_output.txt` - Diagnostic outputs

### Deprecated/Unused Assets
- `docs\**` - Documentation (may need review)
- ` scripts\**` - Deploy scripts (verify if still needed)
- `README.md` - Will be updated with new run commands

## Files to Retain
- All React source files under `frontend/src/`
- `frontend\package.json` and `package-lock.json`
- `frontend\src\components\**` - Core UI components
- `frontend\src\pages\**` - Page components
- `backend\**` - Python backend (preserve API endpoints)
- `.env` and configuration files
- `node_modules` (add to .gitignore if needed)

## Upgrade Notes
- The existing React + Vite project will be upgraded to match the dark navy SOC design system
- All 12 required pages/features will be implemented
- Components will be refactored: AppShell, Sidebar, Header, MetricCard, DataTable, StatusBadge, Panel, Chart, Modal, EmptyState, LoadingState
- API layer will be consolidated and types added
- Mock data layer will be isolated for missing endpoints
- DoS simulation will be simulation-only with clear disclaimer

**Generated**: Project upgrade assessment