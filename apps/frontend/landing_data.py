"""
SEO landing stranice — statički sadržaj (srpski, latinica).
Svaka stranica ima jasan ugao: stub, cena, sinonim (estrih).
"""

from apps.frontend.home_data import PRICE_SECTION, SCREED_TYPES

LANDING_CEMENTNE_KOSULJICE = {
    "slug": "cementne-kosuljice",
    "url_name": "frontend:cementne_kosuljice",
    "breadcrumb_title": "Cementne košuljice",
    "seo_title": "Cementne košuljice — vodič i mašinska izrada",
    "seo_description": (
        "Šta su cementne košuljice, koje vrste postoje i kako izgleda "
        "mašinska ugradnja estriha. Profesionalna izrada širom Srbije — "
        "pozovite za ponudu."
    ),
    "h1": "Cementne košuljice",
    "lead": (
        "Ravna, čvrsta podloga pre keramike, laminata ili parketa — "
        "mašinska izrada cementnih košuljica za stambene, poslovne i "
        "industrijske objekte širom Srbije."
    ),
    "sections": [
        {
            "title": "Šta su cementne košuljice i čemu služe?",
            "paragraphs": [
                (
                    "Cementne košuljice su ravnajući sloj cementnog maltera "
                    "koji se ugrađuje pre završnih podnih obloga. U struci se "
                    "često nazivaju i estrih. Bez kvalitetne košuljice teško "
                    "je postići ravnost, stabilnost i dugotrajnost poda."
                ),
                (
                    "Koriste se u novogradnji i renovaciji: u stanovima, "
                    "kućama, poslovnim prostorima, garažama i halama. "
                    "Debljina i tip izvedbe zavise od projekta, opterećenja "
                    "i toga da li ide izolacija ili podno grejanje."
                ),
            ],
        },
        {
            "title": "Zašto mašinska izrada?",
            "paragraphs": [
                (
                    "Mašinska ugradnja cementnih košuljica omogućava "
                    "ujednačenu debljinu, brži rad na većim površinama i "
                    "precizniju nivelaciju u odnosu na ručno izvođenje. "
                    "To je posebno važno na višespratnim objektima i "
                    "investitorskim projektima."
                ),
                (
                    "U sklopu usluge obično idu pregled objekta, priprema "
                    "podloge, laserska nivelacija i završna obrada površine "
                    "prema dogovoru — kako bi podloga bila spremna za "
                    "narednu fazu gradnje."
                ),
            ],
        },
        {
            "title": "Kada su cementne košuljice pravi izbor?",
            "paragraphs": [
                (
                    "Kada vam treba nosiva, ravna podloga pre završnog poda; "
                    "kada projekat predviđa određenu debljinu ili padove; "
                    "kada se ugrađuje termo ili zvučna izolacija; i kada "
                    "planirate sistem podnog grejanja."
                ),
                (
                    "Ako niste sigurni koja izvedba odgovara vašem objektu, "
                    "javite nam osnovne podatke o lokaciji i kvadraturi — "
                    "predložićemo pristup u skladu sa uslovima na terenu."
                ),
            ],
        },
    ],
    "cards_title": "Vrste cementnih košuljica",
    "cards_subtitle": (
        "Biramo izvedbu prema objektu, opterećenju i zahtevima projekta."
    ),
    "cards": SCREED_TYPES,
    "related": [
        {
            "title": "Cena cementnih košuljica",
            "url_name": "frontend:cena_cementne_kosuljice",
            "text": "Šta utiče na cenu i kako dobiti ponudu prema terenu.",
        },
        {
            "title": "Estrih",
            "url_name": "frontend:estrih",
            "text": "Šta znači estrih i kako se odnosi na cementnu košuljicu.",
        },
        {
            "title": "Naše usluge",
            "url_name": "frontend:usluge",
            "text": "Mašinska izrada, laserska nivelacija i izolacija.",
        },
    ],
}

