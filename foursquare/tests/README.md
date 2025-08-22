# Foursquare Import Test Suite

Comprehensive test suite for the Foursquare Neo4j import tooling, covering unit tests, integration tests, data validation, and geospatial functionality.

## 📋 Test Categories

### 🔧 Unit Tests (`test_foursquare_import.py`)
- Import class initialization
- CSV data reading and parsing
- Data type conversion and validation
- Category parsing and extraction
- Point geometry creation
- Error handling and edge cases
- **No external dependencies** - uses mocks

### 🔗 Integration Tests (`test_integration.py`)
- End-to-end import process
- Neo4j database operations
- Schema creation and constraints
- Relationship building
- Query execution
- **Requires running Neo4j instance**

### 📊 Data Validation Tests (`test_data_validation.py`)
- Coordinate validation and bounds checking
- Numeric field conversion
- String field cleaning
- CSV structure validation
- Category parsing edge cases
- Point geometry validation

### 🗺️ Geospatial Tests (`test_geospatial_queries.py`)
- Spatial distance calculations
- Within-distance queries
- Nearest neighbor searches
- Routing and pathfinding
- Spatial clustering analysis
- Performance testing
- **Requires Neo4j with spatial support**

## 🚀 Running Tests

### Quick Unit Tests
```bash
make test-quick
```

### Unit Tests Only
```bash
make test-unit
```

### Integration Tests (requires Neo4j)
```bash
make test-integration
```

### Geospatial Tests (requires Neo4j with spatial)
```bash
make test-geospatial
```

### All Tests
```bash
make test-all
```

### Coverage Report
```bash
make test-coverage
```

## 🛠️ Test Setup

### 1. Install Test Dependencies
```bash
make test-setup
```

### 2. Configure Test Database
Copy and edit the test configuration:
```bash
cp test_config.env.example test_config.env
# Edit test_config.env with your test Neo4j settings
```

**Important**: Use a separate test database to avoid affecting production data!

### 3. Generate Test Data
```bash
make generate-test-data
```

### 4. Run Tests
```bash
# Unit tests (no Neo4j required)
make test-unit

# Integration tests (Neo4j required)
export RUN_INTEGRATION_TESTS=1
make test-integration
```

## 🗄️ Test Configuration

### Environment Variables
- `RUN_INTEGRATION_TESTS=1` - Enable integration/geospatial tests
- `RUN_LONG_TESTS=1` - Enable performance and long-running tests

### Test Configuration File (`test_config.env`)
```env
NEO4J_CONNECTION_STRING=bolt://neo4j:password@localhost:7687/test_foursquare
RUN_INTEGRATION_TESTS=0
RUN_LONG_TESTS=0
```

### Pytest Configuration (`pytest.ini`)
- Automatic test discovery
- Test markers for categorization
- Timeout settings
- Warning filters

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures and configuration
├── pytest.ini                 # Pytest settings
├── README.md                   # This file
├── test_foursquare_import.py   # Unit tests
├── test_integration.py         # Integration tests
├── test_data_validation.py     # Data validation tests
├── test_geospatial_queries.py  # Geospatial tests
└── fixtures/
    ├── __init__.py
    ├── test_data_generator.py  # Generate test data
    └── data/                   # Generated test files
        ├── test_stops.txt
        ├── test_places.csv
        ├── spatial_test_stops.txt
        ├── spatial_test_places.csv
        ├── unit_test_stops.txt
        └── unit_test_places.csv
```

## 🏷️ Test Markers

Tests are automatically marked based on their requirements:

- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (require Neo4j)
- `@pytest.mark.geospatial` - Geospatial tests (require Neo4j with spatial)
- `@pytest.mark.slow` - Long-running tests

### Running Specific Test Categories
```bash
# Unit tests only
pytest -m "unit"

# Integration tests only
pytest -m "integration"

# Geospatial tests only
pytest -m "geospatial"

