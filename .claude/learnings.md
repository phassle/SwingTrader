# Learnings

Erfarenheter och misstag från tidigare sessioner. Läs denna fil vid start av nya sessioner för att undvika att upprepa samma fel.

## 2026-03-28: Konstitutionsfil lämnades som tom mall

**Vad hände:** `.specify/memory/constitution.md` var en oifylld mall med platshållare som `[PRINCIPLE_1_NAME]`, trots att README.md refererade till fem konkreta principer. Ingen hade fyllt i den efter att spec-kit scaffoldade projektet.

**Lärdom:** Efter att ett scaffold-verktyg (som spec-kit/specify) körs, kontrollera alltid att genererade mallfiler faktiskt fyllts i med projektspecifikt innehåll. Platshållartext i konfigurationsfiler är en tyst bugg — allt ser komplett ut tills någon faktiskt läser filen.

## 2026-03-28: Benchmark-aggregering misslyckades med tom output

**Vad hände:** `scripts.aggregate_benchmark` producerade en benchmark.json med tomma `runs`-array och nollvärden. Skriptet hittade inte graderingsdatan i katalogstrukturen, troligen för att mappnamnen inte matchade det förväntade mönstret (eval-0, eval-1 etc.) utan använde beskrivande namn (eval-1-signal-to-order).

**Lärdom:** Innan man kör aggregeringsskript, kontrollera vilken katalogstruktur skriptet förväntar sig. Om det inte matchar, antingen anpassa strukturen eller bygg benchmark.json manuellt. Lita inte blint på att "det bara funkar" — verifiera output direkt.

## 2026-03-28: ib_insync vs ib_async — utdaterat bibliotek

**Vad hände:** Under research för TWS-skillen upptäcktes att `ib_insync` (det mest refererade Python-biblioteket för IBKR) inte längre underhålls efter att skaparen Ewald de Wit gick bort 2024. Det har ersatts av `ib_async` under ny organisation (ib-api-reloaded). Många tutorials online refererar fortfarande till `ib_insync`.

**Lärdom:** Kontrollera alltid underhållsstatus för rekommenderade bibliotek. Populärt ≠ aktuellt. För IBKR-integration, använd alltid `ib_async` (pip install ib_async), inte `ib_insync`.

## 2026-03-28: Eval-körningar — testfall bör namnges konsekvent

**Vad hände:** Eval-mapparna namngavs med beskrivande namn (eval-1-signal-to-order, eval-2-getting-started) men aggregeringsskriptet förväntade sig troligen ett enklare mönster. Detta ledde till att benchmark-data inte plockades upp automatiskt.

**Lärdom:** Vid skill-evaluering, använd det exakta mappnamnsformatet som eval-viewer-verktygen förväntar sig, eller verifiera kompatibilitet innan man kör. Konsistens i namngivning sparar felsökningstid.
