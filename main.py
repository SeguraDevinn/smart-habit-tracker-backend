from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from datetime import datetime, timezone
import models


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "API is active 🚀"}

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


@app.put("/habits/{habit_id}")
def update_habit(habit_id: int, updated_data: dict, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if not habit:
        return {"Error" : "Habit not found"}
    
    for key, value in updated_data.items():
        if hasattr(habit, key):
            setattr(habit, key, value)
    
    db.commit()
    db.refresh(habit)
    return habit

@app.delete("/habits/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if not habit:
        return {"Error": "Habit not found"}
    
    db.delete(habit)
    db.commit()
    return {"message": f"Habit {habit_id} deleted successfully"}


@app.post("/habits/{habit_id}/increment")
def increment_habit(habit_id: int, db: Session = Depends(get_db)):
    # find habit
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if not habit:
        return {"Error": "Habit not found"}
    # Define today's date range
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day ,tzinfo=timezone.utc)
    # find today's log, else create one
    log = (
        db.query(models.HabitLog)
        .filter(models.HabitLog.habit_id == habit_id)
        .filter(models.HabitLog.date >= today_start)
        .first()
    )

    if not log:
        log = models.HabitLog(
            habit_id=habit_id,
            count=1,
            status="completed" if habit.target_per_day <= 1 else "in_progress"
        )
        db.add(log)
    else:
        log.count += 1
        # update if completed
        log.status = "completed" if log.count >= habit.target_per_day else "in_progress"

    db.commit()
    db.refresh(log)

    # attach the log to the habit and then return the response
    response = {
        "habit": {
            "id": habit.id,
            "name": habit.name,
            "description": habit.description,
            "is_positive": habit.is_positive,
            "target_per_day": habit.target_per_day,
        },
        "today_log": {
            "id": log.id,
            "count": log.count,
            "status": log.status,
            "date": log.date,
        }
    }

    return response

@app.get("/habits/progress/{user_id}")
def get_habit_progress(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    habits = db.query(models.Habit).filter(models.Habit.user_id == user_id).all()

    if not habits:
        raise HTTPException(status_code=404, detail="No habits found for this user")

    results = []

    for habit in habits:
        log = (
            db.query(models.HabitLog)
            .filter(models.HabitLog.habit_id == habit.id)
            .filter(models.HabitLog.date >= today_start)
            .first()
        )
        if log:
            count = log.count
            status = log.status
        else:
            count = 0
            status = "in_progress"

        results.append({
            "id": habit.id,
            "name": habit.name,
            "description": habit.description,
            "is_positive": habit.is_positive,
            "target_per_day": habit.target_per_day,
            "today": {
                "count": count,
                "status": status
            }
        })
    return {"user_id": user_id, "habits": results}


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