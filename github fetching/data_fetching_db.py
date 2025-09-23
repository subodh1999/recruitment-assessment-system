import requests
import time
import os
import logging
import argparse
# import schedule
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Set, Dict, Any, Optional, List
from database import DatabaseManager

load_dotenv()

class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    BASE_URL = "https://api.github.com"
    SOURCING_SEARCH_QUERY = os.getenv("SOURCING_SEARCH_QUERY")
    SOURCING_PROCESSED_USERS_FILE = os.getenv("SOURCING_PROCESSED_USERS_FILE")
    TRAINING_SEARCH_QUERY = os.getenv("TRAINING_SEARCH_QUERY")
    TRAINING_PROCESSED_USERS_FILE = os.getenv("TRAINING_PROCESSED_USERS_FILE")
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10))
    LOG_FILE = os.getenv("LOG_FILE")
    RETRY_DELAY_BASE = int(os.getenv("RETRY_DELAY_BASE", 2))
    POST_BATCH_DELAY = int(os.getenv("POST_BATCH_DELAY", 10))
    DB_PARAMS = {
        "host": os.getenv("DB_HOST"), "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME"), "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }

class GitHubAPIClient:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GitHub token is required in the .env file.")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"})

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, retries: int = 3) -> Optional[Any]:
        for attempt in range(retries):
            try:
                resp = self.session.get(url, params=params)
                if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
                    reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                    wait_duration = max(0, reset_time - time.time()) + 1
                    logging.warning(f"Rate limit hit. Waiting for {wait_duration:.0f} seconds.")
                    time.sleep(wait_duration)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed ({url}) on attempt {attempt+1}: {e}")
                time.sleep(Config.RETRY_DELAY_BASE ** attempt)
        return None

    def search_users(self, query: str, page: int) -> Optional[Dict[str, Any]]:
        params = {"q": query, "per_page": Config.BATCH_SIZE, "page": page}
        return self.get(f"{Config.BASE_URL}/search/users", params=params)

    def get_user_details(self, username: str) -> Optional[Dict[str, Any]]:
        return self.get(f"{Config.BASE_URL}/users/{username}")

    def get_user_repos(self, username: str) -> List[Dict[str, Any]]:
        return self.get(f"{Config.BASE_URL}/users/{username}/repos", params={"per_page": 100}) or []

    def get_user_orgs(self, username: str) -> List[Dict[str, Any]]:
        return self.get(f"{Config.BASE_URL}/users/{username}/orgs") or []

    def get_repo_contributors(self, owner: str, repo_name: str) -> List[Dict[str, Any]]:
        return self.get(f"{Config.BASE_URL}/repos/{owner}/{repo_name}/stats/contributors") or []

    def get_issue_pr_count(self, query: str) -> int:
        data = self.get(f"{Config.BASE_URL}/search/issues", params={"q": query})
        return data.get("total_count", 0) if data else 0

class DataManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_processed_users(self, processed_file: str) -> Set[str]:
        if not os.path.exists(processed_file):
            return set()
        with open(processed_file, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)

    def save_processed_users(self, usernames: Set[str], processed_file: str):
        with open(processed_file, "w", encoding="utf-8") as f:
            for username in sorted(list(usernames)):
                f.write(f"{username}\n")

    def persist_candidates(self, candidates: List[Dict[str, Any]], table_name: str):
        if candidates:
            self.db_manager.persist_candidates(candidates, table_name)

    def clear_all_data(self, processed_file: str, table_name: str):
        if os.path.exists(processed_file):
            os.remove(processed_file)
            logging.info(f"Removed old file: {processed_file}")
        self.db_manager.truncate_data_table(table_name)

