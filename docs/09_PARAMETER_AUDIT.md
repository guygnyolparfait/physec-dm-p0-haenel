# 09 – Audit des paramètres scientifiques

## 1. But de cette étape

Cette étape vérifie la cohérence entre :

1. le dernier modèle scientifique de référence ;
2. `physec_dm/parameters.py` ;
3. les valeurs provisoires utilisées dans `main.py` pour la campagne courte ;
4. les paramètres nécessaires à une campagne scientifique finale.

Aucune valeur provisoire ne doit être transformée silencieusement en valeur scientifique.

La source de référence prioritaire est le dernier document intitulé
`modelisation parametre modifié.pdf`.

---

## 2. Conclusion générale

La structure du code est cohérente avec le dernier modèle.

Les paramètres matériels, LoRa, canal, RFF, batterie et plusieurs paramètres de politique
sont déjà alignés avec le document de référence.

La campagne courte a toutefois utilisé des valeurs de développement pour permettre
l'exécution complète du programme. Ces valeurs ont validé le fonctionnement informatique,
mais elles ne peuvent pas encore servir à produire les résultats scientifiques finaux.

La campagne finale ne doit donc pas être lancée avant de résoudre les paramètres bloquants
décrits dans la section 5.

---

## 3. Paramètres déjà alignés avec le dernier modèle

| Paramètre Python | Valeur du code | Statut scientifique | Décision |
|---|---:|---|---|
| `supply_voltage_v` | 3,3 V | datasheet | conserver |
| `tx_current_a` | 29 mA | datasheet SX1276, point RFO proche de 14 dBm | conserver avec précision du point de fonctionnement |
| `rx_current_a` | 10,8 mA | datasheet SX1276 | conserver |
| `radio_sleep_current_a` | 0,2 µA | datasheet SX1276 | conserver |
| `cpu_current_a` | 5,92 mA | datasheet/dérivé STM32L151xC-A | conserver |
| `cpu_frequency_hz` | 32 MHz | datasheet | conserver |
| `mcu_sleep_current_a` | 1,4 µA | datasheet STM32L151xC | conserver |
| `battery_leak_current_a` | 2,7 µA | dérivé | conserver comme hypothèse explicite |
| `carrier_frequency_hz` | 868 MHz | littérature/scénario | conserver |
| `bandwidth_hz` | 125 kHz | littérature | conserver |
| `spreading_factor` | 12 | littérature/scénario | conserver pour le cas de référence |
| `coding_rate_index` | 1, soit 4/5 | scénario | conserver |
| `preamble_symbols` | 8 | datasheet/scénario | conserver |
| `duty_cycle_fraction` | 1 % | littérature/scénario | conserver en précisant la sous-bande EU868 |
| `noise_figure_db` | 6 dB | littérature/datasheet | conserver |
| `data_payload_bytes` | 32 octets | littérature | conserver |
| `mac_tag_bytes` | 8 octets | politique | conserver |
| `probe_payload_bytes` | 32 octets | littérature/scénario | conserver |
| `challenge_bytes` | 8 octets | politique | conserver |
| `response_bytes` | 8 octets | politique | conserver |
| `probe_delay_s` | 1 s | littérature/scénario | conserver |
| `hardware_reciprocity` | 0,9582 | calibré | conserver et soumettre à sensibilité |
| `maximum_kdr` | 0,30 | politique | conserver |
| `minimum_correlation` | cos(0,30π) ≈ 0,588 | dérivé | conserver |
| `key_length_bits` | 128 bits | littérature/politique | conserver |
| `guard_band_factor` | 1,00 | dérivé neutre | conserver ; ne pas prétendre qu'il vient directement de la littérature |
| `kept_measurement_ratio` | 0,70 | littérature/scénario | conserver comme surrogate explicite |
| `dedicated_probe_interval_s` | 181,0432 s | dérivé du ToA et du duty-cycle | conserver |
| `rff_feature_count` | 3 | littérature | conserver |
| `mallory_separation` | 2,0 | scénario | conserver comme valeur centrale et balayer |
| `target_frr` | 5 % | politique | conserver |
| `rff_threshold` | 7,8147 | dérivé | conserver |
| `rff_processing_time_bob_s` | 1,84 ms | littérature/scénario | conserver avec réserve de transférabilité |
| `ecc_signature_energy_j` | 0,019 J | littérature | conserver comme ancrage, pas comme coût complet de K2 |
| `ecc_signature_time_s` | 0,218 s | littérature | conserver comme ancrage, pas comme protocole complet |
| `maximum_key_age_s` | 86 400 s | politique | conserver |
| `maximum_messages_per_key` | 1000 | politique | conserver |
| `renewal_trigger` | 0,60 | politique | conserver et tester en sensibilité |
| `initial_battery_energy_j` | 28 512 J | dérivé | conserver |
| `battery_reserve_fraction` | 5 % | politique | conserver |
| `critical_latency_budget_s` | 5 s | politique | conserver et tester |
| `normal_latency_budget_s` | 600 s | politique | conserver et tester |
| `critical_far_limit` | 1 % | politique | conserver avec analyse de sensibilité |
| `normal_far_limit` | 5 % | littérature/politique | conserver |
| `message_period_s` | 60 s | scénario | conserver |

