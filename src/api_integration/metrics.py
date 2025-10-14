import json
import pycurl
import requests
from io import BytesIO


class GitHubMetricsClient:
    def __init__(self, github_token=None, datadog_api_key=None, datadog_app_key=None, host="localhost"):
        self.github_token = github_token
        self.datadog_api_key = datadog_api_key
        self.datadog_app_key = datadog_app_key
        self.host = host

    def get_github_user_info(self, username):
        """Fetch GitHub user information."""
        url = f"https://api.github.com/users/{username}"
        headers = {"Accept": "application/vnd.github+json"}

        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None


    def get_github_user_repos(self, username):
        """Fetch all repositories of a GitHub user."""
        url = f"https://api.github.com/users/{username}/repos"
        headers = {"Accept": "application/vnd.github+json"}

        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        
        all_repos = []
        page = 1
        
        while page:
            response = requests.get(url, headers=headers, params={"per_page": 30, "page": page})
            
            if response.status_code != 200:
                break
                
            repos = response.json()
            if not repos:
                break
                
            for repo in repos:
                all_repos.append({
                    "name": repo["name"], 
                    "stars": repo["stargazers_count"],
                    "language": repo["language"]
                })
            
            link_header = response.headers.get("Link", "")
            if "rel=\"next\"" in link_header:
                page += 1
            else:
                page = None
        
        return all_repos


    def submit_datadog_metric(self, metric_name, value):
        """Submit a custom metric to Datadog."""
        url = "https://api.datadoghq.com/api/v1/series"
        
        data = {
            "series": [{
                "metric": metric_name,
                "points": [[1234567890, value]],
                "host": self.host
            }]
        }
        
        buffer = BytesIO()
        curl = pycurl.Curl()
        
        curl.setopt(curl.URL, url)
        curl.setopt(curl.POSTFIELDS, json.dumps(data))
        curl.setopt(curl.HTTPHEADER, [
            "Content-Type: application/json",
            f"DD-API-KEY: {self.datadog_api_key}",
            f"DD-APPLICATION-KEY: {self.datadog_app_key}"
        ])
        curl.setopt(curl.WRITEDATA, buffer)
        
        curl.perform()
        status_code = curl.getinfo(curl.RESPONSE_CODE)
        curl.close()
        
        if status_code == 202:
            return {"status": "success", "metric": metric_name, "value": value}
        else:
            return {"status": "error", "code": status_code}


    def analyze_developer_activity(self, username):
        """Analyze a GitHub user's activity and submit metrics to Datadog."""
        user_info = self.get_github_user_info(username)
        repos = self.get_github_user_repos(username)

        total_stars = sum(repo["stars"] for repo in repos)
        
        self.submit_datadog_metric(
            f"github.user.{username}.total_stars",
            total_stars,
            self.datadog_api_key,
            self.datadog_app_key
        )
        
        self.submit_datadog_metric(
            f"github.user.{username}.repo_count",
            len(repos),
            self.datadog_api_key,
            self.datadog_app_key
        )
        
        return {
            "username": username,
            "total_repositories": len(repos),
            "total_stars": total_stars,
            "activity_level": "high" if total_stars > 50 else "moderate" if total_stars > 10 else "low"
        }
