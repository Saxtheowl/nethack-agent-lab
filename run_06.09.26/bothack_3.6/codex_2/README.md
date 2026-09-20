# Ultimate BotHack 3.6.7 — dossier de refonte

La [méga documentation](docs/ULTIMATE_BOTHACK_3.6_ARCHITECTURE.md) contient l'audit du projet voisin `claude`, les recherches techniques, l'architecture cible, les contrats d'actions, la stratégie de progression, les tests et le backlog de migration.

Le [relevé d'audit](evidence/audit-local-2026-09-17.json) conserve les empreintes des fichiers principaux et les résultats recalculés des campagnes locales.

Recommandation : conserver le moteur C et le window port existants, migrer progressivement vers un bot Python à observations et compétences typées, comparer NLE sur un périmètre borné, puis décider des optimisations à partir de mesures.

Ce dossier ne modifie pas le bot actif et ne constitue pas encore une nouvelle implémentation.

Le [guide pour expliquer l’application actuelle, du débutant à l’expert](docs/COMPRENDRE_BOTHACK_3.6_DEBUTANT_CONFIRME_EXPERT.md) décrit le jeu, le joueur automatique, les composants techniques, l’exploitation et les résultats, avec des présentations prêtes à reprendre. Il inclut une vérification datée du worker actif le 18 septembre 2026.

L'[évaluation des ressources et des runs multi-hôtes](docs/ESTIMATION_RESSOURCES_RUNS_MULTI_HOSTS.md) estime le gain du parallélisme, compare le miniforum à la machine locale et décrit les conditions nécessaires pour conserver des campagnes comparables entre plusieurs machines.
