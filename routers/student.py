from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Module, Course, Lesson, Quiz, Question, Choice, Enrollment, Certificate, QuizResult
from routers.auth import get_current_user
from schemas import SubmitQuiz

router = APIRouter()

@router.get("/dashboard")
def student_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "student": raise HTTPException(status_code=403, detail="Accès refusé")
    
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == user.id).all()
    certs = db.query(Certificate).filter(Certificate.student_id == user.id).all()
    
    enr_data = [{"course_id": e.course_id, "title": e.course.title, "progress": e.progress} for e in enrollments]
    cert_data = []
    for c in certs:
        module = db.query(Module).filter(Module.id == c.module_id).first()
        cert_data.append({
            "module_id": c.module_id,
            "module_title": module.title if module else "Module supprimé",
            "date": c.issue_date
        })
    
    return {"enrollments": enr_data, "certificates": cert_data}
@router.get("/lessons/by_course/{course_id}")
def list_lessons_by_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lessons = db.query(Lesson).filter(Lesson.course_id == course_id).all()
    return [{"id": l.id, "title": l.title, "content_type": l.content_type, "file_path": l.file_path} for l in lessons]


@router.get("/modules")
def student_list_modules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Retourne la liste des modules disponibles pour un utilisateur authentifié."""
    mods = db.query(Module).all()
    return [{"id": m.id, "title": m.title, "description": m.description} for m in mods]

@router.get("/courses")
def list_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "student": raise HTTPException(status_code=403, detail="Accès refusé")
    courses = db.query(Course).all()
    result = []
    for c in courses:
        module = db.query(Module).filter(Module.id == c.module_id).first()
        teacher = db.query(User).filter(User.id == c.teacher_id).first()
        enrollment = db.query(Enrollment).filter_by(student_id=user.id, course_id=c.id).first()
        result.append({
            "id": c.id,
            "title": c.title,
            "module_title": module.title if module else None,
            "teacher_name": teacher.username if teacher else None,
            "enrolled": enrollment is not None,
            "progress": enrollment.progress if enrollment else 0
        })
    return result

@router.get("/courses/{course_id}/lessons")
def list_course_lessons(course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "student": raise HTTPException(status_code=403, detail="Accès refusé")
    lessons = db.query(Lesson).filter(Lesson.course_id == course_id).all()
    return [{"id": l.id, "title": l.title, "content_type": l.content_type, "file_path": l.file_path} for l in lessons]

@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {"student", "teacher", "admin"}:
        raise HTTPException(status_code=403, detail="Accès refusé")
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Leçon non trouvée")
    return {
        "id": lesson.id,
        "title": lesson.title,
        "content_type": lesson.content_type,
        "file_path": lesson.file_path,
        "course_id": lesson.course_id
    }

@router.get("/lessons/{lesson_id}/quiz")
def get_quiz(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "student": raise HTTPException(status_code=403, detail="Accès refusé")
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson or not lesson.quiz:
        raise HTTPException(status_code=404, detail="Quiz non trouvé pour cette leçon")

    quiz = lesson.quiz
    questions_data = []
    for question in quiz.questions:
        questions_data.append({
            "id": question.id,
            "text": question.text,
            "choices": [{"id": c.id, "text": c.text} for c in question.choices]
        })
    return {"quiz_id": quiz.id, "lesson_id": lesson.id, "questions": questions_data}

@router.post("/enroll/{course_id}")
def enroll(course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "student": raise HTTPException(status_code=403, detail="Accès refusé")
    if db.query(Enrollment).filter_by(student_id=user.id, course_id=course_id).first():
        return {"msg": "Déjà inscrit"}
    
    enr = Enrollment(student_id=user.id, course_id=course_id, progress=0.0)
    db.add(enr)
    db.commit()
    return {"msg": "Inscription validée"}

@router.post("/quiz/{quiz_id}/submit")
def submit_quiz(quiz_id: int, sub: SubmitQuiz, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "student": raise HTTPException(status_code=403, detail="Accès refusé")
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz: raise HTTPException(status_code=404, detail="Quiz non trouvé")
    
    correct_answers = 0
    total_questions = len(quiz.questions)
    
    for answer in sub.answers:
        choice = db.query(Choice).filter(Choice.id == answer.choice_id, Choice.question_id == answer.question_id).first()
        if choice and choice.is_correct:
            correct_answers += 1
            
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    passed = score >= 50.0  
    
    qr = db.query(QuizResult).filter_by(student_id=user.id, quiz_id=quiz_id).first()
    if qr:
        qr.score = score
        qr.passed = passed
    else:
        qr = QuizResult(student_id=user.id, quiz_id=quiz_id, score=score, passed=passed)
        db.add(qr)
    db.commit()
    
    course_id = quiz.lesson.course_id
    course_lessons = db.query(Lesson).filter(Lesson.course_id == course_id).all()
    total_course_quizzes = sum([1 for l in course_lessons if l.quiz])
    
    if total_course_quizzes > 0:
        passed_quizzes = 0
        for l in course_lessons:
            if l.quiz:
                q_res = db.query(QuizResult).filter_by(student_id=user.id, quiz_id=l.quiz.id, passed=True).first()
                if q_res: passed_quizzes += 1
                
        progress = (passed_quizzes / total_course_quizzes) * 100
        enr = db.query(Enrollment).filter_by(student_id=user.id, course_id=course_id).first()
        if enr: 
            enr.progress = progress
            db.commit()
            
    return {"score": score, "passed": passed, "msg": "Quiz validé!" if passed else "Quiz échoué, veuillez réessayer."}


@router.get("/course/{course_id}/lessons")
def get_course_lessons(course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "student": 
        raise HTTPException(status_code=403, detail="Accès refusé")
        
    # Vérification : l'étudiant est-il bien inscrit ?
    enrollment = db.query(Enrollment).filter_by(student_id=user.id, course_id=course_id).first()
    if not enrollment: 
        raise HTTPException(status_code=403, detail="Vous n'êtes pas inscrit à ce cours")
    
    # Récupération des leçons
    lessons = db.query(Lesson).filter(Lesson.course_id == course_id).all()
    
    output = []
    for l in lessons:
        quiz_data = None
        
        # S'il y a un VRAI quiz créé dans ta base de données, on le récupère
        if l.quiz:
            quiz_data = {
                "id": l.quiz.id,
                "title": l.quiz.title,
                "questions": [
                    {
                        "id": q.id,
                        "text": q.text,
                        "choices": [{"id": c.id, "text": c.text} for c in q.choices]
                    } for q in l.quiz.questions
                ]
            }
        # SI LE QUIZ N'EXISTE PAS ENCORE (ce qui est ton cas actuellement),
        # On force l'affichage d'un faux quiz de test pour que ton HTML l'affiche !
        else:
            quiz_data = {
                "id": 999,
                "title": f"Quiz de validation : {l.title}",
                "questions": [
                    {
                        "id": 101,
                        "text": "Que signifie le 'J' dans AJAX ?",
                        "choices": [
                            {"id": 1, "text": "Java"},
                            {"id": 2, "text": "JavaScript"},
                            {"id": 3, "text": "JQuery"}
                        ]
                    },
                    {
                        "id": 102,
                        "text": "AJAX permet de recharger une page entière.",
                        "choices": [
                            {"id": 4, "text": "Vrai"},
                            {"id": 5, "text": "Faux (Seulement une parstie de la page)"}
                        ]
                    }
                ]
            }
        
        output.append({
            "id": l.id,
            "title": l.title,
            "file_path": l.file_path,
            "quiz": quiz_data
        })
        
    return output