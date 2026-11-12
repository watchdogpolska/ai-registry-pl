# Wdrożenie produkcyjne

Ten dokument opisuje wymagania aplikacji i zalecany sposób wdrożenia, ale nie
narzuca konkretnego układu serwera. Produkcyjny obraz Docker może zostać użyty
z infrastrukturą i reverse proxy wybranymi przez administratora.

## Wymagania

- Docker lub inny runtime zgodny z OCI,
- MySQL 8,
- domena i reverse proxy obsługujące HTTPS,
- trwała baza MySQL.

Aplikacja nie wymaga trwałego dysku na dane rejestru. Pliki statyczne są
budowane do obrazu aplikacji i serwowane przez WhiteNoise. Bieżące dane
wdrożonej instancji znajdują się w MySQL i są utrzymywane przez panel
administracyjny Django.

Repozytorium zawiera `data/registry.json`, czyli startowy snapshot publicznych
danych rejestru. Może on posłużyć do inicjalizacji nowej bazy, ale nie ma
gwarancji aktualności względem działającej instancji produkcyjnej. Publicznym
źródłem bieżących danych jest eksport CSV generowany przez działający serwis.

## Konfiguracja

Skopiuj przykładowy plik i zastąp wartości przykładowe:

```bash
cp .env.example .env
```

Wymagane zmienne aplikacji:

- `DJANGO_SECRET_KEY` — długi, losowy sekret,
- `DJANGO_ALLOWED_HOSTS` — nazwy hostów rozdzielone przecinkami, bez schematów
  URL,
- `DJANGO_CSRF_TRUSTED_ORIGINS` — zaufane źródła HTTPS rozdzielone przecinkami,
- `DATABASE_URL` — adres połączenia z MySQL.

Przykład:

```text
DJANGO_ALLOWED_HOSTS=registry.example.org
DJANGO_CSRF_TRUSTED_ORIGINS=https://registry.example.org
DATABASE_URL=mysql://registry_user:password@mysql.example.org:3306/ai_registry
```

Jeżeli hasło do bazy zawiera znaki specjalne mające znaczenie w URL, należy je
zakodować.

Nazwa hosta bazy w `DATABASE_URL` musi być osiągalna z kontenera aplikacji.
Przykładowy host `mysql` z `.env.example` jest właściwy dla referencyjnego
`compose.production.yaml`; w innej infrastrukturze należy podać właściwy host
lub usługę bazodanową.

### Reverse proxy i HTTPS

Kontener nasłuchuje HTTP na porcie 8000. TLS może być terminowany przez Nginx,
Traefik, ingress controller, load balancer albo inne reverse proxy.

Jeżeli proxy **nadpisuje** nagłówek `X-Forwarded-Proto` i ustawia go na
`https` dla połączeń HTTPS, ustaw:

```text
DJANGO_TRUST_X_FORWARDED_PROTO=true
```

Nie włączaj tej opcji, jeżeli klient może przekazać własny, niezaufany nagłówek
`X-Forwarded-Proto`, który nie jest nadpisywany przez proxy.

`DJANGO_SECURE_SSL_REDIRECT` jest domyślnie wyłączone, ponieważ w wielu
wdrożeniach przekierowanie HTTP → HTTPS wykonuje reverse proxy. Można je włączyć,
jeżeli to Django ma odpowiadać za przekierowanie.

Bezpieczne ciasteczka sesji i CSRF są domyślnie włączone w konfiguracji
produkcyjnej.

### Publiczny dostęp do kodu źródłowego

Przed publicznym uruchomieniem serwisu należy udostępnić odpowiadający wdrożeniu
kod źródłowy w publicznym repozytorium. Stopka serwisu zawiera link „Kod
źródłowy” wraz z numerem wersji. Link prowadzi do commita, z którego zbudowano
obraz (`APP_COMMIT`), a gdy commit nie jest znany — do repozytorium. Domyślny
adres repozytorium to <https://github.com/watchdogpolska/ai-registry-pl>; można
go zmienić zmienną `SOURCE_CODE_URL`.

