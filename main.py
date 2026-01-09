from fastapi import (
    FastAPI,
    Depends,
    Request,
    Form,
    Response,
    Cookie
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import hashlib

from database import SessionLocal
from models import User, Werknemer, Uur

# -------------------------------------------------
# App setup
# -------------------------------------------------

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# -------------------------------------------------
# Database dependency
# -------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------
# Auth helper (LOGIN VERPLICHT)
# -------------------------------------------------

def require_login(session_user: str | None = Cookie(default=None)):
    if not session_user:
        return RedirectResponse("/login", status_code=302)
    return session_user

# -------------------------------------------------
# Login / Logout
# -------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )

@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": {}, "error": "Onjuiste inloggegevens"}
        )

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user.password_hash:
        return templates.TemplateResponse(
            "login.html",
            {"request": {}, "error": "Onjuiste inloggegevens"}
        )

    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        key="session_user",
        value=user.username,
        httponly=True,
        samesite="lax"
    )
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session_user")
    return response

# -------------------------------------------------
# Beveiligde routes
# -------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(user=Depends(require_login)):
    return """
    <h2>Urenregistratie</h2>
    <ul>
      <li><a href="/werknemers">Werknemers</a></li>
      <li><a href="/uren">Uren</a></li>
      <li><a href="/factuur">Factuur maken</a></li>
      <li><a href="/logout">Uitloggen</a></li>
    </ul>
    """

# -------------------------------------------------
# Werknemers
# -------------------------------------------------

@app.get("/werknemers", response_class=HTMLResponse)
def werknemers(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_login)
):
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
    db: Session = Depends(get_db),
    user=Depends(require_login)
):
    w = Werknemer(naam=naam, adres=adres, uursalaris=uursalaris)
    db.add(w)
    db.commit()
    return RedirectResponse("/werknemers", status_code=302)

# -------------------------------------------------
# Uren
# -------------------------------------------------

@app.get("/uren", response_class=HTMLResponse)
def uren(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_login)
):
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
    db: Session = Depends(get_db),
    user=Depends(require_login)
):
    uur = Uur(
        werknemer_id=werknemer_id,
        periode=periode,
        aantal_uren=aantal_uren
    )
    db.add(uur)
    db.commit()
    return RedirectResponse("/uren", status_code=302)

# -------------------------------------------------
# Facturen
# -------------------------------------------------

@app.get("/factuur", response_class=HTMLResponse)
def factuur_selectie(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_login)
):
    werknemers = db.query(Werknemer).all()
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

@app.get("/factuur/{werknemer_id}/{periode}", response_class=HTMLResponse)
def factuur(
    werknemer_id: int,
    periode: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_login)
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
