import os
# to remove the warning after K means clustering
os.environ['LOKY_MAX_CPU_COUNT'] = '6'
os.environ['OMP_NUM_THREADS'] = '6'

import pickle
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, LargeBinary, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

from sklearn.cluster import KMeans
from sklearn.metrics import classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from preprocessing import preprocess_pipeline

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy model for storing
Base = declarative_base()

class ModelPickle(Base):
    __tablename__ = "model_pickles"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, unique=True, index=True)
    pickle_data = Column(LargeBinary)

# Create the table if it doesnt exist
Base.metadata.create_all(bind=engine)


def fetch_data_from_db(query: str) -> pd.DataFrame:
    print("Step 1: Fetching data from database")
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)
        print(f"Successfully fetched {df.shape[0]} rows.")
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def scale_data(df: pd.DataFrame) -> tuple[pd.DataFrame, StandardScaler]:
    print("Step 4: Scaling data after cleaning and transformation")
    if df.empty:
        return df, None
        
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df)
    df_scaled = pd.DataFrame(scaled_features, columns=df.columns, index=df.index)
    
    print("Data scaling complete.")
    return df_scaled, scaler


def perform_clustering(df_scaled: pd.DataFrame, n_clusters) -> tuple[pd.DataFrame, KMeans]:
    print(f"Step 5: Performing K-Means clustering with {n_clusters} clusters")
    if df_scaled.empty:
        return df_scaled, None
        
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df_scaled['cluster'] = kmeans.fit_predict(df_scaled)

    print(df_scaled.head())
    print(df_scaled.shape)
    print((df_scaled["cluster"]==1).sum())
    
    print("Clustering complete. 'cluster' column added.")
    return df_scaled, kmeans

def train_models(df_with_clusters: pd.DataFrame) -> dict:

    print("Step 6: Training models...")
    if df_with_clusters.empty:
        return {}

    X = df_with_clusters.drop('cluster', axis=1)
    y = df_with_clusters['cluster']

    #Implementing SMOTE for balancing data
    smote = SMOTE(random_state=42)
    X_smote, y_smote = smote.fit_resample(X, y)
    
    X_train, X_test, y_train, y_test = train_test_split(X_smote, y_smote, test_size=0.3, random_state=42)

    #################### uncomment below code for viewing shape of train and test split of balanced data

    # print("X_train shape:", X_train.shape)
    # print("X_test shape:", X_test.shape)
    # print("y_train shape:", y_train.shape)
    # print("y_test shape:", y_test.shape)

    ############# Uncomment below code for viewing the balancing of clusters ######################3

    # df_with_clusters_smote = pd.DataFrame(X_smote, columns=['followers', 'public_repos', 'total_stars_received',
    #    'total_forks_received', 'account_age_days', 'pr_merge_rate',
    #    'prs_closed_unmerged', 'pr_issue_ratio', 'total_issue_activity'])
    # df_with_clusters_smote['Clusters'] = y_smote

    # cluster_1_count = (df_with_clusters_smote['Clusters'] == 1).sum() # values in cluster 0
    # print(f"Total number of values in cluster 1 is {cluster_1_count}")

    # cluster_0_count = (df_with_clusters_smote['Clusters'] == 0).sum() # values in cluster 0
    # print(f"Total number of values in cluster 0 is {cluster_0_count}")
    
    
    
    # model training

    # 1 - Logistic Regression

    log_reg = LogisticRegression(random_state=42)
    log_reg.fit(X_train, y_train)
    print("\nLogistic Regression model trained.")

    y_pred_lr = log_reg.predict(X_test)
    print("Logistic Regression Report")
    print(classification_report(y_test, y_pred_lr))
    print("--------------------------------------------------------")
    
    
    # 2 - Random forest

    random_forest = RandomForestClassifier(random_state=42)
    random_forest.fit(X_train, y_train)
    print("\nRandom Forest model trained.")

    y_pred_rf = random_forest.predict(X_test)
    print("Random Forest Report")
    print(classification_report(y_test, y_pred_rf))
    print("--------------------------------------------------------")

    # 3 - Decision Tree

    decision_tree = DecisionTreeClassifier(random_state=42)
    decision_tree.fit(X_train, y_train)
    print("\nDecision Tree model trained.")

    y_pred_dt = decision_tree.predict(X_test)
    print("Decision Tree Report")
    print(classification_report(y_test, y_pred_dt))
    print("--------------------------------------------------------")
    
    models = {
        "logistic_regression": log_reg,
        "random_forest": random_forest,
        "decision_tree": decision_tree
     }
    
    return models

def store_pickles_in_db(objects_to_pickle: dict):
    print("Step 7: Storing pickle files in the database...")
    db = SessionLocal()
    try:
        for name, obj in objects_to_pickle.items():
            pickle_data = pickle.dumps(obj)
            
            # Check if the model already exists and update it, otherwise create new
            db_model = db.query(ModelPickle).filter(ModelPickle.model_name == name).first()
            if db_model:
                db_model.pickle_data = pickle_data
                print(f"Updated pickle for '{name}' in the database.")
            else:
                db_model = ModelPickle(model_name=name, pickle_data=pickle_data)
                db.add(db_model)
                print(f"Stored new pickle for '{name}' in the database.")
        
        db.commit()
    except Exception as e:
        print(f"Error storing pickles: {e}")
        db.rollback()
    finally:
        db.close()



def main():
    
    sql_query = "SELECT * FROM github_users;"
    
    # Pipeline Execution
    raw_df = fetch_data_from_db(sql_query)
    
    if not raw_df.empty:
        preprocessed_df = preprocess_pipeline(raw_df)
        scaled_df, scaler = scale_data(preprocessed_df)
        df_with_clusters, kmeans_model = perform_clustering(scaled_df, n_clusters=2)
        trained_models = train_models(df_with_clusters)        
        # Combine all objects to be pickled
        objects_to_save = {
            "standard_scaler": scaler,
            "kmeans_model": kmeans_model,
            **trained_models  # Adds all trained models to the dictionary (** is for unpacking dictionary)
        }
        
        store_pickles_in_db(objects_to_save)
        
        print("\nPipeline executed successfully!")
        

if __name__ == "__main__":
    
    main()