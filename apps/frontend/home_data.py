"""
Statički sadržaj početne stranice — srpski (latinica).
"""

from apps.frontend.static_media_data import WORK_CAROUSEL_SLIDES

HOME_SEO_TITLE = "Cementne košuljice — mašinska izrada širom Srbije"
HOME_SEO_DESCRIPTION = (
    "Cementne košuljice (estrih) mašinskim putem za stambene, poslovne i "
    "industrijske objekte širom Srbije. Vrste, proces rada i ponuda prema "
    "uslovima na terenu — pozovite za procenu."
)
HOME_OG_IMAGE_STATIC = "img/cementne-kosuljice6.webp"

ABOUT_SCREED = {
    "eyebrow": "Osnove",
    "title": "Šta su cementne košuljice?",
    "subtitle": (
        "Estrih — ravnajući sloj koji čini stabilnu podlogu pre završnih "
        "podnih obloga."
    ),
    "paragraphs": [
        (
            "Cementne košuljice (estrih, ravnajući sloj) predstavljaju nosivi "
            "sloj cementnog maltera koji se ugrađuje pre keramike, laminata, "
            "parketa ili drugih završnih podova. Njihov zadatak je da obezbede "
            "ravnu, čvrstu i dugotrajnu podlogu u skladu sa projektom."
        ),
        (
            "Mašinskom izradom postiže se ujednačena debljina i kontrolisana "
            "nivelacija na celoj površini — od stanova i kuća do poslovnih "
            "prostora i industrijskih objekata. U sklopu radova često idu i "
            "priprema podloge, laserska nivelacija i izolacioni slojevi."
        ),
    ],
}

SCREED_TYPES = [
    {
        "title": "Klasična cementna košuljica",
        "text": (
            "Standardni ravnajući sloj od cementa, peska i vode — pouzdana "
            "podloga za većinu stambenih i poslovnih objekata."
        ),
    },
    {
        "title": "Plivajuća košuljica",
        "text": (
            "Ugrađuje se preko termo ili zvučne izolacije. Pogodna kada je "
            "potrebna bolja izolacija među etažama ili prema tlu."
        ),
    },
    {
        "title": "Košuljica za podno grejanje",
        "text": (
            "Ravna podloga oko sistema grejanja, sa debljinom i izvedbom "
            "usklađenom sa zahtevima projekta i tipom instalacije."
        ),
    },
    {
        "title": "Industrijska cementna košuljica",
        "text": (
            "Namenjena objektima sa većim opterećenjem — hale, garaže i "
            "proizvodni prostori, uz prilagođenu debljinu i čvrstoću sloja."
        ),
    },
]

PRICE_SECTION = {
    "eyebrow": "Ponuda",
    "title": "Cena cementnih košuljica",
    "subtitle": (
        "Cena se utvrđuje prema uslovima na terenu — bez univerzalne cene "
        "po kvadratu."
    ),
    "intro": (
        "Svaki objekat ima drugačije uslove: pristup gradilištu, spratnost, "
        "stanje podloge, potrebnu debljinu i obim pripremnih radova. Zato "
        "ponudu za cementne košuljice dajemo nakon osnovnih informacija o "
        "projektu ili nakon pregleda lokacije."
    ),
    "factors_title": "Šta utiče na cenu?",
    "factors": [
        "Kvadratura i debljina košuljice",
        "Stanje i priprema postojeće podloge",
        "Potreba za termo ili zvučnom izolacijom",
        "Laserska nivelacija i zahtevi projekta",
        "Pristup objektu, spratnost i logistika na terenu",
        "Rokovi i dinamika izvođenja radova",
    ],
    "closing": (
        "Javite nam lokaciju, okvirnu kvadraturu i tip objekta — pripremamo "
        "procenu i ponudu u najkraćem roku."
    ),
}

MACHINE_SCREED_ADVANTAGES = [
    {
        "title": "Ravna i precizno nivelisana podloga",
        "text": (
            "Laserska nivelacija obezbeđuje tačne visine i padove pre ugradnje "
            "košuljice."
        ),
    },
    {
        "title": "Brže izvođenje radova",
        "text": (
            "Mašinska ugradnja skraćuje rokove u odnosu na ručnu izradu "
            "na većim površinama."
        ),
    },
    {
        "title": "Ujednačen kvalitet na celoj površini",
        "text": (
            "Kontrolisana debljina i homogena struktura sloja na celoj "
            "površini objekta."
        ),
    },
    {
        "title": "Pogodno za velike i male objekte",
        "text": (
            "Od stanova i kuća do poslovnih prostora i industrijskih hala."
        ),
    },
    {
        "title": "Mogućnost izvođenja na višim spratovima",
        "text": (
            "Oprema i logistika prilagođeni radu u zgradama sa više etaža."
        ),
    },
    {
        "title": "Idealna priprema za podno grejanje",
        "text": (
            "Ravna podloga spremna za sisteme podnog grejanja i završne "
            "obloge."
        ),
    },
    {
        "title": "Dugotrajnost i otpornost podloge",
        "text": (
            "Čvrsta osnova za keramiku, laminat, parket i druge završne "
            "podove."
        ),
    },
]