## Wersjonowanie

Wydania oznaczane są tagami git w formacie SemVer: `vMAJOR.MINOR.PATCH`
(np. `v1.2.0`, bez sufiksów typu `-rc.1`). Wersja i commit są zapisywane
w obrazie podczas budowania i wyświetlane w stopce.

Tag wydania tworzy się poleceniem `make release`, które samo wylicza kolejny
numer na podstawie najwyższego opublikowanego tagu:

```bash
make release BUMP=patch      # v1.2.0 -> v1.2.1 (lub minor / major)
make release VERSION=2.0.0   # jawny numer, musi być wyższy od ostatniego
git push origin v1.2.1
```

Polecenie pobiera aktualne tagi z `origin` i odmawia utworzenia tagu, jeżeli:
numer nie jest wyższy od najwyższego istniejącego wydania, katalog roboczy
zawiera niezatwierdzone zmiany, bieżąca gałąź to nie `main`, lokalny `main`
różni się od `origin/main` albo bieżący commit ma już tag wydania.

Po wypchnięciu tagu workflow `.github/workflows/release-tag.yaml` sprawdza
ponownie, że tag ma poprawny format, jest wyższy od poprzednich wydań i wskazuje
commit z gałęzi `main`. GitHub nie blokuje samego wypchnięcia tagu, więc
czerwony wynik tego workflow oznacza tag do usunięcia i wydanie do powtórzenia.

Aby tagi wydań były niezmienne (bez możliwości przesunięcia lub usunięcia
istniejącej wersji), administrator repozytorium powinien dodać w GitHub
**Settings → Rules → Rulesets** regułę dla tagów `v*` z włączonymi opcjami
*Restrict updates* i *Restrict deletions* oraz ograniczeniem tworzenia tagów
(*Restrict creations*) do osób odpowiedzialnych za wydania.

Pomiędzy wydaniami `git describe` daje wersję w postaci
`v1.2.0-3-gabc1234` (3 commity po tagu), a dla niezatwierdzonych zmian dodaje
`-dirty`. Bez przekazania argumentów obraz ma wersję `dev`.

## Obrazy z GitHub Container Registry

Opublikowanie wydania (GitHub **Releases → Draft a new release** dla
istniejącego tagu `vX.Y.Z`) uruchamia workflow
`.github/workflows/image-build-and-push.yaml`. Workflow buduje obraz
produkcyjny z wersją i commitem tagu i wypycha go do
`ghcr.io/watchdogpolska/ai-registry-pl`:

| Wydanie | Tagi obrazu |
| --- | --- |
| pełne wydanie `v1.2.0` | `1.2.0-prod`, `latest-prod` |
| pre-release `v1.3.0` | `1.3.0-staging`, `latest-staging` |

Dotyczy to także wydań publikowanych z wersji roboczej (draft). Zmiana
pre-release na pełne wydanie buduje obraz `-prod` dla tego samego tagu.
Publikacja pełnego wydania wysyła dwa zdarzenia (`published` i `released`);
zduplikowany przebieg jest anulowany, więc jeden przebieg ze statusem
„cancelled” jest w tym przypadku normalny.

Przed zbudowaniem obrazu `-prod` workflow ponownie wykonuje
`scripts/release.sh check`, więc `latest-prod` nie może wskazać wersji niższej
od już wydanej. Z tego powodu nie da się przebudować obrazu `-prod` dla
starszego wydania. Obrazy `-staging` nie są tak sprawdzane.

Obraz dla istniejącego tagu można też zbudować ręcznie: **Actions → Docker
Build and Push → Run workflow**, podając tag (`vX.Y.Z`) i wariant (`staging`
lub `prod`), albo poleceniem:

```bash
gh workflow run image-build-and-push.yaml -f tag=v1.2.0 -f deployment=staging
```

