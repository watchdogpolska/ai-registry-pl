# Rejestr wykorzystania AI w polskim sektorze publicznym

Rejestr systemów i zastosowań sztucznej inteligencji w polskim sektorze
publicznym, prowadzony przez
[Sieć Obywatelską Watchdog Polska](https://siecobywatelska.pl/).

Repozytorium zawiera kod aplikacji oraz startowy snapshot publicznych danych
rejestru w pliku `ai_registry/data/registry.json`. Snapshot służy do
zainicjalizowania nowej instalacji. Nie jest gwarantowany jako aktualny względem
działającego serwisu i może być aktualizowany tylko okazjonalnie.

Aktualny publiczny stan rejestru można pobrać z działającej strony za pomocą
funkcji **„Pobierz dane w formacie CSV”**.

## Uruchomienie lokalne

Środowisko deweloperskie korzysta z Docker Compose, Django i MySQL 8.4.

```bash
docker compose up --build
```

Aplikacja jest następnie dostępna pod adresem
<http://localhost:8001/>.

Przy pierwszym uruchomieniu lokalnym baza jest pusta. Aby załadować startowy
snapshot danych dołączony do repozytorium, uruchom w drugim terminalu:

```bash
docker compose exec django python manage.py loaddata data/registry.json
```

Snapshot należy ładować tylko do nowej lub celowo wyczyszczonej bazy.

Przydatne polecenia:

```bash
docker compose run --rm django python manage.py migrate
docker compose run --rm django python manage.py createsuperuser
docker compose run --rm django python manage.py test
```

Watcher SCSS działa jako osobny serwis deweloperski i zapisuje `bundle.css`
w katalogu plików statycznych Django.

## Wdrożenie produkcyjne

Repozytorium zawiera kompletny obraz produkcyjny Docker. Podczas budowania obrazu
kompilowany jest SCSS, wykonywane jest `collectstatic`, a aplikacja jest
uruchamiana przez Gunicorn. Pliki statyczne są serwowane przez WhiteNoise.

Obraz wymaga MySQL 8 oraz konfiguracji produkcyjnej przekazanej przez zmienne
środowiskowe.

Najprostszy wariant uruchomienia z MySQL wykorzystuje referencyjny
Docker Compose. Przykładowa nazwa hosta bazy `mysql` z pliku `.env.example`
odpowiada usłudze zdefiniowanej w `compose.production.yaml`:

```bash
cp .env.example .env
# uzupełnij .env

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

Alternatywnie można uruchomić obraz przez `docker run` z bazą MySQL dostępną
z sieci kontenera; ten wariant opisano w [instrukcji wdrożenia](docs/deployment.md).

Polecenie `loaddata` jest przeznaczone wyłącznie do inicjalizacji **nowej
bazy** danymi startowymi z repozytorium. Jeżeli wdrażana jest istniejąca baza
rejestru, nie należy ładować do niej snapshotu.

Panel administracyjny Django jest dostępny pod ścieżką `/admin/` w domenie
skonfigurowanej dla aplikacji. Logowanie wymaga konta z odpowiednimi uprawnieniami.

Plik `compose.production.yaml` pokazuje referencyjne środowisko produkcyjne
z MySQL 8.4. Nie narzuca ono infrastruktury docelowej: aplikacja może korzystać
z zewnętrznej usługi MySQL, innego orkiestratora i istniejącego reverse proxy.

Pełna instrukcja, w tym konfiguracja HTTPS, inicjalizacja nowej bazy,
przeniesienie istniejącej bazy i aktualizacja wdrożenia, znajduje się w
[docs/deployment.md](docs/deployment.md).

## Dane rejestru i snapshot startowy

Dane działającej instancji są przechowywane w MySQL i edytowane przez panel
administracyjny Django.

Plik `ai_registry/data/registry.json` jest **snapshotem startowym**. Jego
głównym celem jest umożliwienie uruchomienia nowej instancji z przykładowym
stanem publicznego rejestru bez potrzeby przekazywania osobnego dumpa bazy.
Snapshot:

- nie jest źródłem bieżących danych działającego rejestru,
- nie ma gwarancji, że odpowiada aktualnemu stanowi produkcji,
- może być aktualizowany okazjonalnie,
- nie powinien być używany do nadpisywania istniejącej bazy produkcyjnej.

Dla odbiorcy publicznego źródłem aktualnych danych jest eksport CSV generowany
przez działający serwis. Dla administratora wdrożonej instancji wiążącym stanem
aplikacji jest jej bieżąca baza MySQL.

### Odświeżenie snapshotu

Z zaufanej bazy zawierającej stan rejestru przeznaczony do opublikowania można
wygenerować nowy snapshot:

```bash
cd ai_registry
python manage.py export_registry_data
```

W lokalnym środowisku Docker:

```bash
docker compose exec django python manage.py export_registry_data
```

Domyślny wynik to `ai_registry/data/registry.json`. Eksport obejmuje modele
rejestru z aplikacji `home`, w tym źródła, historię statusów, oceny, tagi
i relacje. Pomija pola `comments` oznaczone jako wewnętrzne w modelach
`AISystem`, `Deployment` i `AIUse`. Nie zawiera użytkowników Django,
haseł, sesji ani logów panelu administracyjnego.

Ze względów bezpieczeństwa eksport jest przerywany, jeżeli w danych znajdują się
rekordy `AIUse` z `published=False`.

Historyczny importer CSV używany podczas budowania pierwszej wersji rejestru nie
jest częścią procesu produkcyjnego.

## Projekt źródłowy

Projekt powstał na bazie otwartego
[AI Registry](https://github.com/danesjenovdan/ai-registry), stworzonego
pierwotnie przez [Danes je nov dan](https://danesjenovdan.si/).

Polska wersja została w 2026 roku istotnie zmodyfikowana i rozbudowana przez
[Sieć Obywatelską Watchdog Polska](https://siecobywatelska.pl/), w szczególności
w zakresie modelu danych, struktury rejestru, prezentacji danych i procesu ich
przygotowania.

## Licencje

Kod aplikacji jest udostępniany na licencji GNU Affero General Public License
v3.0 only (`AGPL-3.0-only`). Pełny tekst znajduje się w
[LICENSE.txt](LICENSE.txt).

Publiczne dane rejestru są udostępniane na licencji Creative Commons Attribution
4.0 International (CC BY 4.0), zgodnie z zasadami opisanymi w
[DATA_LICENSE.md](DATA_LICENSE.md).

Pliki i zasoby pochodzące od podmiotów trzecich mogą podlegać własnym licencjom. Informacje o dołączonych zasobach zewnętrznych znajdują się w [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
