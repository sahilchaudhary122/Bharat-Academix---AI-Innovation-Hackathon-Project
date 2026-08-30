import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SECRET_KEY")

if not supabase_url:
    raise ValueError("SUPABASE_URL is not configured.")

if not supabase_key:
    raise ValueError("SUPABASE_SECRET_KEY is not configured.")

supabase: Client = create_client(
    supabase_url,
    supabase_key
)