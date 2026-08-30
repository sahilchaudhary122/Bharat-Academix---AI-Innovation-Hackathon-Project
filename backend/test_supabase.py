from database.supabase_client import supabase

test_student = {
    "name": "Test Student",
    "grade": "10",
    "preferred_language": "English",
    "current_level": "beginner",
    "learning_goals": "Learn Physics"
}


response = (
    supabase
    .table("students")
    .insert(test_student)
    .execute()
)

print("Student inserted successfully!")
print(response.data)