# PharmaGest — gestion de pharmacie (Django)

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (Linux/macOS : source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py charger_demo --mot-de-passe "UnMotDePasseDeTest1!"   # données fictives + 4 comptes de démo
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000/ — l'interface charge Bootstrap 5 et Bootstrap Icons depuis un CDN (Internet requis).

## Comptes de démonstration (créés par `charger_demo --mot-de-passe`)

| Compte | Rôle | Page d'accueil |
|---|---|---|
| `pharmacien` | Pharmacien responsable | Tableau de bord |
| `gestionnaire` | Gestionnaire de stock | Stock et lots |
| `caissier` | Caissier | Caisse |
| `responsable` | Responsable de gestion | Tableau de bord |

Le super-utilisateur voit tout et gère les comptes via `/admin/`. Ne laissez jamais ces comptes de démo en production.

## Règles à retenir

- Une commande d'achat n'augmente **pas** le stock : seule la réception validée le fait, une seule fois.
- Les ventes sortent le lot qui expire en premier (FEFO) ; périmé ou bloqué = jamais vendu.
- Une vente validée n'est jamais supprimée : on la corrige par un **retour** tracé.
- Les paiements mobile money / carte / chèque sont **simulés** dans cette version.

## Tests

```bash
python manage.py test
```

## Configuration

Copiez `.env.example` en `.env`. Avec `DJANGO_DEBUG=False`, définissez aussi `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, lancez `python manage.py collectstatic` et servez le site en HTTPS.

## Sauvegarde

Base SQLite : copier `db.sqlite3` **et** le dossier `media/` (photos). Testez régulièrement la restauration.