# Exclude slow tests
pytest -m "not slow"
```

## 🔧 Test Fixtures

### Automatic Fixtures (`conftest.py`)
- `test_config` - Neo4j test configuration
- `neo4j_available` - Check Neo4j availability
- `temp_data_dir` - Temporary directory for test files
- `mock_neo4j_config` - Mocked configuration for unit tests
- `sample_stops_data` - Sample transit stops data
- `sample_places_data` - Sample places data
- `test_csv_files` - Generated test CSV files
- `clean_test_database` - Database cleanup before/after tests
- `mock_importer` - Mocked importer for unit tests
- `integration_importer` - Real importer for integration tests

## 📊 Test Coverage

The test suite aims for high coverage of critical functionality:

### Import Functions
- ✅ Data reading and parsing
- ✅ Data type conversion
- ✅ Schema creation
- ✅ Batch processing
- ✅ Relationship creation
- ✅ Error handling

### Geospatial Functions
- ✅ Coordinate validation
- ✅ Point geometry creation
- ✅ Distance calculations
- ✅ Spatial relationships
- ✅ Routing queries
- ✅ Clustering analysis

### Data Validation
- ✅ CSV structure validation
- ✅ Coordinate bounds checking
- ✅ Category parsing
- ✅ String cleaning
- ✅ Numeric conversion

## 🐛 Debugging Tests

### Verbose Output
```bash
pytest -v -s tests/
```

### Run Single Test
```bash
pytest tests/test_foursquare_import.py::TestFoursquareImporter::test_init -v
```

### Debug Integration Issues
```bash
# Check Neo4j connection
make test

# Validate test configuration
python -c "
import sys; sys.path.append('../gtfs')
from neo4j_config import Neo4jConfig
config = Neo4jConfig('test_config.env')
print(f'URI: {config.uri}')
print(f'Database: {config.database}')
print(f'Valid: {config.validate_connection()}')
"
```

### Test Data Generation Issues
```bash
# Generate test data manually
python tests/fixtures/test_data_generator.py --output-dir tests/fixtures/data

# Check generated files
ls -la tests/fixtures/data/
```

## 🔍 Continuous Integration

For CI/CD pipelines, use:

```yaml
# Example GitHub Actions
- name: Run Unit Tests
  run: make test-unit

- name: Run Integration Tests
  env:
    RUN_INTEGRATION_TESTS: 1
  run: make test-integration
  # Only if Neo4j service is available
```

## 📈 Performance Expectations

### Unit Tests
- Should complete in < 30 seconds
- No external network calls
- Predictable execution time

### Integration Tests
- Should complete in < 2 minutes
- Requires Neo4j connection
- May vary based on database performance

### Geospatial Tests
- Should complete in < 5 minutes
- Tests spatial query performance
- Requires Neo4j with spatial indexes

## 🚨 Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Check Neo4j is running: `neo4j status`
   - Verify credentials in `test_config.env`
   - Check firewall settings

2. **Import Permission Denied**
   - Check file permissions on test data
   - Verify Neo4j user has database write access

3. **Spatial Queries Fail**
   - Ensure Neo4j version >= 3.4 for spatial support
   - Check spatial indexes are created
   - Verify SRID configuration (4326)

4. **Tests Timeout**
   - Increase timeout in `pytest.ini`
   - Check database performance
   - Consider reducing test data size

5. **Missing Test Data**
   - Run `make generate-test-data`
   - Check `tests/fixtures/data/` directory exists
   - Verify data generator completed successfully

### Getting Help

1. Check test output for specific error messages
2. Run tests with `-v -s` flags for detailed output
3. Verify Neo4j configuration and connectivity
4. Review test fixtures and data generation
5. Check Neo4j logs for database-related issues

## 🎯 Test Quality Goals

- **Coverage**: > 90% for critical import functions
- **Reliability**: Tests should pass consistently
- **Speed**: Unit tests < 30s, Integration tests < 2min
- **Maintainability**: Clear test names and documentation
- **Isolation**: Tests don't affect each other or production data