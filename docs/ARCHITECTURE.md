# Architecture proposee pour `agent media`

## Structure

```text
AgentMedia/
├── main.py
├── requirements.txt
├── .env.example
├── data/
│   ├── raw/
│   └── processed/
├── outputs/
├── docs/
│   └── ARCHITECTURE.md
└── src/
    └── agent_media/
        ├── __init__.py
        ├── config.py
        ├── data_loader.py
        ├── calendar_utils.py
        ├── mappings.py
        ├── profile_builder.py
        ├── retrieval.py
        ├── scoring.py
        ├── content_generator.py
        ├── image_generator.py
        ├── export_service.py
        ├── post_store.py
        └── orchestrator.py
```

## Role des dossiers

- `data/raw/`: fichiers sources Excel et CSV.
- `data/processed/`: artefacts prepares, profils, index FAISS, JSON intermediaires.
- `outputs/`: sorties metier, posts, images, exports finaux.
- `src/agent_media/`: logique Python de l'application.
- `docs/`: documentation technique et decisions d'architecture.

## Ce que fait maintenant le pipeline

- charge les fichiers Excel et CSV
- nettoie les donnees et reconstruit les profils produits
- cree le mapping des fetes tunisiennes et des saisons marketing
- score les produits pour la prochaine fete et les saisons actives
- genere des posts Facebook / Instagram
- cree des visuels locaux simples dans `outputs/campaign_images/`
- exporte les artefacts dans `data/processed/` et `outputs/`

## Comment migrer ton ancien script

- `BLOC 1 DATA`: vers `data_loader.py`.
- `classification des fetes`: vers `calendar_utils.py`.
- `generation de posts`: `content_generator.py`.
- `generation d'images`: `image_generator.py`.
- `RAG / FAISS / embeddings`: `retrieval.py`.
- `feedback loop / dataset posts`: vers `post_store.py`.

## Lancement

```bash
python main.py
```

## Fichiers de sortie

- `outputs/pipeline_snapshot.json`: resume du dernier lancement
- `outputs/dataset_posts.json`: posts enregistres
- `outputs/campaign_images/`: visuels generes
- `data/processed/profil_produits_final.csv`: profils produits exportes
- `data/processed/profils_mistral.json`: export JSON des profils
- `data/processed/fetes_mapping.json`: mapping fetes enrichi

## Note importante

Le fichier `social_media_agent_versionfinal_(1).py` est conserve comme source legacy. La bonne pratique maintenant est de migrer la logique par blocs dans `src/agent_media/` au lieu de continuer a modifier ce fichier exporte depuis Colab.
