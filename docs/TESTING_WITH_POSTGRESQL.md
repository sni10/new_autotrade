# 🧪 Testing with PostgreSQL Environment

## Overview

This project now includes a complete PostgreSQL testing environment that runs tests with a real PostgreSQL database, both locally and in GitHub Actions CI/CD pipeline.

## 🏗️ Architecture

### Local Development
- **Main PostgreSQL**: `docker-compose.yml` - Port 5434 (for development)
- **Test PostgreSQL**: `docker-compose.test.yml` - Port 5435 (for testing)

### CI/CD (GitHub Actions)
- **Test PostgreSQL**: Runs in isolated container environment
- **Automatic cleanup**: Containers are removed after tests complete

## 📁 Files Structure

```
├── docker-compose.test.yml     # Test environment with PostgreSQL
├── Dockerfile.test            # Specialized test container
├── entrypoint.sh             # Database connection script
├── .github/workflows/
│   └── python-tests.yml     # Updated CI/CD workflow
└── tests/                   # All test files (221 tests)
    ├── database/           # Database-specific tests
    ├── entities/          # Entity tests
    ├── repositories/      # Repository tests
    ├── services/         # Service tests
    └── ...              # Other test categories
```

## 🚀 Usage

### Running Tests Locally

```bash
# Run all tests with PostgreSQL
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-runner

# Clean up after tests
docker-compose -f docker-compose.test.yml down -v
```

### Running Specific Test Categories

```bash
# Run only database tests
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/database/ -v

# Run only service tests
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/services/ -v
```

## 🔧 Configuration

### Environment Variables (Test Container)

| Variable | Value | Description |
|----------|-------|-------------|
| `DB_HOST` | `postgres-test` | PostgreSQL hostname |
| `DB_PORT` | `5432` | PostgreSQL port (internal) |
| `DB_USER` | `airflow` | Database username |
| `DB_PASSWORD` | `airflow` | Database password |
| `DB_NAME` | `airflow` | Database name |
| `PYTHONPATH` | `/app/src` | Python module path |

### PostgreSQL Configuration (Test)

- **Image**: `postgres:16`
- **Port Mapping**: `5435:5432` (to avoid conflict with dev DB)
- **Memory**: Uses tmpfs for faster I/O
- **Health Checks**: Ensures DB is ready before tests start
- **Optimized Settings**: Configured for testing performance

## 🎯 GitHub Actions Integration

### Workflow Triggers
- **Pull Requests**: to `dev`, `stage`, `release/*`, `main`
- **Pushes**: to `dev`, `stage`, `release/*`, `main`

### Workflow Steps
1. **Checkout** repository code
2. **Setup Docker Buildx** for multi-platform builds
3. **Start PostgreSQL** and run tests via docker-compose
4. **Collect logs** if tests fail
5. **Clean up** containers and system resources
6. **Archive artifacts** (test results, coverage reports)
7. **Upload artifacts** to GitHub

### Artifacts Generated
- `pytest-artifacts-{run_number}` - Test cache and results
- `coverage-report-{run_number}` - Code coverage reports

## 📊 Test Categories

| Category | Count | Description |
|----------|-------|-------------|
| **Database** | 3 | PostgreSQL connectivity and CRUD operations |
| **Entities** | 2 | Domain entity tests (Deal, CurrencyPair) |
| **Repositories** | 3 | Data access layer tests |
| **Services** | 4 | Business logic and service tests |
| **Factories** | 2 | Object creation factory tests |
| **Monitoring** | 5 | System monitoring and statistics |
| **Fixes** | 7 | Bug fix validation tests |
| **Architecture** | 2 | System architecture tests |
| **Integration** | 2 | End-to-end integration tests |
| **Config** | 1 | Configuration loading tests |
| **Total** | **221** | **All tests with PostgreSQL support** |

## 🔍 Database Tests

### Connection Test (`test_db_connection.py`)
- ✅ PostgreSQL connectivity
- ✅ Table creation/deletion
- ✅ Data insertion/retrieval
- ✅ Connection cleanup

### CRUD Operations (`test_database_crud_operations.py`)
- ✅ Deal creation and modification
- ✅ Repository synchronization
- ✅ Data persistence verification

### Visual CRUD (`test_database_visual_crud.py`)
- ✅ Table structure inspection
- ✅ Data visualization
- ✅ Migration verification

## 🚨 Troubleshooting

### Port Conflicts
If you get "port already allocated" error:
```bash
# Check what's using the port
docker ps

# Stop conflicting containers
docker-compose down

# Or use different port in docker-compose.test.yml
```

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.test.yml logs postgres-test

# Verify database is ready
docker-compose -f docker-compose.test.yml exec postgres-test pg_isready -U airflow
```

### Test Failures
```bash
# Run tests with verbose output
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/ -v -s

# Run specific failing test
docker-compose -f docker-compose.test.yml run --rm test-runner pytest tests/path/to/test.py::test_name -v
```

## 📈 Performance

### Local Test Performance
- **Total Tests**: 221
- **Execution Time**: ~50 seconds
- **Database Startup**: ~10 seconds
- **Test Execution**: ~40 seconds

### CI/CD Performance
- **Container Build**: ~2-4 minutes (cached layers)
- **Test Execution**: ~1-2 minutes
- **Total Pipeline**: ~3-6 minutes

## 🔄 Migration from Old Setup

### Before (Issues)
- ❌ Used pre-built Docker image without PostgreSQL
- ❌ Tests couldn't connect to database
- ❌ Database-dependent tests were skipped or failed
- ❌ No real database integration testing

### After (Solutions)
- ✅ PostgreSQL included in test environment
- ✅ All tests run with real database connections
- ✅ Complete database integration testing
- ✅ Isolated test database (no conflicts)
- ✅ Automatic cleanup and resource management

## 🎉 Benefits

1. **Real Database Testing**: Tests run against actual PostgreSQL
2. **CI/CD Integration**: Automated testing in GitHub Actions
3. **Isolation**: Test database separate from development
4. **Performance**: Optimized PostgreSQL configuration for testing
5. **Reliability**: Health checks ensure database readiness
6. **Cleanup**: Automatic container and resource cleanup
7. **Artifacts**: Test results and coverage reports preserved
8. **Scalability**: Easy to add more database-dependent tests

## 📝 Next Steps

1. **Monitor CI/CD**: Watch GitHub Actions for any issues
2. **Add More Tests**: Expand database integration tests
3. **Performance Tuning**: Optimize test execution time
4. **Documentation**: Keep this guide updated with changes