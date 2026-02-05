from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def get_user_profile(user_id):
    response = supabase.table("profiles") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute()

    return response.data
