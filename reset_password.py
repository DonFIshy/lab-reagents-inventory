import sqlite3
import bcrypt

# חיבור למסד הנתונים
conn = sqlite3.connect('users.db')
c = conn.cursor()

# בוחרים סיסמה חדשה
new_password = 'NewPassword123!'  # כאן שים את הסיסמה החדשה שתרצה

# גיבוב הסיסמה
hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

# שם המשתמש לאיפוס
username = 'admin'

# עדכון הסיסמה במסד
c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed.decode(), username))

conn.commit()
conn.close()

print("✅ הסיסמה של המשתמש 'admin' אופסה בהצלחה! עכשיו אפשר להתחבר עם הסיסמה החדשה.")