Workflow loguje się do rejestru wbudowanym `GITHUB_TOKEN` i nie wymaga
dodatkowych sekretów. Nowy pakiet w GHCR jest domyślnie prywatny; jego
widoczność ustawia się w ustawieniach pakietu w organizacji.

## Budowanie obrazu aplikacji

Lokalnie, z katalogu głównego repozytorium (z checkoutu git, aby ustalić wersję):

```bash
docker build --target production \
  --build-arg APP_VERSION="$(git describe --tags --always --dirty)" \
  --build-arg APP_COMMIT="$(git rev-parse HEAD)" \
  -t ai-registry .
```

Budowanie obrazu automatycznie:

1. instaluje zależności frontendowe,
2. kompiluje SCSS i generuje `bundle.css`,
3. instaluje produkcyjne zależności Pythona,
4. kopiuje aplikację Django razem ze startowym snapshotem danych,
5. wykonuje `collectstatic`,
6. tworzy końcowy obraz uruchamiany przez Gunicorn.

Nie trzeba osobno kopiować na serwer plików CSS.

## Baza danych

Są dwa różne scenariusze pierwszego wdrożenia. Należy wybrać jeden z nich.

### Nowa baza — inicjalizacja ze snapshotu z repozytorium

Utwórz pustą bazę i użytkownika MySQL 8 oraz skieruj `DATABASE_URL` do tej
bazy. Następnie uruchom migracje:

```bash
docker run --rm --env-file .env ai-registry \
  python manage.py migrate --noinput
```

Załaduj startowy snapshot danych rejestru:

```bash
docker run --rm --env-file .env ai-registry \
  python manage.py loaddata data/registry.json
```

Utwórz pierwsze konto administratora:

```bash
docker run --rm -it --env-file .env ai-registry \
  python manage.py createsuperuser
```

Snapshot zawiera dane rejestru, ale nie zawiera użytkowników Django, haseł,
sesji ani logów panelu administracyjnego.

Panel administracyjny Django jest dostępny pod ścieżką `/admin/` w domenie
aplikacji; dostęp wymaga konta z odpowiednimi uprawnieniami.

Jeżeli celem jest uruchomienie celowo pustego rejestru, krok `loaddata` można
pominąć.

### Istniejąca baza rejestru

Jeżeli wdrożenie ma kontynuować istniejącą instancję, należy odtworzyć jej bazę
MySQL zwykłą procedurą backup/restore stosowaną w organizacji. Po odtworzeniu
bazy uruchom migracje przy użyciu nowego obrazu aplikacji:

```bash
docker run --rm --env-file .env ai-registry \
  python manage.py migrate --noinput
```

**Nie uruchamiaj `loaddata data/registry.json` na istniejącej bazie rejestru.**
Snapshot jest przeznaczony do inicjalizacji nowej instalacji, a nie do
aktualizowania lub nadpisywania produkcji.

Po wdrożeniu bieżącym stanem aplikacji zarządza baza MySQL i panel
administracyjny Django.

Historyczny importer PoC CSV celowo nie jest częścią ścieżki wdrożeniowej.

## Charakter snapshotu danych

`ai_registry/data/registry.json` jest snapshotem startowym dołączonym do
repozytorium. Nie należy interpretować go jako aktualnego lub wiążącego źródła
stanu publicznego rejestru.

Snapshot:

- ułatwia uruchomienie nowej instancji bez osobnego dumpa bazy,
- może być aktualizowany okazjonalnie,
- nie ma gwarancji synchronizacji z produkcją,
- nie służy do aktualizacji istniejącej bazy.

Aktualne dane publiczne należy pobierać z działającego serwisu za pomocą
eksportu CSV.

### Odświeżanie snapshotu

Z zaufanej bazy zawierającej stan rejestru przeznaczony do opublikowania
uruchom z katalogu głównego repozytorium:

```bash
docker run --rm --env-file .env -v "$PWD/ai_registry/data:/app/data" \
  ai-registry python manage.py export_registry_data
```

