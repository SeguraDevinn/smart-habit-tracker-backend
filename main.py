from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/ping")
def ping():
    return {"message": "pong 🏓"}

# --- Habits CRUD ---

@app.get("/habits")
def get_habits(db: Session = Depends(get_db)):
    return db.query(models.Habit).all()

@app.post("/habits")
def create_habit(habit: dict, db: Session = Depends(get_db)):
    # create a new habit
    new_habit = models.Habit(
        name = habit["name"],
        description=habit.get("description", ""),
        is_positive=habit.get("is_positive", True),
        target_per_day=habit.get("target_per_day", 1),
        user_id=habit.get("user_id", 1)
    )
    # add it to database
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit

@app.post("/habit/{habit_id}/log")
def log_habit(habit_id: int, log_data: dict, db: Session = Depends(get_db)):
    # create a new log
    new_log = models.HabitLog(
        habit_id=habit_id,
        count=log_data.get("count",1),
        status=log_data.get("status", "completed")
    )
    # add it to database
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

@app.get("/habits/{habit_id}/logs")
def get_logs(habit_id: int, db: Session = Depends(get_db)):
    return db.query(models.HabitLog).filter(models.HabitLog.habit_id == habit_id).all()


# --Users CRUD --


@app.post("/users")
def create_user(user: dict, db: Session = Depends(get_db)):
    new_user = models.User(username=user["username"])
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()