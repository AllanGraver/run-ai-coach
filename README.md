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
