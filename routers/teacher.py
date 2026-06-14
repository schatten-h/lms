import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models import User, Course, Lesson, Quiz, Question, Choice, Enrollment
from routers.auth import get_current_user
from schemas import CourseCreate, QuizCreate

router = APIRouter()

@router.post("/courses")
def create_course(course: CourseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "teacher": 
        raise HTTPException(status_code=403, detail="Accès refusé")
    new_course = Course(title=course.title, module_id=course.module_id, teacher_id=user.id)
    db.add(new_course)
    db.commit()
    return {"msg": "Cours créé avec succès"}

@router.get("/courses")
def teacher_list_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "teacher": 
        raise HTTPException(status_code=403, detail="Accès refusé")
    courses = db.query(Course).filter(Course.teacher_id == user.id).all()
    return [{"id": c.id, "title": c.title, "module_id": c.module_id} for c in courses]

@router.post("/lessons")
def upload_lesson(
    title: str = Form(...),
    course_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role != "teacher": 
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Vérification de sécurité optionnelle pour s'assurer que le cours appartient à l'enseignant
    course = db.query(Course).filter(Course.id == course_id, Course.teacher_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Cours non trouvé ou accès non autorisé")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext == '.pdf':
        subfolder = "pdfs"
        content_type = "pdf"
    elif file_ext == '.mp4':
        subfolder = "videos"
        content_type = "video"
    else:
        raise HTTPException(status_code=400, detail="Format non supporté (uniquement PDF ou MP4)")

    filename = f"{uuid.uuid4()}{file_ext}"
    relative_path = f"/uploads/{subfolder}/{filename}"
    absolute_path = os.path.join("uploads", subfolder, filename)

    with open(absolute_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_lesson = Lesson(title=title, content_type=content_type, file_path=relative_path, course_id=course_id)
    db.add(new_lesson)
    db.commit()
    
    return {"msg": "Leçon ajoutée avec succès", "lesson_id": new_lesson.id}

@router.post("/quizzes")
def create_quiz(quiz_data: QuizCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "teacher": 
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    new_quiz = Quiz(lesson_id=quiz_data.lesson_id)
    db.add(new_quiz)
    db.flush()
    
    for q in quiz_data.questions:
        new_question = Question(quiz_id=new_quiz.id, text=q.text)
        db.add(new_question)
        db.flush()
        
        for c in q.choices:
            new_choice = Choice(question_id=new_question.id, text=c.text, is_correct=c.is_correct)
            db.add(new_choice)
            
    db.commit()
    return {"msg": "Quiz complet créé avec succès"}