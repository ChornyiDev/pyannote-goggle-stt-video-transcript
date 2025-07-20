import os
from dotenv import load_dotenv
from google.cloud import storage
from google.api_core import exceptions

 # Load environment variables from .env file
load_dotenv()

def test_gcs_connection():
    """
    Checks connection to Google Cloud Storage and access to the specified bucket.
    """
    print("--- Starting GCS connection test ---")

    # 1. Check for environment variable
    bucket_name_full = os.getenv('FIREBASE_STORAGE_BUCKET')
    if not bucket_name_full:
        print("ERROR: Environment variable FIREBASE_STORAGE_BUCKET not found in .env file.")
        return

    print(f"Found full bucket name: {bucket_name_full}")

    # 2. Use full bucket name as is
    parsed_bucket_name = bucket_name_full
    print(f"Attempting to connect to bucket named: '{parsed_bucket_name}'")

    # 3. Check credentials
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("ERROR: Environment variable GOOGLE_APPLICATION_CREDENTIALS not found.")
        print("Make sure your .env file contains: GOOGLE_APPLICATION_CREDENTIALS=service_account.json")
        return
    
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file '{credentials_path}' not found.")
        return
    
    print(f"Using credentials file: {credentials_path}")

    # 4. Attempt connection
    try:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(parsed_bucket_name)
        print("\n✅ SUCCESS! Connected to bucket.")
        print(f"  Bucket ID: {bucket.id}")
        print(f"  Name: {bucket.name}")
        print(f"  Location: {bucket.location}")
        print(f"  Creation time: {bucket.time_created}")

    except exceptions.NotFound:
        print(f"\n❌ ERROR 404: Bucket named '{parsed_bucket_name}' not found.")
        print("  Check that the name in FIREBASE_STORAGE_BUCKET in your .env file is correct.")
        print("  Also make sure the service account has 'Storage Object Viewer' permission for this bucket.")
    
    except exceptions.Forbidden:
        print(f"\n❌ ERROR 403: Access to bucket '{parsed_bucket_name}' is forbidden.")
        print("  This means the credentials are correct, but the service account does not have enough rights.")
        print("  Go to Google Cloud Console -> IAM & Admin -> Service Accounts,")
        print("  find the relevant account and grant it the 'Storage Admin' or at least 'Storage Object Admin' role.")

    except Exception as e:
        print(f"\n❌ OTHER ERROR OCCURRED: {e}")

    print("\n--- Test completed ---")


if __name__ == "__main__":
    test_gcs_connection()
