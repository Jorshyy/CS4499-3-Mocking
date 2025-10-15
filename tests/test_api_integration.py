import pytest
from unittest.mock import call, MagicMock
# from api_integration import metrics

from api_integration import GitHubMetricsClient

# fixture for GitHubMetricsClient
@pytest.fixture
def mock_github_metrics_client():
    return GitHubMetricsClient(
        github_token="test_github_token",
        datadog_api_key="test_datadog_api_key",
        datadog_app_key="test_datadog_app_key",
        host="localhost"
    )



@pytest.mark.parametrize(
    "username, token, status_code, expected",
    [
        pytest.param("user1", "token1", 200, {"login": "user1"}, id="get_user_metrics_success"),
        pytest.param("user2", "token2", 404, None, id="get_user_metrics_not_found"),
        pytest.param("user3", None, 200, {"login": "user2"}, id="get_user_metrics_success_without_token"),
    ]
)
def test_get_github_user_info(mock_github_metrics_client, mocker, username, status_code, expected):
    mock_response = mocker.MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = expected
    githubRequest = mocker.patch("metrics.requests.get", return_value=mock_response)

    result = GitHubMetricsClient.get_github_user_info(self=mock_github_metrics_client, username=username)

    assert result == expected
    assert githubRequest.call_count == 1


@pytest.mark.parametrize(
    "pages, expected_names, expected_calls",
    [
        pytest.param(
            [dict(status=200, json=[{"name": "r1", "stargazers_count": 5, "language": "Py"}], link=None)],
            ["r1"], 1, id="single_page"
        ),
        pytest.param(
            [
                dict(status=200, json=[{"name": "r1", "stargazers_count": 2, "language": "Py"}], link='<https://api.github.com/users/u/repos?page=2>; rel="next"'),
                dict(status=200, json=[{"name": "r2", "stargazers_count": 3, "language": "Py"}], link=None),
            ],
            ["r1", "r2"], 2, id="two_pages"
        ),
        pytest.param(
            [dict(status=500, json=[], link=None)],
            [], 1, id="server_error"
        )
    ]
)
def test_get_github_user_repos_pagination(mock_github_metrics_client, mocker, pages, expected_names, expected_calls):
    def mockResponse(p):
        mock = MagicMock()
        mock.status_code = p["status"]
        mock.json.return_value = p["json"]
        mock.headers = {"Link": p["link"]} if p["link"] else {}
        return mock

    mock_get = mocker.patch("metrics.requests.get", side_effect=[mockResponse(p) for p in pages])

    result = GitHubMetricsClient.get_github_user_repos(self=mock_github_metrics_client, username="u")

    assert [r["name"] for r in result] == expected_names
    assert mock_get.call_count == expected_calls

    # Check the first call URL and params
    first_args, first_kwargs = mock_get.call_args_list[0]
    assert first_args[0].endswith("/users/u/repos")
    assert first_kwargs["params"]["page"] == 1
    assert first_kwargs["params"]["per_page"] == 30
    assert "headers" in first_kwargs




@pytest.mark.parametrize(
    "status_code, expected",
    [
        pytest.param(202, {"status": "success", "metric": "m", "value": 7}, id="accepted"),
        pytest.param(400, {"status": "error", "code": 400}, id="bad_request"),
        pytest.param(500, {"status": "error", "code": 500}, id="server_error"),
    ]
)
def test_submit_datadog_metric(mock_github_metrics_client, mocker, status_code, expected):
    curl = mocker.MagicMock()
    mocker.patch("metrics.pycurl.Curl", return_value=curl)
    curl.getinfo.return_value = status_code

    result = GitHubMetricsClient.submit_datadog_metric(
        self=mock_github_metrics_client,
        metric_name="m",
        value=7,
        host="testhost"
    )

    assert result == expected



@pytest.mark.parametrize(
    "username, stars_list, expected",
    [
        pytest.param(
            "alice", [1, 2, 3, 4],
            {"username": "alice", "total_repositories": 4, "total_stars": 10, "activity_level": "low"},
            id="low"
        ),
        pytest.param(
            "bob", [5, 5, 5],
            {"username": "bob", "total_repositories": 3, "total_stars": 15, "activity_level": "moderate"},
            id="moderate"
        ),
        pytest.param(
            "carol", [20, 20, 11],
            {"username": "carol", "total_repositories": 3, "total_stars": 51, "activity_level": "high"},
            id="high"
        ),
    ]
)
def test_analyze_developer_activity(mock_github_metrics_client, mocker, username, stars_list, expected):
    mocker.patch("metrics.GitHubMetricsClient.get_github_user_info", return_value={"login": username})
    mocker.patch(
        "metrics.GitHubMetricsClient.get_github_user_repos",
        return_value=[{"name": f"r{i}", "stars": s, "language": "Py"} for i, s in enumerate(stars_list)]
    )
    submit = mocker.patch("metrics.GitHubMetricsClient.submit_datadog_metric", return_value={"status": "success"})

    result = GitHubMetricsClient.analyze_developer_activity(self=mock_github_metrics_client, username=username)

    assert result == expected
    expected_calls = [
        call(f"github.user.{username}.total_stars", expected["total_stars"]),
        call(f"github.user.{username}.repo_count", expected["total_repositories"]),
    ]
    submit.assert_has_calls(expected_calls, any_order=True)
    assert submit.call_count == 2