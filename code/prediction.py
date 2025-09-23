import os
import pickle
import random 
import pandas as pd
from sqlalchemy import create_engine, text, Column, String, Integer, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
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

Base = declarative_base()

class ModelPickle(Base):
    __tablename__ = "model_pickles"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, unique=True, index=True)
    pickle_data = Column(LargeBinary)

class Candidate(Base):
    __tablename__ = 'candidate'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)
    password = Column(String)

Base.metadata.create_all(bind=engine)

def load_models_from_db(model_names: list) -> dict:
    print("Loading trained models from the database")
    db = SessionLocal()
    models = {}
    try:
        for name in model_names:
            db_model = db.query(ModelPickle).filter(ModelPickle.model_name == name).first()
            if db_model:
                models[name] = pickle.loads(db_model.pickle_data)
                print(f"Successfully loaded model: '{name}'")
            else:
                raise ValueError(f"Model '{name}' not found in the database.")
        return models
    except Exception as e:
        print(f"Error loading models: {e}")
        return {}
    finally:
        db.close()

def fetch_live_data(query: str) -> pd.DataFrame:
    print("\nStep 1: Fetching live data for prediction...")
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)
        print(f"Successfully fetched {df.shape[0]} new users.")
        return df
    except Exception as e:
        print(f"Error fetching live data: {e}")
        return pd.DataFrame()

def predict(df: pd.DataFrame, scaler, model) -> pd.Series:
    print("\nStep 4: Scaling data and making predictions...")
    if df.empty:
        return pd.Series()
    
    try:
        expected_columns = scaler.get_feature_names_out()
        for col in expected_columns:
            if col not in df.columns:
                df[col] = 0
        df_aligned = df[expected_columns]
        
        scaled_features = scaler.transform(df_aligned)
        predictions = model.predict(scaled_features)
        return predictions
    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        return pd.Series()

def update_user_status(results_df: pd.DataFrame, engine):
    print("\nStep 5: Updating user status in the database ")

    if 'username' not in results_df.columns:
        print("Error: Key 'username' not found in DataFrame. Cannot update database.")
        return

    df_to_update = results_df.copy()
    status_map = {0: 'selected', 1: 'rejected'}
    df_to_update['predicted_cluster'] = df_to_update['predicted_cluster'].map(status_map)
    df_to_update.dropna(subset=['predicted_cluster'], inplace=True)
    
    if df_to_update.empty:
        print("No valid records to update after mapping.")
        return

    records_to_update = df_to_update[['username', 'predicted_cluster']].rename(
        columns={'predicted_cluster': 'status'}
    ).to_dict(orient='records')

    if not records_to_update:
        print("No records to update.")
        return

    update_query = text("UPDATE unknown_github_users SET status = :status WHERE username = :username")

    try:
        with engine.begin() as connection:
            connection.execute(update_query, records_to_update)
        print(f"Successfully updated status for {len(records_to_update)} users.")
    except Exception as e:
        print(f"Error updating database: {e}")

def store_selected_candidate(results_df: pd.DataFrame):
    print("\nStep 6: Storing selected candidate...")

    selected_df = results_df[results_df['predicted_cluster'] == 0].copy()

    if selected_df.empty:
        print("No new candidate were selected to be stored.")
        return

    if 'email' not in selected_df.columns:
        selected_df['email'] = None

    null_email_mask = selected_df['email'].isnull()

    generated_emails = selected_df.loc[null_email_mask, 'username'] + '@gmail.com'

    selected_df.loc[null_email_mask, 'email'] = generated_emails

    selected_df['password'] = [str(random.randint(10000, 99999)) for _ in range(len(selected_df))]

    candidate_to_insert = selected_df[['username', 'email', 'password']].to_dict(orient='records')

    db = SessionLocal()
    try:
        existing_usernames_q = db.query(Candidate.username).filter(
            Candidate.username.in_([c['username'] for c in candidate_to_insert])
        )
        existing_usernames = {username for (username,) in existing_usernames_q}

        new_candidate = [
            Candidate(**user_data) for user_data in candidate_to_insert
            if user_data['username'] not in existing_usernames
        ]

        if not new_candidate:
            print("All selected candidate already exist in the 'candidate' table.")
            return

        db.add_all(new_candidate)
        db.commit()
        print(f"Successfully stored {len(new_candidate)} new users in the 'candidate' table.")

    except Exception as e:
        print(f"An error occurred while storing candidate: {e}")
        db.rollback()
    finally:
        db.close()

def main_prediction():
    required_models = ['standard_scaler', 'logistic_regression']
    loaded_models = load_models_from_db(required_models)
    
    if len(loaded_models) != len(required_models):
        print("Could not load all required models. Exiting.")
        return

    scaler = loaded_models['standard_scaler']
    log_reg_model = loaded_models['logistic_regression']

    sql_query = "SELECT * FROM unknown_github_users WHERE status IS NULL;"
    live_df = fetch_live_data(sql_query)

    if not live_df.empty:
        original_df = live_df.copy()
        
        preprocessed_df = preprocess_pipeline(live_df)
        
        predictions = predict(preprocessed_df, scaler, log_reg_model)

        results_df = original_df.loc[preprocessed_df.index].copy()
        results_df['predicted_cluster'] = predictions
        
        print("\n--- Prediction Results ---")
        print(results_df[['username', 'predicted_cluster']].head())

        update_user_status(results_df, engine)

        store_selected_candidate(results_df)

if __name__ == "__main__":
    print("Starting prediction pipeline...")
    main_prediction()
    print("\nPipeline finished.")