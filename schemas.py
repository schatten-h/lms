from pydantic import BaseModel
from typing import List, Optional

class ChoiceCreate(BaseModel):
    text: str
    is_correct: bool

class QuestionCreate(BaseModel):
    text: str
    choices: List[ChoiceCreate]

class QuizCreate(BaseModel):
    lesson_id: int
    questions: List[QuestionCreate]

class SubmitAnswer(BaseModel):
    question_id: int
    choice_id: int

class SubmitQuiz(BaseModel):
    answers: List[SubmitAnswer]

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class ModuleCreate(BaseModel):
    title: str
    description: str

class CourseCreate(BaseModel):
    title: str
    module_id: int

class IssueCertificate(BaseModel):
    student_id: int
    module_id: int