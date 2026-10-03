import json, os, sqlite3
from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.security import check_password_hash, generate_password_hash

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "clinic.db")
BASE_MEDS = json.load(open(os.path.join(HERE, "medicines.json"), encoding="utf-8"))
FREQ = ["1-0-0 (OD morning)", "0-0-1 (HS night)", "1-0-1 (BD)", "1-1-1 (TDS)", "1-1-1-1 (QID)", "SOS (if needed)", "Stat"]
TIME = ["After food", "Before food", "With food", "Empty stomach"]
FIELDS = ["co", "dx", "kco", "pho", "sxho", "allho", "bp", "p", "spo2", "t", "cns", "cvs", "rs", "pa", "adv"]

st.markdown("""
<style>
.block-container{max-width:900px;padding-top:1.5rem}
div[data-baseweb="input"] > div, div[data-baseweb="base-input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"]{
  background:#121816 !important;border:1px solid #2c3835 !important;border-radius:8px !important}
textarea, input{color:#e6eeeb !important;font-size:16px !important}
[data-testid="stCaptionContainer"] p{color:#e6eeeb !important;font-size:15px !important}
label p{color:#e6eeeb !important;font-size:16px !important;font-weight:600 !important}
h3{color:#2dd4bf !important;text-transform:uppercase;letter-spacing:.05em;font-size:14px !important}
[data-testid="stTabs"] [role="tablist"]{gap:8px;border-bottom:none}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"]{display:none}
[data-testid="stTabs"] button[role="tab"]{flex:1;justify-content:center;padding:10px;border:1px solid #2dd4bf;
  border-radius:8px;background:transparent;color:#2dd4bf}
[data-testid="stTabs"] button[role="tab"] p{color:inherit !important}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{background:#2dd4bf;color:#fff}
[data-testid="stTabs"] [role="tabpanel"]{background:#1b2321;border:1px solid #2c3835;border-radius:12px;padding:16px;margin-top:12px}
.stButton > button, .stDownloadButton > button{border-radius:8px;border:1px solid #2dd4bf;background:transparent;color:#2dd4bf}
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"]{background:#2dd4bf;color:#fff}
[data-testid="stExpander"]{background:#121816;border:1px solid #2c3835;border-radius:10px}
</style>
""", unsafe_allow_html=True)


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS doctors(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, name TEXT, clinic TEXT);
    CREATE TABLE IF NOT EXISTS patients(reg TEXT PRIMARY KEY, name TEXT, age TEXT, sex TEXT, mobile TEXT);
    CREATE TABLE IF NOT EXISTS visits(id INTEGER PRIMARY KEY, reg TEXT, date TEXT, doctor TEXT, clinic TEXT, data TEXT);
    CREATE TABLE IF NOT EXISTS custom_meds(name TEXT PRIMARY KEY);
    """)
    c.commit(); c.close()


def get_patient(reg):
    c = conn()
    p = c.execute("SELECT * FROM patients WHERE reg=?", (reg,)).fetchone()
    c.close()
    return dict(p) if p else None


def get_visits(reg):
    c = conn()
    rows = c.execute("SELECT * FROM visits WHERE reg=? ORDER BY id", (reg,)).fetchall()
    c.close()
    out = []
    for r in rows:
        v = json.loads(r["data"]); v.update(date=r["date"], doctor=r["doctor"], clinic=r["clinic"]); out.append(v)
    return out


def all_meds():
    c = conn()
    extra = [r["name"] for r in c.execute("SELECT name FROM custom_meds")]
    c.close()
    return sorted(set(BASE_MEDS + extra))


def make_pdf(reg):
    p, vs = get_patient(reg), get_visits(reg)
    ss = getSampleStyleSheet()
    n = ParagraphStyle("n", parent=ss["Normal"], fontSize=9, leading=12)
    P = lambda t: Paragraph(escape(str(t or "")).replace("\n", "<br/>"), n)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28)
    el = [Paragraph(f"<b>{escape(vs[-1]['clinic'] if vs else 'Clinic')}</b>", ParagraphStyle("c", parent=n, alignment=1, fontSize=14, leading=18)),
          Paragraph("<b>OPD CLINICAL RECORD</b>", ParagraphStyle("c2", parent=n, alignment=1, fontSize=11)), Spacer(1, 8)]
    t = Table([[P(f"Name: {p['name']}"), P(f"Age/Sex: {p['age']} / {p['sex']}"), P(f"Reg no.: {p['reg']}"), P(f"Mobile: {p['mobile']}")]],
              colWidths=[165, 100, 135, 139])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .7, colors.black)]))
    el += [t, Spacer(1, 8)]
    for i, v in enumerate(vs, 1):
        g = lambda k: escape(v.get(k, "") or "")
        left = (f"<b>C/o:</b> {g('co')}<br/><b>K/c/o:</b> {g('kco')}<br/><b>P/h/o:</b> {g('pho')}<br/><b>Sx/h/o:</b> {g('sxho')}<br/>"
                f"<b>All/h/o:</b> {g('allho')}<br/><br/><b>O/E:</b> BP {g('bp')} | P {g('p')} | SpO2 {g('spo2')} | T {g('t')}<br/>"
                f"<b>S/E:</b> CNS {g('cns')} | CVS {g('cvs')} | RS {g('rs')} | P/A {g('pa')}")
        rx = "<br/>".join(f"{j}. {escape(m['n'])} {escape(m.get('d',''))} - {escape(m.get('f',''))} x {escape(m.get('days',''))} days, {escape(m.get('w',''))}"
                          for j, m in enumerate(v.get("meds", []), 1))
        right = f"<b>Diagnosis:</b> {g('dx')}<br/><br/><b>Rx:</b><br/>{rx}" + (f"<br/><br/><b>Advice:</b> {g('adv')}" if v.get("adv") else "")
        head = f"<b>Visit {i} - {escape(v['date'] or '')} - {escape(v['doctor'] or '')} ({escape(v['clinic'] or '')})</b>"
        t = Table([[Paragraph(head, n), ""], [Paragraph(left, n), Paragraph(right, n)]], colWidths=[240, 299])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .7, colors.black), ("SPAN", (0, 0), (1, 0)), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eeeb"))]))
        el += [t, Spacer(1, 8)]
    el.append(Paragraph("Generated by ClinicRecord. Show this record to any clinic to continue treatment without repeating history.", ParagraphStyle("f", parent=n, fontSize=7)))
    doc.build(el)
    return buf.getvalue()


# ---------------- login ----------------
def login_page():
    st.title("🩺 ClinicRecord")
    a, b = st.tabs(["Doctor login", "New doctor? Register"])
    with a:
        u = st.text_input("Username", key="lu")
        pw = st.text_input("Password", type="password", key="lp")
        if st.button("Login"):
            c = conn(); r = c.execute("SELECT * FROM doctors WHERE username=?", (u.strip(),)).fetchone(); c.close()
            if r and check_password_hash(r["password"], pw):
                st.session_state.doc = {"name": r["name"], "clinic": r["clinic"]}; st.rerun()
            else:
                st.error("Wrong username or password")
    with b:
        name = st.text_input("Doctor name (e.g. Dr. Mohd Amir Khan)")
        clinic = st.text_input("Clinic / hospital name")
        ru = st.text_input("Choose username", key="ru")
        rp = st.text_input("Choose password", type="password", key="rp")
        if st.button("Register & login"):
            if not all(x.strip() for x in (name, clinic, ru, rp)):
                st.error("Fill all fields")
            else:
                try:
                    c = conn()
                    c.execute("INSERT INTO doctors(username,password,name,clinic) VALUES(?,?,?,?)", (ru.strip(), generate_password_hash(rp), name.strip(), clinic.strip()))
                    c.commit(); c.close()
                    st.session_state.doc = {"name": name.strip(), "clinic": clinic.strip()}; st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already taken")


# ---------------- main ----------------
def load_patient():
    reg = st.session_state.get("reg", "").strip()
    p = get_patient(reg)
    st.session_state.prev = None
    if not p:
        st.session_state.prevmsg = "New patient."
        return
    st.session_state.f_name, st.session_state.f_age = p["name"], int(p["age"] or 0)
    st.session_state.f_sex, st.session_state.f_mobile = p["sex"] or "M", p["mobile"] or ""
    vs = get_visits(reg)
    if vs:
        for k in ("kco", "pho", "sxho", "allho"):
            st.session_state[k] = vs[-1].get(k, "")
        l = vs[-1]
        st.session_state.prevmsg = (f"**{len(vs)} previous visit(s)** - last: {l['date']} at {l['clinic']}, Dx: {l.get('dx') or '-'}, "
                                    f"Rx: {', '.join(m['n'] for m in l['meds']) or '-'}. Chronic history carried forward.")


def visit_page():
    st.text_input("Registration no.", key="reg", on_change=load_patient, help="Type and press Enter to load history")
    if st.session_state.get("prevmsg"):
        st.caption(st.session_state.prevmsg)
    c = st.columns(3)
    c[0].text_input("Name", key="f_name"); c[1].number_input("Age", 0, 120, key="f_age")
    c[2].selectbox("Sex", ["M", "F", "Other"], key="f_sex")
    c = st.columns(2)
    c[0].text_input("Mobile no.", key="f_mobile"); d = c[1].date_input("Date", date.today())

    st.subheader("History")
    c = st.columns(2)
    c[0].text_area("C/o (chief complaint)", key="co", height=80); c[1].text_area("Diagnosis", key="dx", height=80)
    c[0].text_area("K/c/o (known case of)", key="kco", height=80); c[1].text_area("P/h/o (past history)", key="pho", height=80)
    c[0].text_area("Sx/h/o (surgical history)", key="sxho", height=80); c[1].text_area("All/h/o (allergy history)", key="allho", height=80)
    st.subheader("O/E (on examination)")
    c = st.columns(4)
    c[0].text_input("BP (mmHg)", key="bp"); c[1].text_input("P (/min)", key="p")
    c[2].text_input("SpO2 (%)", key="spo2"); c[3].text_input("T (°F)", key="t")
    st.subheader("S/E (systemic examination)")
    c = st.columns(4)
    c[0].text_input("CNS", key="cns"); c[1].text_input("CVS", key="cvs"); c[2].text_input("RS", key="rs"); c[3].text_input("P/A", key="pa")

    st.subheader("Rx (treatment)")
    meds_list = all_meds()
    st.session_state.setdefault("nm", 1)
    for i in range(st.session_state.nm):
        c = st.columns([3, 1.2, 2, 1, 2])
        c[0].selectbox("Medicine (type to search)", meds_list, index=None, accept_new_options=True, key=f"mn{i}", placeholder="Type to search medicine")
        c[1].text_input("Dose", key=f"md{i}"); c[2].selectbox("Frequency", FREQ, key=f"mf{i}")
        c[3].text_input("Days", key=f"mdays{i}"); c[4].selectbox("When", TIME, key=f"mw{i}")
    b = st.columns([1, 1, 4])
    if b[0].button("+ Add medicine"): st.session_state.nm += 1; st.rerun()
    if b[1].button("- Remove") and st.session_state.nm > 1: st.session_state.nm -= 1; st.rerun()
    st.text_area("Advice / follow-up", key="adv", height=70)

    if st.button("Save visit & create PDF", type="primary"):
        reg, name = st.session_state.get("reg", "").strip(), st.session_state.get("f_name", "").strip()
        if not reg or not name:
            st.error("Registration no. and name are required"); return
        meds = [{"n": st.session_state.get(f"mn{i}"), "d": st.session_state.get(f"md{i}", ""), "f": st.session_state.get(f"mf{i}"),
                 "days": st.session_state.get(f"mdays{i}", ""), "w": st.session_state.get(f"mw{i}")} for i in range(st.session_state.nm)]
        meds = [m for m in meds if m["n"]]
        visit = {k: st.session_state.get(k, "") for k in FIELDS}; visit["meds"] = meds
        doc = st.session_state.doc
        c = conn()
        c.execute("INSERT OR REPLACE INTO patients VALUES(?,?,?,?,?)", (reg, name, str(st.session_state.f_age), st.session_state.f_sex, st.session_state.f_mobile))
        c.execute("INSERT INTO visits(reg,date,doctor,clinic,data) VALUES(?,?,?,?,?)", (reg, str(d), doc["name"], doc["clinic"], json.dumps(visit)))
        for m in meds:
            if m["n"] not in BASE_MEDS:
                c.execute("INSERT OR IGNORE INTO custom_meds VALUES(?)", (m["n"],))
        c.commit(); c.close()
        st.session_state.pdf = (reg, make_pdf(reg))
        st.success("Visit saved")
    if st.session_state.get("pdf"):
        reg, data = st.session_state.pdf
        st.download_button("⬇ Download patient PDF", data, file_name=f"record_{reg}.pdf", mime="application/pdf")


def patients_page():
    q = st.text_input("Search name, mobile or reg no.").lower()
    c = conn(); rows = c.execute("SELECT * FROM patients ORDER BY name").fetchall(); c.close()
    shown = [r for r in rows if q in (r["reg"] + r["name"] + (r["mobile"] or "")).lower()]
    if not shown: st.info("No patients yet.")
    for r in shown:
        vs = get_visits(r["reg"])
        with st.expander(f"{r['name']} · {r['reg']} · {r['mobile']}  ({len(vs)} visits)"):
            for v in vs:
                st.write(f"**{v['date']}** - {v.get('dx') or '-'} - {', '.join(m['n'] for m in v['meds'])}")
            st.download_button("⬇ Download PDF", make_pdf(r["reg"]), file_name=f"record_{r['reg']}.pdf", mime="application/pdf", key="dl" + r["reg"])


init_db()
if "doc" not in st.session_state:
    login_page()
else:
    doc = st.session_state.doc
    h = st.columns([4, 1])
    h[0].markdown(f"## 🩺 ClinicRecord\n{doc['clinic']} · {doc['name']}")
    if h[1].button("Logout"):
        st.session_state.clear(); st.rerun()
    t1, t2 = st.tabs(["New visit", "Patients"])
    with t1: visit_page()
    with t2: patients_page()
