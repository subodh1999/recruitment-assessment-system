import pandas as pd
import numpy as np

def clean_and_prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    print("Step 2: Cleaning and preparing data")
    if df.empty:
        return df
    ########### Numeric Columns ##################
    cluster_cols = [
        'followers', 'public_repos', 'total_stars_received', 
        'total_forks_received', 'organizations_count', 'account_age_days',
        'issues_opened', 'issues_closed', 'prs_opened', 'prs_closed',
        'prs_merged', 'total_contributions'
    ]
    df_cluster = df[cluster_cols].copy()



    # Handling extreme outliers
    df_cluster = df_cluster[df_cluster['followers'] <= 40000]
    df_cluster = df_cluster[df_cluster['public_repos'] <= 1800]
    df_cluster = df_cluster[df_cluster['total_stars_received'] <= 200000]
    df_cluster = df_cluster[df_cluster['total_forks_received'] <= 50000]
    df_cluster = df_cluster[df_cluster['organizations_count'] <= 15]
    df_cluster = df_cluster[df_cluster['issues_opened'] <= 2000]
    df_cluster = df_cluster[df_cluster['issues_closed'] <= 1500]
    df_cluster = df_cluster[df_cluster['prs_opened'] <= 4000]
    df_cluster = df_cluster[df_cluster['prs_closed'] <= 4000]
    df_cluster = df_cluster[df_cluster['prs_merged'] <= 4000]
    df_cluster = df_cluster[df_cluster['total_contributions'] <= 250]
    # Eleminating invalid records
    invalid_condition = (df_cluster['prs_opened'] == 0) & \
                      ((df_cluster['prs_closed'] > 0) | (df_cluster['prs_merged'] > 0))
    df_cluster = df_cluster[~invalid_condition]

    
    print(f"Data cleaned. Shape is now: {df_cluster.shape}")
    return df_cluster

def transform_features(df: pd.DataFrame) -> pd.DataFrame:
    print("Step 3: Transforming features")
    if df.empty:
        return df
        
    # Deriving new columns 
    df['pr_merge_rate'] = df['prs_merged'] / df['prs_opened']
    df['pr_issue_ratio'] = df['prs_opened'] / df['issues_opened']
    df['prs_closed_unmerged'] = df['prs_closed'] - df['prs_merged']
    df['total_issue_activity'] = df['issues_opened'] + df['issues_closed']

    # Fill NaN values that result from division by zero
    df.fillna(0, inplace=True)

    # Replaceing infinity (inf) and negative infinity (-inf) with 0
    df.replace([np.inf, -np.inf], 0, inplace=True)
    
    # Droping original columns that are no longer required
    cols_to_drop = ['issues_opened', 'issues_closed', 'prs_opened', 'prs_closed', 'prs_merged', 'total_contributions', 'organizations_count']
    df = df.drop(columns=cols_to_drop)

    # Logging for removing skewness present in data
    df = np.log1p(df)

    print("Feature transformation complete.")
    return df

def preprocess_pipeline(df: pd.DataFrame) -> pd.DataFrame:

    print("Step: Cleaning data")
    cleaned_df = clean_and_prepare_data(df)
    print("Step: Transforming data")
    transformed_df = transform_features(cleaned_df)
    print("Preprocessing complete.")
    return transformed_df