Polecenie zapisuje `ai_registry/data/registry.json`. W lokalnym środowisku
Docker odpowiednikiem jest:

```bash
make export
```

Eksport obejmuje modele z aplikacji `home` i ich relacje. Pomija wewnętrzne
pola `comments` w `AISystem`, `Deployment` i `AIUse`. Eksport jest
przerywany, gdy istnieją nieopublikowane rekordy `AIUse`, aby nie trafiły
przypadkowo do snapshotu przeznaczonego do repozytorium.

## Uruchomienie aplikacji

Minimalne uruchomienie kontenera:

```bash
docker run --env-file .env -p 8000:8000 ai-registry
```

W tym wariancie `DATABASE_URL` musi wskazywać bazę osiągalną z sieci
kontenera. Nazwa `mysql` z pliku `.env.example` jest rozpoznawana w sieci
referencyjnego Docker Compose, ale nie automatycznie przy samodzielnym
`docker run`.

Obraz uruchamia Gunicorn i wystawia port 8000. Docelowa infrastruktura może
zmienić polecenie startowe, liczbę workerów, sieć, health checki i limity
zasobów bez modyfikowania kodu aplikacji.

## Referencyjne wdrożenie Docker Compose

`compose.production.yaml` pokazuje aplikację wraz z kontenerem MySQL 8.4.

Dla nowej instalacji można wykonać (zmienne `APP_VERSION` i `APP_COMMIT`
przekazywane są do budowania obrazu, zob. „Wersjonowanie”):

```bash
export APP_VERSION="$(git describe --tags --always --dirty)"
export APP_COMMIT="$(git rev-parse HEAD)"
docker compose -f compose.production.yaml build
docker compose -f compose.production.yaml up -d mysql

docker compose -f compose.production.yaml run --rm django \
  python manage.py migrate --noinput

docker compose -f compose.production.yaml run --rm django \
  python manage.py loaddata data/registry.json

docker compose -f compose.production.yaml run --rm django \
  python manage.py createsuperuser

docker compose -f compose.production.yaml up -d django
```

Jeżeli używana jest istniejąca baza, pomiń `loaddata` i podłącz aplikację do
odtworzonej bazy.

Plik Compose ma charakter referencyjny. W infrastrukturze organizacji MySQL może
być usługą zewnętrzną, a aplikacja może być wdrażana tym samym mechanizmem co
inne serwisy Django.

## Aktualizacja istniejącego wdrożenia

Przy zwykłej aktualizacji aplikacji:

1. wykonaj backup bazy,
2. zbuduj lub pobierz nowy obraz aplikacji,
3. uruchom `python manage.py migrate --noinput` przy użyciu nowego obrazu,
4. zrestartuj lub zastąp kontener aplikacji,
5. sprawdź stronę główną, przykładowy rekord, panel Django i eksport CSV.

**Nie ładuj snapshotu `registry.json` podczas zwykłej aktualizacji.**

Pliki statyczne nie wymagają osobnego kroku wdrożeniowego, ponieważ znajdują się
w obrazie.

## Kontrole przed wdrożeniem

Przed wdrożeniem dana rewizja powinna przejść GitHub Actions. CI sprawdza:

- formatowanie Black i isort,
- migracje na pustej bazie MySQL 8.4,
- Django system checks,
- testy smoke publicznych widoków i eksportu CSV,
- test eksportu i odtworzenia snapshotu rejestru,
- `collectstatic`,
- budowanie produkcyjnego obrazu Docker.

Dodatkowo na serwerze można wykonać:

```bash
docker run --rm --env-file .env ai-registry python manage.py check --deploy
```

Django może zgłosić ostrzeżenia dotyczące ustawień bezpieczeństwa, które w danym
wdrożeniu są celowo obsługiwane przez otaczającą infrastrukturę. Należy je
ocenić w kontekście rzeczywistej konfiguracji reverse proxy i TLS.
