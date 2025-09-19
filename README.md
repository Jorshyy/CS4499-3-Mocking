# Unit 2: Mocking Assignment - API Integration Testing

## Overview
You will write comprehensive tests for the `api_integration.py` module, which integrates with GitHub's REST API and Datadog's metrics API. This assignment tests your understanding of mocking techniques, parameterized testing, and testing best practices.

## Module Functions to Test

### 1. `get_github_user_info(username, token=None)`
- Makes a single API call to GitHub's user endpoint
- Returns user data on success (200), None on 404, None on other errors
- Uses optional authentication token

### 2. `get_github_user_repos(username, token=None)`
- Makes paginated API calls to GitHub's repositories endpoint
- Continues pagination based on Link header presence (`rel="next"`)
- Aggregates all repository data across pages
- **Key testing opportunity**: Use `assert_has_calls()` to verify sequential API calls

### 3. `submit_datadog_metric(metric_name, value, api_key, app_key, host="localhost")`
- Uses `pycurl` to submit metrics to Datadog
- Returns success/error status based on HTTP response code
- **Key testing opportunity**: Mock `pycurl.Curl()` and its methods

### 4. `analyze_developer_activity(username, github_token, datadog_api_key, datadog_app_key)`
- Runner function that calls all other functions
- Aggregates GitHub data and submits metrics to Datadog
- Returns analysis summary

## Testing Requirements

### Test File Structure
Create `tests/test_api_integration.py` with tests for each function.

### Required Testing Techniques

#### 1. **MagicMock Usage**
- Mock `requests.get()` response objects with dynamic attributes
- Mock response methods: `.json()`, `.status_code`, `.headers.get()`
- Mock `pycurl.Curl()` object and all its methods (`setopt`, `perform`, `getinfo`, `close`)

#### 2. **Parameterized Testing** 
- Each test function must use `@pytest.mark.parametrize`
- Each test must have **exactly 3 test cases** with meaningful `id` parameters
- Example scenarios:
  - Success cases, error cases, edge cases
  - Different response codes, different data structures
  - Pagination scenarios (single page, multiple pages, no data)

#### 3. **assert_has_calls() Usage**
- `get_github_user_repos()` tests must verify pagination calls
- Use `mock.call()` objects to verify exact API call sequence
- Test scenarios: single page, multiple pages, interrupted pagination

#### 4. **Proper Mocking Strategy**
- Mock external dependencies (`requests.get`, `pycurl.Curl`)
- **DO NOT mock the functions you're testing** (common mistake)
- Mock at the correct level (where the dependency is used, not where it's defined)
- Use `mocker.patch()` for all mocking

## Test Examples You Must Include

### For `get_github_user_repos()`:
```python
@pytest.mark.parametrize("pages,expected_calls", [
    pytest.param([...], [...], id="single_page"),
    pytest.param([...], [...], id="multiple_pages"), 
    pytest.param([...], [...], id="no_next_link")
])
def test_get_github_user_repos_pagination(mocker, pages, expected_calls):
    # Your test implementation
    mock_get.assert_has_calls(expected_calls)
```

### For `submit_datadog_metric()`:
- Mock `pycurl.Curl()` constructor
- Mock all curl methods: `setopt()`, `perform()`, `getinfo()`, `close()`
- Test different HTTP response codes

### For `analyze_developer_activity()`:
- Mock all internal function calls
- Verify integration between GitHub data and Datadog submissions
- Test data aggregation logic

## Rubric (100 Points Total)

### Parametrized Testing (15 points)
- **15 points**: All test functions properly parametrized with exactly 3 test cases each, meaningful IDs
- **10 points**: Most tests parametrized correctly, minor issues
- **5 points**: Some parametrization present but incomplete
- **0 points**: No or incorrect parametrization

### Correct Mocking (30 points)
- **30 points**: All external dependencies properly mocked, no testing of mock objects, correct patch locations
- **20 points**: Most mocking correct, 1-2 minor issues
- **10 points**: Some correct mocking but significant issues (testing mocks, wrong patch locations)
- **0 points**: Incorrect or missing mocking

### Function Coverage & Test Quality (40 points)
- **40 points**: Tests for all 4 functions, tests pass, good assertions, proper use of assert_has_calls
- **30 points**: Tests for 3-4 functions, mostly passing, good test structure
- **20 points**: Tests for 2-3 functions, some issues with test logic
- **10 points**: Tests for 1-2 functions, significant issues
- **0 points**: No working tests or major implementation problems

### Project Setup & Execution (15 points)
- **15 points**: `git clone` → `uv sync` → `pytest` works flawlessly
- **0 points**: Any troubleshooting required to run tests (automatic loss of full 15 points)

## Submission Requirements

1. Create `tests/metrics.py`
2. Ensure all dependencies are in `pyproject.toml`
3. Tests must run with simple `pytest` command
4. Include clear test function names and docstrings
5. Commit and push to your repository

## Common Mistakes to Avoid

- **DON'T** mock the function you're testing (e.g., don't mock `get_github_user_info` when testing it)
- **DON'T** forget to mock response object methods like `.json()` and `.headers.get()`
- **DON'T** use regular `Mock` when `MagicMock` is needed for dynamic attributes
- **DON'T** forget to test pagination scenarios with `assert_has_calls()` or the multiple calls to submit_datadog_metric
- **DON'T** hardcode test data - use parametrization for different scenarios

## Tips for Success

- Start with the simplest function (`get_github_user_info`) first
- Use `MagicMock()` for response objects that need dynamic methods
- Test pagination by mocking different Link header scenarios
- Mock `pycurl.Curl()` constructor and all its instance methods
- Use meaningful parameter IDs in your test cases
- Run tests frequently during development
- Debug debug debug!