---

## 4. Valeurs de `main.py` qui étaient seulement provisoires

Les valeurs suivantes ont permis de réussir la campagne courte, mais elles ne sont pas encore
des valeurs scientifiques finales.

| Paramètre | Valeur de la campagne courte | Problème |
|---|---:|---|
| `challenge_response_latency_s` | 4 s | latence complète du protocole non sourcée |
| `mac_cycles` | 32 000 cycles | le dernier modèle exige un profilage compatible STM32L1 |
| `variation_feasible` | `True` | une condition booléenne a été imposée sans métrique de variabilité |
| `minimum_deadline_s` | 1 s | politique provisoire non justifiée |
| `raw_bit_count` | 128 bits | valeur fixée alors qu'elle doit dépendre du protocole et des mesures |
| `reconciliation_cycles_per_bit` | 100 cycles/bit | valeur provisoire non sourcée |
| `privacy_amplification_cycles` | 6 400 cycles | valeur provisoire non sourcée |
| `reconciliation_message_energy_j` | 0,005 J | valeur provisoire non sourcée |
| `reconciliation_message_latency_s` | 0,5 s | valeur provisoire non sourcée |
| `security_strength_bits` | 128 bits | acceptable comme politique, mais K2 reste incomplet |
| `k2_protocol_id` | `DEVELOPMENT_ONLY` | confirme que K2 n'est pas finalisé |
| `sensing_energy_j` | 0,001 J | valeur de développement |
| `application_energy_j` | 0,002 J | valeur de développement |
| `receive_windows_energy_j` | 0,003 J | valeur de développement |
| `sleep_energy_j` | 0,004 J | valeur de développement |
| `critical_message_probability` | 0,20 | différent du scénario de départ du modèle : 0,10 |
| `mallory_attempt_probability` | 0,10 | différent du scénario de départ du modèle : 0,15 |
| `contextual_weights` | [0,25; 0,25; 0,25; 0,25] | une seule politique équilibrée, insuffisante pour l'étude |
| budget duty-cycle smoke | 10 s | volontairement large et non représentatif |
| `max_steps` | 5 | uniquement un test informatique |

---

## 5. Paramètres bloquants avant les résultats finaux

### 5.1 Coûts de calcul

Les paramètres suivants doivent être mesurés, sourcés sur une plateforme compatible,
ou traités par une analyse de sensibilité clairement déclarée :

- `mac_cycles` ;
- `reconciliation_cycles_per_bit` ;
- `privacy_amplification_cycles`.

Le dernier modèle précise qu'aucune valeur universelle compatible avec le STM32L1
et les implémentations retenues n'est disponible.

### 5.2 Protocole complet K2

Les valeurs de signature ECC ne représentent pas un renouvellement complet.

Il faut définir explicitement :

- le nombre de signatures ;
- le nombre de vérifications ;
- les tailles des messages ;
- le nombre de transmissions ;
- le nombre de réceptions ;
- le délai total ;
- l'identifiant du protocole.