LANDING_CENA = {
    "slug": "cena-cementne-kosuljice",
    "url_name": "frontend:cena_cementne_kosuljice",
    "breadcrumb_title": "Cena",
    "seo_title": "Cena cementnih košuljica — ponuda prema terenu",
    "seo_description": (
        "Koliko koštaju cementne košuljice? Cena zavisi od kvadrature, "
        "debljine, pripreme podloge i uslova na gradilištu. Bez fiksne "
        "cene po m² — zatražite procenu."
    ),
    "h1": "Cena cementnih košuljica",
    "lead": (
        "Ne postoji jedna univerzalna cena po kvadratu. Ponudu za cementne "
        "košuljice dajemo prema uslovima na terenu — nakon osnovnih "
        "informacija o objektu ili pregleda lokacije."
    ),
    "sections": [
        {
            "title": "Zašto nema fiksne cene po m²?",
            "paragraphs": [
                (
                    "Svako gradilište je drugačije: pristup mešalici i "
                    "opremi, spratnost, stanje postojeće podloge, potrebna "
                    "debljina estriha i eventualna izolacija. Zbog toga "
                    "okvirne cene sa interneta često ne odgovaraju realnom "
                    "obimu radova na vašem objektu."
                ),
                (
                    "Ispravniji pristup je da nam kažete lokaciju, okvirnu "
                    "kvadraturu, tip objekta i da li ide podno grejanje ili "
                    "izolacija. Na osnovu toga pripremamo procenu, a po "
                    "potrebi i obilazak radi konačne ponude."
                ),
            ],
        },
        {
            "title": "Kako dobiti tačnu ponudu?",
            "paragraphs": [
                (
                    "Pozovite nas ili pošaljite upit sa osnovnim podacima. "
                    "Što preciznije opišete objekat, brže možemo da "
                    "procenimo obim: debljinu košuljice, pripremu podloge "
                    "i rokove izvođenja."
                ),
                (
                    "Radimo mašinsku izradu cementnih košuljica širom Srbije "
                    "— za privatne investitore, građevinske firme i "
                    "poslovne objekte."
                ),
            ],
        },
    ],
    "factors_title": PRICE_SECTION["factors_title"],
    "factors": PRICE_SECTION["factors"],
    "faq": [
        {
            "question": "Da li možete dati cenu samo po telefonu?",
            "answer": (
                "Možemo dati orijentacionu procenu ako imamo dovoljno "
                "podataka (kvadratura, debljina, sprat, lokacija). "
                "Konačna ponuda često zahteva potvrdu uslova na terenu."
            ),
        },
        {
            "question": "Šta najviše poskupljuje radove?",
            "answer": (
                "Obično veća debljina, loša ili nepripremljena podloga, "
                "dodatna izolacija, otežan pristup i rad na višim etažama. "
                "Zato pregled objekta pomaže da ponuda bude realna."
            ),
        },
        {
            "question": "Da li cena uključuje materijal?",
            "answer": (
                "Obim ponude dogovaramo po projektu — šta ulazi u cenu "
                "(materijal, ugradnja, nivelacija, izolacija) jasno "
                "navodimo pre početka radova."
            ),
        },
    ],
    "related": [
        {
            "title": "Cementne košuljice — vodič",
            "url_name": "frontend:cementne_kosuljice",
            "text": "Šta su košuljice, vrste i kada su pravi izbor.",
        },
        {
            "title": "Estrih",
            "url_name": "frontend:estrih",
            "text": "Objašnjenje termina estrih i ravnajući sloj.",
        },
        {
            "title": "Kontakt",
            "url_name": "frontend:kontakt",
            "text": "Pozovite nas za procenu i ponudu.",
        },
    ],
}

LANDING_ESTRIH = {
    "slug": "estrih",
    "url_name": "frontend:estrih",
    "breadcrumb_title": "Estrih",
    "seo_title": "Estrih — cementna košuljica i ravnajući sloj",
    "seo_description": (
        "Šta je estrih? Estrih je cementna košuljica — ravnajući sloj pre "
        "završnog poda. Mašinska izrada estriha širom Srbije — pozovite "
        "za ponudu."
    ),
    "h1": "Estrih (cementna košuljica)",
    "lead": (
        "Estrih je stručni naziv za ravnajući sloj — u praksi isti posao "
        "kao cementne košuljice. Mašinski ga ugrađujemo kao ravnu, čvrstu "
        "podlogu pre završnih podnih obloga."
    ),
    "sections": [
        {
            "title": "Šta znači estrih?",
            "paragraphs": [
                (
                    "Estrih (engl. screed) označava sloj koji nivelira i "
                    "ojačava podlogu pre postavljanja keramike, laminata, "
                    "parketa ili drugih obloga. U Srbiji se isti sloj "
                    "najčešće zove cementna košuljica ili ravnajući sloj."
                ),
                (
                    "Bez obzira na naziv, cilj je isti: homogena debljina, "
                    "adekvatna čvrstoća i ravnost u toleranciji koju zahteva "
                    "projekat i tip završnog poda."
                ),
            ],
        },
        {
            "title": "Estrih i cementne košuljice — da li je to isto?",
            "paragraphs": [
                (
                    "U svakodnevnoj gradnji termini se koriste kao sinonimi. "
                    "Kada tražite „estrih“, „cementne košuljice“ ili "
                    "„ravnajući sloj“, u suštini tražite istu uslugu: "
                    "izradu i ugradnju nosive podloge pre završnog poda."
                ),
                (
                    "Kod nas se fokusira na mašinsku izradu cementnih "
                    "košuljica, uz lasersku nivelaciju i pripremu podloge "
                    "prema uslovima na objektu."
                ),
            ],
        },
        {
            "title": "Kada vam treba estrih?",
            "paragraphs": [
                (
                    "Kada završavate novi objekat, renovirate postojeći "
                    "prostor, ugrađujete izolaciju ispod poda ili "
                    "pripremate sistem podnog grejanja. Estrih mora biti "
                    "dovoljno suv pre postavljanja završnih obloga — vlaga "
                    "se proverava pre te faze."
                ),
                (
                    "Za orijentacionu procenu cene estriha (cementnih "
                    "košuljica) potrebni su podaci o kvadraturi, debljini "
                    "i lokaciji — jer uslovi na terenu bitno utiču na "
                    "obim radova."
                ),
            ],
        },
    ],
    "cards_title": "Uobičajene izvedbe estriha",
    "cards_subtitle": (
        "Od klasičnog ravnajućeg sloja do podloge za podno grejanje."
    ),
    "cards": SCREED_TYPES,
    "related": [
        {
            "title": "Cementne košuljice",
            "url_name": "frontend:cementne_kosuljice",
            "text": "Kompletan pregled usluge i vrsta košuljica.",
        },
        {
            "title": "Cena cementnih košuljica",
            "url_name": "frontend:cena_cementne_kosuljice",
            "text": "Kako se formira cena prema terenu.",
        },
        {
            "title": "Usluge",
            "url_name": "frontend:usluge",
            "text": "Mašinska izrada, nivelacija i izolacija.",
        },
    ],
}
