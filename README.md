# 🏃‍♂️ Run AI Coach

Et personligt hobby‑projekt, der **automatisk henter løbedata fra Strava** og kører analyser i skyen ved hjælp af **GitHub Actions**.

Projektet er bygget som et lærings‑ og eksperimentprojekt med fokus på:
- automatisering
- cloud‑jobs (gratis)
- senere AI‑analyse og e‑mail‑rapportering

---

## ✅ Hvad gør projektet lige nu?

- ⏰ Kører **automatisk hver dag** via GitHub Actions (cron)
- 🔐 Autentificerer mod **Strava API** (OAuth + refresh token)
- 🏃 Henter de **seneste aktiviteter** fra Strava
- 📄 Printer aktiviteternes data i **GitHub Actions logs**

> Dette er et MVP / proof‑of‑concept.  
> Næste skridt er analyse, AI‑tekst og mail‑output.

---

## 🧱 Arkitektur (overblik)

---

## 📁 Projektstruktur

---

## ⚙️ Forudsætninger

- GitHub‑konto
- Strava‑konto med aktiviteter
- Strava API App (Client ID / Secret)
- Repository skal være **public** (for gratis GitHub Actions)

---

## 🔐 Secrets (meget vigtigt)

Projektet bruger GitHub Secrets til at gemme følsomme oplysninger.

Disse skal oprettes i:
**Repository → Settings → Secrets and variables → Actions**

| Secret navn | Beskrivelse |
|------------|------------|
| `STRAVA_CLIENT_ID` | Client ID fra Strava API app |
| `STRAVA_CLIENT_SECRET` | Client Secret fra Strava API app |
| `STRAVA_REFRESH_TOKEN` | OAuth refresh token |

> ⚠️ Secrets må **aldrig** ligge direkte i kode eller commits.

---

## ▶️ Sådan kører workflowet

### Automatisk
- Kører **dagligt kl. 05:15 UTC**
- Styres af cron i `.github/workflows/daily.yml`

### Manuelt (til test)
1. Gå til fanen **Actions**
2. Vælg **Daily test run**
3. Klik **Run workflow**

Output kan ses direkte i Actions‑logs.

---

## 🧪 Eksempel på output (logs)

---

## 🛣️ Planlagte næste trin

- [ ] Gemme Strava‑data som CSV / JSON
- [ ] Beregne uge‑km, belastning og trends
- [ ] AI‑genereret træningsfeedback
- [ ] Automatisk e‑mail‑rapport
- [ ] Udvidelse til fodbold / golf data

---

## 📌 Noter

- Projektet er et **hobby‑ og læringsprojekt**
- Ingen data deles offentligt
- Kører udelukkende på gratis cloud‑tjenester

---

## 👤 Forfatter

Allan Graver Christensen  
Senior Mechanical Engineer & sports‑/AI‑entusiast
