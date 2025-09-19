import pytest
from unittest.mock import MagicMock, Mock, call
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
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = expected

    gitHubRequest = mocker.patch('api_integration.metrics.requests.get')
    gitHubRequest.return_value = mock_response

    result = metrics.get_github_user_info(username, token)

    assert result == expected
    gitHubRequest.assert_called_once()