Tant que cette description n'existe pas, `K2` doit rester un scénario expérimental
ou être exclu des conclusions énergétiques définitives.

### 5.3 Énergie de base

Les quatre valeurs suivantes ne doivent pas rester arbitraires :

- `sensing_energy_j` ;
- `application_energy_j` ;
- `receive_windows_energy_j` ;
- `sleep_energy_j`.

Une partie peut être dérivée des courants, de la tension et des durées.
Les coûts propres au capteur et au traitement applicatif doivent être sourcés
ou balayés comme paramètres de scénario.

### 5.4 Variabilité du canal

`variation_feasible=True` n'est pas suffisant scientifiquement.

Il faut ajouter une condition explicite qui vérifie que le canal contient
assez de variabilité pour produire de l'entropie, indépendamment de la seule corrélation.

### 5.5 Latence du défi-réponse

`challenge_response_latency_s=4.0` doit être remplacé par une décomposition :

- réception du défi ;
- délai RX/TX ;
- calcul du MAC ;
- transmission de la réponse ;
- délais protocolaires.

### 5.6 Échéance de renouvellement

`minimum_deadline_s=1.0` ne peut pas être utilisé comme valeur finale sans justification.
L'échéance doit être reliée à l'âge restant de la clé et au seuil anticipé.

### 5.7 Poids du Decision Maker

Une seule politique équilibrée ne suffit pas.

La campagne finale doit au minimum comparer :

- une politique équilibrée ;
- une politique orientée énergie ;
- une politique orientée latence ;
- une politique orientée sécurité ;
- éventuellement une politique contextuelle dépendant de la criticité et de la batterie.

Tous les vecteurs doivent comporter quatre poids positifs ou nuls dont la somme vaut 1.

---

## 6. Paramètre du modèle absent du code actuel

Le dernier modèle prévoit une quantification du SNR :

- `snr_quantization_step_db = 0.25 dB`.

Ce paramètre n'est pas encore présent dans `Parameters`.

Il doit être ajouté avant l'étude de robustesse à l'erreur d'estimation,
mais il ne bloque pas une première campagne nominale sans quantification.

---

## 7. Scénario nominal du modèle à utiliser comme point de départ

Le scénario nominal de départ est :

```text
SNR moyen                     : à balayer
Shadowing                     : 3 dB
Messages critiques            : 0,10
Tentatives de Mallory         : 0,15 par période
Période des messages          : 60 s
Séparation Mallory            : 2,0
Vitesse nominale              : 0 m/s
Profil RFF                    : disponible
Variabilité PHY               : doit être validée
Duty-cycle                    : 1 %
```

La campagne finale ne doit pas reposer sur un seul SNR.
Elle doit balayer plusieurs niveaux radio.

---

## 8. Décision prise après l'audit

### Ce qui ne change pas

Les modules scientifiques déjà validés ne sont pas modifiés à cette étape :

```text
models.py
channel.py
authentication.py
key_generation.py
energy_latency.py
decision_maker.py
mission.py
campaign.py
```

### Ce qui doit être créé ensuite

La prochaine étape est de créer une configuration scientifique séparée de la campagne smoke :

```text
physec_dm/scientific_config.py
tests/test_scientific_config.py
```

Cette configuration devra :

1. reprendre uniquement les valeurs déjà justifiées ;
2. conserver un statut explicite pour les valeurs de scénario ;
3. refuser les paramètres bloquants non résolus ;
4. définir les scénarios de balayage ;
5. définir les politiques comparées ;
6. définir les graines Monte Carlo ;
7. empêcher toute confusion avec `build_smoke_parameters()`.

---

## 9. Verdict

La chaîne informatique est validée.

La campagne scientifique finale n'est pas encore autorisée, car les coûts CPU,
le protocole K2, l'énergie de base, la variabilité du canal et la latence complète
du défi-réponse restent à résoudre ou à traiter explicitement par sensibilité.

La prochaine action correcte est donc :

```text
audit terminé
→ résolution documentée des paramètres bloquants
→ scientific_config.py
→ campagne pilote scientifique
→ campagne complète
→ courbes et compte rendu
```