PROCESS_STEPS = [
    {
        "title": "Pregled objekta i dogovor",
        "text": (
            "Obilazak lokacije, utvrđivanje obima radova, debljine košuljice "
            "i uslova na gradilištu — dogovor oko rokova i narednih faza."
        ),
    },
    {
        "title": "Priprema podloge",
        "text": (
            "Provera nosivosti, vlage i čistoće podloge; postavljanje izolacije "
            "ili pripremnih slojeva prema projektu."
        ),
    },
    {
        "title": "Nivelacija",
        "text": (
            "Lasersko određivanje visina i padova kako bi ugradnja košuljice "
            "bila u skladu sa projektom."
        ),
    },
    {
        "title": "Mašinska ugradnja",
        "text": (
            "Ugradnja cementne košuljice mašinskim putem — ujednačena debljina "
            "na celoj površini."
        ),
    },
    {
        "title": "Završna obrada",
        "text": (
            "Perdašenje i zaštita površine po potrebi; podloga spremna za "
            "postavljanje završnih podnih obloga."
        ),
    },
]

HOME_PROJECT_HIGHLIGHTS = [
    {
        "title": "Stambeni objekti",
        "caption": WORK_CAROUSEL_SLIDES[0].caption,
        "image": WORK_CAROUSEL_SLIDES[0],
    },
    {
        "title": "Poslovni prostori",
        "caption": WORK_CAROUSEL_SLIDES[2].caption,
        "image": WORK_CAROUSEL_SLIDES[2],
    },
    {
        "title": "Investitorski projekti",
        "caption": WORK_CAROUSEL_SLIDES[4].caption,
        "image": WORK_CAROUSEL_SLIDES[4],
    },
]

HOME_FAQ_ITEMS = [
    {
        "question": "Šta je cementna košuljica?",
        "answer": (
            "Cementna košuljica (estrih, ravnajući sloj) je ravna nosiva "
            "podloga od cementnog maltera koja se ugrađuje pre postavljanja "
            "završnih podnih obloga, poput keramike, laminata ili parketa."
        ),
    },
    {
        "question": "Da li su estrih i cementna košuljica ista stvar?",
        "answer": (
            "U praksi se termini često koriste kao sinonimi. Estrih i "
            "ravnajući sloj označavaju istu funkciju — ravnu nosivu podlogu "
            "pre završnog poda. Kod nas govorimo o mašinskoj izradi "
            "cementnih košuljica. Više o terminu estrih možete pročitati "
            "na posebnoj stranici posvećenoj estrihu."
        ),
    },
    {
        "question": "Zašto birati mašinsku izradu košuljice?",
        "answer": (
            "Mašinska ugradnja obezbeđuje ujednačenu debljinu, bržu izvedbu "
            "i preciznu nivelaciju, posebno na većim površinama i višespratnim "
            "objektima."
        ),
    },
    {
        "question": "Kolika je uobičajena debljina cementne košuljice?",
        "answer": (
            "Debljina zavisi od projekta, opterećenja i toga da li ide "
            "izolacija ili podno grejanje. Tačnu debljinu utvrđujemo pri "
            "pregledu objekta i dogovoru o obimu radova."
        ),
    },
    {
        "question": "Koliko traje sušenje pre postavljanja podova?",
        "answer": (
            "Vreme sušenja zavisi od debljine sloja, vrste košuljice, "
            "temperature i vlage na objektu. Deblji sloj i vlažniji uslovi "
            "produžavaju rok. Pre ugradnje završnih obloga obavezno se "
            "proverava vlaga podloge."
        ),
    },
    {
        "question": "Koliko koštaju cementne košuljice?",
        "answer": (
            "Cena zavisi od uslova na terenu: kvadrature, debljine, pripreme "
            "podloge, izolacije, spratnosti i pristupa objektu. Zato ne "
            "navodimo fiksnu cenu po m² — ponudu dajemo nakon osnovnih "
            "informacija o projektu ili pregleda lokacije. Detaljnije o "
            "faktorima cene pišemo na stranici o ceni cementnih košuljica."
        ),
    },
    {
        "question": "Na kojoj teritoriji pružate usluge?",
        "answer": (
            "Realizujemo cementne košuljice mašinskim putem na teritoriji "
            "cele Srbije, za stambene, poslovne i industrijske objekte."
        ),
    },
    {
        "question": "Kako mogu dobiti ponudu?",
        "answer": (
            "Pozovite nas telefonom ili pošaljite upit putem kontakt stranice. "
            "Potrebne su osnovne informacije o objektu, kvadraturi i lokaciji "
            "radi procene i dogovora oko rokova."
        ),
    },
    {
        "question": "Da li radite pripremu podloge i nivelaciju?",
        "answer": (
            "Da. U sklopu usluge obuhvatamo pregled objekta, pripremu podloge, "
            "lasersku nivelaciju i mašinsku ugradnju cementne košuljice prema "
            "projektu."
        ),
    },
]
