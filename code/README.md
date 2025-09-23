############################################## DATA FETCHING [API] ###############################################
# GitHub User Profiler

A Python-based data pipeline that searches, profiles, and stores GitHub user information in a PostgreSQL database. The system supports two distinct pipelines: one for sourcing unknown users and another for training data collection.

## Features

- **Dual Pipeline System**: Separate workflows for sourcing and training data
- **Comprehensive User Profiling**: Collects detailed GitHub user metrics including repositories, contributions, and activity
- **Rate Limit Handling**: Intelligent API rate limit management with automatic retry mechanisms
- **Concurrent Processing**: Multi-threaded user enrichment for improved performance
- **Database Integration**: PostgreSQL storage with conflict resolution
- **Resume Capability**: Tracks processed users to avoid duplicates and enable resume functionality

## Architecture

The system consists of several key components:

- **GitHubAPIClient**: Handles all GitHub API interactions with rate limiting
- **DatabaseManager**: Manages PostgreSQL operations and table initialization
- **DataManager**: Handles file operations and data persistence coordination
- **GitHubProfiler**: Orchestrates the profiling pipeline workflow

## Prerequisites

- Python 3.7+
- PostgreSQL database
- GitHub Personal Access Token

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd github-user-profiler
```

2. Install required dependencies:
```bash
pip install requests psycopg2-binary python-dotenv
```

3. Set up your environment variables by creating a `.env` file:

```env
# GitHub API Configuration
GITHUB_TOKEN=your_github_personal_access_token

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Pipeline Configuration
SOURCING_SEARCH_QUERY="your search query for sourcing"
SOURCING_PROCESSED_USERS_FILE=sourcing_processed_users.txt
TRAINING_SEARCH_QUERY="your search query for training"
TRAINING_PROCESSED_USERS_FILE=training_processed_users.txt

# Performance Settings
MAX_WORKERS=5
BATCH_SIZE=10
RETRY_DELAY_BASE=2
POST_BATCH_DELAY=10

# Logging
LOG_FILE=github_profiler.log
```

## Configuration

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with appropriate permissions:
   - `public_repo` (for public repository access)
   - `user:read` (for user profile information)
3. Add the token to your `.env` file

### Search Queries

Define your search queries using GitHub's search syntax:
- `SOURCING_SEARCH_QUERY`: Query for discovering new users
- `TRAINING_SEARCH_QUERY`: Query for collecting training dataset

Example queries:
```env
SOURCING_SEARCH_QUERY="location:california followers:>100"
TRAINING_SEARCH_QUERY="language:python followers:>500"
```

## Usage

### Command Line Interface

Run specific pipelines using the command line:

```bash
# Run the sourcing pipeline
python data_fetching_db.py sourcing

# Run the training pipeline
python data_fetching_db.py training
```

### Pipeline Types

#### Sourcing Pipeline
- **Target Table**: `unknown_github_users`
- **Behavior**: Incremental processing (resumes from where it left off)
- **Purpose**: Continuous discovery of new GitHub users

#### Training Pipeline
- **Target Table**: `github_users`
- **Behavior**: Fresh start (clears existing data)
- **Purpose**: Clean dataset collection for training purposes

## Data Schema

Both pipelines store data in tables with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| username | VARCHAR(255) | GitHub username (Primary Key) |
| name | VARCHAR(255) | User's display name |
| email | VARCHAR(255) | Public email address |
| profile_url | VARCHAR(255) | GitHub profile URL |
| followers | INTEGER | Number of followers |
| public_repos | INTEGER | Number of public repositories |
| total_stars_received | INTEGER | Total stars across all repositories |
| total_forks_received | INTEGER | Total forks across all repositories |
| organizations_count | INTEGER | Number of organizations user belongs to |
| account_age_days | INTEGER | Age of GitHub account in days |
| primary_languages | TEXT | Top 3 programming languages (comma-separated) |
| hireable | BOOLEAN | Whether user is available for hire |
| location | VARCHAR(255) | User's location |
| issues_opened | INTEGER | Total issues opened by user |
| issues_closed | INTEGER | Total issues closed by user |
| prs_opened | INTEGER | Total pull requests opened |
| prs_closed | INTEGER | Total pull requests closed |
| prs_merged | INTEGER | Total pull requests merged |
| total_contributions | INTEGER | Total contributions across repositories |

## Performance Tuning

### Configuration Parameters

- `MAX_WORKERS`: Number of concurrent threads for user enrichment (default: 5)
- `BATCH_SIZE`: Users processed per API search request (default: 10)
- `POST_BATCH_DELAY`: Seconds to wait between batches (default: 10)
- `RETRY_DELAY_BASE`: Base delay for exponential backoff (default: 2)

### Rate Limiting

The system automatically handles GitHub's rate limits:
- Monitors `X-RateLimit-Remaining` header
- Implements exponential backoff for failed requests
- Waits for rate limit reset when necessary

## Monitoring and Logging

Logs are written to both console and file (specified by `LOG_FILE`). The system provides detailed logging for:

- Pipeline progress and batch processing
- API rate limit status
- Database operations
- Error handling and retries
- User processing statistics

## Resuming Operations

The system maintains processed user lists in text files:
- `SOURCING_PROCESSED_USERS_FILE`: Tracks users processed by sourcing pipeline
- `TRAINING_PROCESSED_USERS_FILE`: Tracks users processed by training pipeline

This enables:
- Avoiding duplicate processing
- Resuming interrupted operations
- Incremental data collection

## Scheduled Operations (Optional)

The code includes commented scheduler functionality using the `schedule` library. To enable automated runs:

1. Install the schedule library:
```bash
pip install schedule
```

2. Uncomment the scheduler code in the `main()` function
3. Adjust the schedule intervals as needed:
   - Sourcing pipeline: Every 90 days
   - Training pipeline: Every 180 days

## Error Handling

The system includes robust error handling:
- **API Failures**: Automatic retry with exponential backoff
- **Database Errors**: Comprehensive logging and graceful failure
- **Data Validation**: Handles missing or malformed API responses
- **Rate Limits**: Automatic waiting and retry mechanisms

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify database credentials in `.env`
   - Ensure PostgreSQL server is running
   - Check network connectivity

2. **GitHub API Rate Limits**
   - Verify your GitHub token is valid
   - Consider reducing `MAX_WORKERS` and increasing `POST_BATCH_DELAY`
   - Monitor your rate limit usage

3. **Memory Issues**
   - Reduce `BATCH_SIZE` for large-scale operations
   - Monitor system resources during execution

### Debug Mode

Enable detailed logging by modifying the logging level in `setup_logging()`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
1. Check the logs for detailed error information
2. Verify your configuration settings
3. Review GitHub API documentation for search query syntax
4. Open an issue with detailed error information and configuration (excluding sensitive data)



######################################## Model training and Prediction #######################################
## About (main .py and prediction.py) Code
# - main.py
    - This file contain the code to fetchdata from "github_user" table from postgres_sql.
    - This code cleans, transformorm, log, scale the raw data.
    - post scaling we perform clustering with k as 2.
    - After clustering we Train the model for Prediction and store the pickel file in "model_pickel" table in DB.

# - prediction.py
    - After model training we load the pickel model in prediction.py and run the prediction on live fetch data which is stored in "unknown_github_users".
    - After prediction a status tab is added to same table "unknown_github_users" which has either "selected" or "rejected" value
    - it also stores selected candidate in a new "candidate" table.

    

