from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import aiosqlite

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 템플릿 설정
templates = Jinja2Templates(directory="pages")

# 데이터베이스 초기화
@app.on_event("startup")
async def startup():
    app.state.db = await aiosqlite.connect('database.db')
    await app.state.db.execute('''
        CREATE TABLE IF NOT EXISTS survey_responses (
            id INTEGER PRIMARY KEY,
            question TEXT,
            response TEXT
        )
    ''')
    await app.state.db.commit()

# 데이터베이스 종료
@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()

# 데이터 모델 정의
class SurveyResponse(BaseModel):
    question: str
    response: str

# 기본 페이지 엔드포인트
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# 다른 페이지 엔드포인트 예시
@app.get("/review", response_class=HTMLResponse)
async def read_review(request: Request):
    return templates.TemplateResponse("review.html", {"request": request})

# 데이터 저장 엔드포인트
@app.post("/submit-survey")
async def submit_survey(survey_response: SurveyResponse):
    if not survey_response.question or not survey_response.response:
        raise HTTPException(status_code=400, detail="유효하지 않은 요청 데이터")
    
    async with app.state.db.execute(
        "INSERT INTO survey_responses (question, response) VALUES (?, ?)",
        (survey_response.question, survey_response.response)
    ) as cursor:
        await app.state.db.commit()
        return {"message": "데이터 저장 성공"}

# 데이터 조회 엔드포인트
@app.get("/get-responses")
async def get_responses():
    async with app.state.db.execute("SELECT * FROM survey_responses") as cursor:
        rows = await cursor.fetchall()
        return [{"id": row[0], "question": row[1], "response": row[2]} for row in rows]

# 서버 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000) 