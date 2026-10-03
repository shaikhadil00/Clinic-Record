# 🩺 ClinicRecord

A simple digital patient record system for clinics. The doctor fills in the patient's visit once, picks medicines from a dropdown, and the patient gets a PDF they can show at any other clinic. Treatment history follows the patient, so nobody has to start from zero.

**🔗 Live demo:** https://clinic-record.onrender.com

> The first load can take about a minute if the app has been idle (free hosting wakes up on demand).
> This is a demo, so please use **fake patient data only**.

## Features

- 👨‍⚕️ Doctor registration and login, with the clinic name added to every record
- 📝 Visit form in the clinic's own format: C/o, Diagnosis, K/c/o, P/h/o, Sx/h/o, All/h/o
- 🩺 O/E (BP, Pulse, SpO2, Temp) and S/E (CNS, CVS, RS, P/A)
- 💊 Rx with a searchable medicine dropdown, dose, frequency, days and before/after food
- 🔁 Patient history loads by Registration no. and carries forward chronic and allergy history
- 📄 One-click PDF in the OPD Clinical Record layout, with all visits listed
- 🔎 Patients tab to search records and download PDFs
- 🌙 Dark teal theme

## How to use

1. Open the live demo link.
2. Open the **New doctor? Register** tab and create a doctor account.
3. Enter a Registration no. and the patient details.
4. Fill in the history, examination and Rx, then click **Save visit & create PDF**.
5. Click **Download patient PDF** to get the record.

## Run it on your computer

```bash
git clone https://github.com/shaikhadil00/Clinic-Record.git
cd Clinic-Record
pip install -r requirements.txt
streamlit run app.py
```

## Tech stack

- Python and Streamlit (interface)
- SQLite (database)
- ReportLab (PDF generation)
- Werkzeug (password hashing)

## Project files

| File | Purpose |
|------|---------|
| `app.py` | Full application: login, forms, database, PDF |
| `medicines.json` | Medicine dropdown list (edit to add more) |
| `requirements.txt` | Python packages |
| `.streamlit/config.toml` | Dark theme settings |

## Roadmap

- [ ] Permanent cloud database (MongoDB)
- [ ] Patient consent and OTP before sharing history between clinics
- [ ] Clinic logo and doctor signature on the PDF
- [ ] Send the PDF by WhatsApp or SMS
- [ ] Drug interaction and allergy warnings

## Disclaimer

This is a prototype for testing. It is not yet approved for storing real patient data.
