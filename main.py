
from fastapi import FastAPI, Depends, Request, Form
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Werknemer, Uur
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from fastapi import Response
from itsdangerous import URLSafeSerializer
from models import User
import hashlib

import traceback
from fastapi.responses import PlainTextResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




SECRET_KEY = "verander-dit-later-naar-iets-geheims"
serializer = URLSafeSerializer(SECRET_KEY)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not hashlib.sha256(password.encode()).hexdigest() == user.password_hash:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Ongeldige login"}
        )

    token = serializer.dumps(user.username)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("session", token, httponly=True)
    return response



def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)




@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Urenregistratie</h2>
    <ul>
      <li><a href="/werknemers">Werknemers</a></li>
      <li><a href="/uren">Uren</a></li>
      <li><a href="/factuur">Factuur maken</a></li>
    </ul>
    """


@app.get("/werknemers", response_class=HTMLResponse)
def werknemers(request: Request, db: Session = Depends(get_db)):
    werknemers = db.query(Werknemer).all()
    return templates.TemplateResponse(
        "werknemers.html",
        {"request": request, "werknemers": werknemers}
    )

@app.post("/werknemers")
def werknemer_toevoegen(
    naam: str = Form(...),
    adres: str = Form(...),
    uursalaris: float = Form(...),
    db: Session = Depends(get_db)
):
    w = Werknemer(naam=naam, adres=adres, uursalaris=uursalaris)
    db.add(w)
    db.commit()
    return {"status": "opgeslagen"}

@app.get("/uren", response_class=HTMLResponse)
def uren(request: Request, db: Session = Depends(get_db)):
    werknemers = db.query(Werknemer).all()
    return templates.TemplateResponse(
        "uren.html",
        {"request": request, "werknemers": werknemers}
    )

@app.post("/uren")
def uren_opslaan(
    werknemer_id: int = Form(...),
    periode: str = Form(...),
    aantal_uren: float = Form(...),
    db: Session = Depends(get_db)
):
    uur = Uur(
        werknemer_id=werknemer_id,
        periode=periode,
        aantal_uren=aantal_uren
    )
    db.add(uur)
    db.commit()
    return {"status": "opgeslagen"}


@app.get("/factuur", response_class=HTMLResponse)
def factuur_selectie(request: Request, db: Session = Depends(get_db)):
    werknemers = werknemers = db.query(Werknemer).all()

    periodes = (
        db.query(Uur.periode)
        .distinct()
        .order_by(Uur.periode)
        .all()
    )
    periodes = [p[0] for p in periodes]

    return templates.TemplateResponse(
        "factuur_selectie.html",
        {
            "request": request,
            "werknemers": werknemers,
            "periodes": periodes
        }
    )


@app.get("/factuur_resultaat")
def factuur_resultaat(werknemer_id: int, periode: str):
    return RedirectResponse(
        url=f"/factuur/{werknemer_id}/{periode}",
        status_code=302
    )


@app.get("/factuur/{werknemer_id}/{periode}", response_class=HTMLResponse)
def factuur(
    werknemer_id: int,
    periode: str,
    request: Request,
    db: Session = Depends(get_db)
):
    werknemer = db.query(Werknemer).get(werknemer_id)

    uren = db.query(Uur).filter(
        Uur.werknemer_id == werknemer_id,
        Uur.periode == periode
    ).all()

    totaal_uren = sum(u.aantal_uren for u in uren)
    bedrag = totaal_uren * werknemer.uursalaris

    return templates.TemplateResponse(
        "factuur.html",
        {
            "request": request,
            "werknemer": werknemer,
            "periode": periode,
            "totaal_uren": totaal_uren,
            "uurtarief": werknemer.uursalaris,
            "bedrag": bedrag
        }
    )

@app.get("/create_admin", response_class=PlainTextResponse)
def create_admin():
    try:
        db = SessionLocal()

        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            return "admin bestaat al"

        user = User(
            username="admin",
            password_hash="test"
        )
        db.add(user)
        db.commit()

        return "admin aangemaakt"

    except Exception:
        return traceback.format_exc()

    finally:
        db.close()









