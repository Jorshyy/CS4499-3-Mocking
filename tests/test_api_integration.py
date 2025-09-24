import pytest
from unittest.mock import call
from api_integration import metrics


@pytest.mark.parametrize(
    "username, token, status_code, expected",
    [
        pytest.param("user1", "token1", 200, {"login": "user1"}, id="get_user_metrics_success"),
        pytest.param("user2", "token2", 404, None, id="get_user_metrics_not_found"),
        pytest.param("user3", None, 200, {"login": "user2"}, id="get_user_metrics_success_without_token"),
    ]
)
def test_get_user_metrics(mocker, username, token, status_code, expected):
    mock_response = mocker.MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = expected

    gitHubRequest = mocker.patch('api_integration.metrics.requests.get')
    gitHubRequest.return_value = mock_response

    result = metrics.get_github_user_info(username, token)

    assert result == expected
    gitHubRequest.assert_called_once()


@pytest.mark.parametrize(
    "json_return_value, status, expected_calls, expected_json",
    [
        pytest.param([], 200, [], [], id="get_user_repos_no_repos"),
        pytest.param(
            [{"name": "repo1", "stargazers_count": 5, "language": "Python"}],
            200,
            [call("https://api.github.com/users/user1/repos", headers={'Accept': 'application/vnd.github+json'}, params={'per_page': 30, 'page': 1})],
            [{"name": "repo1", "stars": 5, "language": "Python"}],
            id="get_user_repos_1_page"
        ),
        pytest.param(
            [],
            418,
            [],
            [],
            id="empty_repos_response"
        )
    ]
)
def test_get_github_user_repos(mocker, status, json_return_value, expected_calls, expected_json):
    mock_response_page = mocker.MagicMock()
    mock_response_page.status_code = status
    mock_response_page.json.return_value = json_return_value


    gitHubRequest = mocker.patch('api_integration.metrics.requests.get')
    gitHubRequest.return_value = mock_response_page

    # Call function
    result = metrics.get_github_user_repos("user1")
    gitHubRequest.assert_has_calls(expected_calls)
    assert result == expected_json


@pytest.mark.parametrize(
    "status_code, expected",
    [
        pytest.param(202, {"status": "success", "metric": "metric_name", "value": 100}, id="submit_metric_success"),
        pytest.param(400, {"status": "error", "code": 400}, id="submit_metric_failure"),
        pytest.param(500, {"status": "error", "code": 500}, id="submit_metric_server_error"),
    ]
)
def test_submit_datadog_metric(mocker, status_code, expected):
    # mock pycurl.Curl()
    curl_mock = mocker.MagicMock()
    curl_mock.getinfo.return_value = 200
    mocker.patch('api_integration.metrics.pycurl.Curl', return_value=curl_mock)

    # mock setopt
    mocker.patch.object(curl_mock, 'setopt')
    # mock perform
    mocker.patch.object(curl_mock, 'perform')
    # mock getinfo
    mocker.patch.object(curl_mock, 'getinfo', return_value=status_code)
    # mock close
    mocker.patch.object(curl_mock, 'close')

    result = metrics.submit_datadog_metric("metric_name", 100, "api_key", "app_key")
    assert result == expected


@pytest.mark.parametrize(
    "username, stars_list, expected",
    [
        pytest.param("user1", [6, 1, 1, 1, 1], {"username": "user1", "total_repositories": 5, "total_stars": 10, "activity_level": "low"}, id="low_activity"),
        pytest.param("user1", [5, 5, 5, 5, 5], {"username": "user1", "total_repositories": 5, "total_stars": 25, "activity_level": "moderate"}, id="moderate_activity"),
        pytest.param("user1", [40, 20, 10, 5], {"username": "user1", "total_repositories": 4, "total_stars": 75, "activity_level": "high"}, id="high_activity"),
    ]
)
def test_analyze_developer_activity(mocker, username, stars_list, expected):
    # mock get_github_user_info
    mock_get_user_info = mocker.patch('api_integration.metrics.get_github_user_info')
    mock_get_user_info.return_value = {"login": username}

    # mock get_github_user_repos
    mock_get_user_repos = mocker.patch('api_integration.metrics.get_github_user_repos')
    mock_get_user_repos.return_value = [{"name": f"repo{i}", "stars": stars, "language": "Python"} for i, stars in enumerate(stars_list)]

    # mock submit_datadog_metric
    mock_submit_metric = mocker.patch('api_integration.metrics.submit_datadog_metric')
    mock_submit_metric.return_value = {"status": "success"}

    expected_metric_calls = [
        call(f"github.user.{username}.total_stars", expected["total_stars"], "datadog_api_key", "datadog_app_key"),
        call(f"github.user.{username}.repo_count", expected["total_repositories"], "datadog_api_key", "datadog_app_key")
    ]
    result = metrics.analyze_developer_activity(username, "github_token", "datadog_api_key", "datadog_app_key")

    assert result == expected
    mock_get_user_info.assert_called_once()
    mock_get_user_repos.assert_called_once()
    mock_submit_metric.assert_called()
    mock_submit_metric.assert_has_calls(expected_metric_calls, any_order=True)
    assert mock_submit_metric.call_count == 2