class GitHubProfiler:
    def __init__(self, api_client: GitHubAPIClient, data_manager: DataManager, search_query: str, processed_file: str, target_table: str):
        self.client = api_client
        self.data_manager = data_manager
        self.search_query = search_query
        self.processed_file = processed_file
        self.target_table = target_table
        self.page = 1
        self.processed_usernames = self.data_manager.load_processed_users(self.processed_file)
        logging.info(f"[{self.target_table}] Loaded {len(self.processed_usernames)} previously processed usernames.")

    def run(self, start_fresh: bool = False):
        if start_fresh:
            logging.info(f"[{self.target_table}] Starting fresh: deleting old data and clearing table.")
            self.data_manager.clear_all_data(self.processed_file, self.target_table)
            self.processed_usernames = set()

        while True:
            if not self._process_batch():
                logging.info(f"[{self.target_table}] Processing finished.")
                break
            logging.info(f"Batch complete. Waiting {Config.POST_BATCH_DELAY} seconds.")
            time.sleep(Config.POST_BATCH_DELAY)

    def _process_batch(self) -> bool:
        logging.info(f"--- [{self.target_table}] Processing search page {self.page} ---")
        results = self.client.search_users(self.search_query, self.page)

        # First, check for a failed API call or a response with a missing "items" key.
        if not results or "items" not in results:
            logging.error(f"[{self.target_table}] Search returned invalid data. Stopping.")
            return False

        # Separately, check if the items list is empty, which means no more users were found.
        if not results["items"]:
            logging.warning(f"[{self.target_table}] No more users found on page {self.page}. Concluding search.")
            return False
        # --- END OF FIX ---

        new_users = [u["login"] for u in results["items"] if u["login"] not in self.processed_usernames]
        logging.info(f"[{self.target_table}] Fetched {len(results['items'])} users, {len(new_users)} are new.")

        if new_users:
            enriched_data = self._enrich_users_concurrently(new_users)
            self.data_manager.persist_candidates(enriched_data, self.target_table)

        self.processed_usernames.update(u["login"] for u in results["items"])
        self.data_manager.save_processed_users(self.processed_usernames, self.processed_file)
        self.page += 1
        return True

    def _enrich_users_concurrently(self, usernames: List[str]) -> List[Dict[str, Any]]:
        enriched = []
        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            future_map = {executor.submit(self._enrich_candidate, u): u for u in usernames}
            for future in as_completed(future_map):
                try:
                    data = future.result()
                    if data:
                        enriched.append(data)
                        logging.info(f"Successfully processed profile for: {future_map[future]}")
                except Exception as e:
                    logging.error(f"Error processing {future_map[future]}: {e}", exc_info=True)
        return enriched

    def _enrich_candidate(self, username: str) -> Optional[Dict[str, Any]]:
        profile = self.client.get_user_details(username)
        if not profile: return None
        repos = self.client.get_user_repos(username)
        orgs = self.client.get_user_orgs(username)
        total_stars, total_forks, languages = 0, 0, {}
        for repo in repos:
            total_stars += repo.get("stargazers_count", 0)
            total_forks += repo.get("forks_count", 0)
            if lang := repo.get("language"):
                languages[lang] = languages.get(lang, 0) + 1
        total_contributions = sum(c.get("total", 0) for r in repos if not r.get("fork") for c in self.client.get_repo_contributors(username, r['name']) if c.get("author", {}).get("login") == username)
        created_dt = datetime.strptime(profile["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        account_age_days = (datetime.now(timezone.utc) - created_dt).days
        return {"username": username, "name": profile.get("name"), "email": profile.get("email"), "profile_url": profile.get("html_url"), "followers": profile.get("followers"), "public_repos": profile.get("public_pos"), "total_stars_received": total_stars, "total_forks_received": total_forks, "organizations_count": len(orgs), "account_age_days": account_age_days, "primary_languages": ", ".join(sorted(languages, key=languages.get, reverse=True)[:3]), "hireable": profile.get("hireable"), "location": profile.get("location"), "issues_opened": self.client.get_issue_pr_count(f"author:{username} type:issue"), "issues_closed": self.client.get_issue_pr_count(f"author:{username} type:issue is:closed"), "prs_opened": self.client.get_issue_pr_count(f"author:{username} type:pr"), "prs_closed": self.client.get_issue_pr_count(f"author:{username} type:pr is:closed"), "prs_merged": self.client.get_issue_pr_count(f"author:{username} type:pr is:merged"), "total_contributions": total_contributions}

def run_sourcing_pipeline():
    logging.info("--- Starting Sourcing Pipeline (for 'unknown_github_users') ---")
    api_client = GitHubAPIClient(Config.GITHUB_TOKEN)
    db_manager = DatabaseManager(Config.DB_PARAMS)
    data_manager = DataManager(db_manager)
    profiler = GitHubProfiler(api_client, data_manager,
        search_query=Config.SOURCING_SEARCH_QUERY,
        processed_file=Config.SOURCING_PROCESSED_USERS_FILE,
        target_table="unknown_github_users"
    )
    profiler.run(start_fresh=False)
    logging.info("--- Sourcing Pipeline Finished ---")

def run_training_pipeline():
    logging.info("--- Starting Training Pipeline (for 'github_users') ---")
    api_client = GitHubAPIClient(Config.GITHUB_TOKEN)
    db_manager = DatabaseManager(Config.DB_PARAMS)
    data_manager = DataManager(db_manager)
    profiler = GitHubProfiler(api_client, data_manager,
        search_query=Config.TRAINING_SEARCH_QUERY,
        processed_file=Config.TRAINING_PROCESSED_USERS_FILE,
        target_table="github_users"
    )
    profiler.run(start_fresh=True)
    logging.info("--- Training Pipeline Finished ---")

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.FileHandler(Config.LOG_FILE), logging.StreamHandler()])

def main():
    setup_logging()
    db_manager = DatabaseManager(Config.DB_PARAMS)
    db_manager.initialize_tables()

    parser = argparse.ArgumentParser(description="Run a specific GitHub data pipeline.")
    parser.add_argument("pipeline", choices=["sourcing", "training"], help="The pipeline to run ('sourcing' or 'training').")
    args = parser.parse_args()

    if args.pipeline == "sourcing":
        run_sourcing_pipeline()
    elif args.pipeline == "training":
        run_training_pipeline()

    # --- SCHEDULER CODE: UNCOMMENT TO USE ---
    # logging.info("Scheduler started. Waiting for scheduled jobs...")
    # schedule.every(90).days.do(run_sourcing_pipeline)
    # schedule.every(180).days.do(run_training_pipeline)
    #
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)

if __name__ == "__main__":
    main()