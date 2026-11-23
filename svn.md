# Modellen in Subversion

Dit zijn de mappen in `svn.geostandaarden.nl`. Aan iedere map is een team toegekend.

| Folder         | project        | Omschrijving                                                      |
| -------------- | -------------- | ----------------------------------------------------------------- |
| BRO            | BRO            | Basisregistratie Ondergrond                                       |
| CIM-DSO        | TPOD           | Conceptuele informatiemodellen DSO                                |
| Datatypes      | Basisprogramma | Basis datatypes                                                   |
| Geostandaarden | Basisprogramma | Niet echt beheerde bestanden kopie-en van INSPIRE/ISO             |
| IMEV           | IMEV           | Informatiemodel Externe Veiligheid                                |
| IMGeluid       | IMGeluid       | Informatiemodel Geluid                                            |
| IMGeo          | BGT            | Informatiemodel Geografie                                         |
| IMGolf         | NEN3610        | Voorbeeldmodel Informatiemodel Golfbaan                           |
| IMKA           |                | Informatiemodel Klimaatadaptatie Hitte                            |
| IMKL           | IMKL           | Informatiemodel Kabels en Leidingen                               |
| IMKL-MIM       | IMKL           | Informatiemodel Kabels en Leidingen volgens MIM                   |
| IMLE           |                | Informatiemodel en kwaliteitskader agrarische landschapselementen |
| IMMobiliteit   |                | Informatiemodel Mobiliteit                                        |
| IMOW           | DSO            | Informatiemodel Omgevingswet                                      |
| IMROI          |                | Informatiemodel Repressieve Object Informatie                     |
| IMSOR          |                |                                                                   |
| IMWOZ          |                | Informatiemodel Waardering Onroerende Zaken                       |
| INSPIRE        | EU             | INSPIRE Modellen. Deze bevat een kopie van de INSPIRE modellen    |
| MIM            | MIM            | Metamodel Informatie Modelleleren                                 |
| NEN3610        | NEN3610        | NEN 3610                                                          |
| WaU            |                |                                                                   |
| VTH            | VTH            | Vergunning Toezicht Handhaving                                    |


## Acties

| Folder         | Actie                                         |
| -------------- | --------------------------------------------- |
| BRO            | TODO                                          |
| Geostandaarden | Kijken of we die in andere modellen gebruiken |
| IMSOR          | TODO                                          |
| WaU            | TODO                                          |

## In de mappen zitten beheerde UML modellen in bestanden

| Folder       | bestand                                    | type        | MIM | Catologus                                                                                                                     | Status            |
| ------------ | ------------------------------------------ | ----------- | --- | ----------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| CIM-DSO      | dso-cim-am.xml                             | conceptueel | 1.2 | [Conceptueel Informatiemodel Aanvragen en meldingen.](https://geonovum.github.io/dso-cim-am/)                                 | werkversie        |
| CIM-DSO      | dso-cim-bhkv.xml                           | conceptueel | 1.2 | [Conceptueel informatiemodel Bronhouder Koppelvlak](https://geonovum.github.io/dso-cim-bhkv/)                                 | werkversie        |
| CIM-DSO      | dso-cim-hlp.xml                            | conceptueel | 1.2 | [Conceptueel Informatiemodel Help en ondersteuning](https://geonovum.github.io/dso-cim-hlp/)                                  | werkversie        |
| CIM-DSO      | dso-cim-mac.xml                            | conceptueel | 1.2 | [Conceptueel Informatiemodel Machtigen](https://geonovum.github.io/dso-cim-mac/)                                              | werkversie        |
| CIM-DSO      | dso-cim-oi.xml                             | conceptueel | 1.2 | [Conceptueel informatiemodel Omgevingsinformatie](https://geonovum.github.io/dso-cim-oi/)                                     | werkversie        |
| CIM-DSO      | dso-cim-op.xml                             | conceptueel | 1.2 | [Conceptueel informatiemodel Officiële Publicaties](https://docs.geostandaarden.nl/dso/def-im-dso-cim-op-20240123/)           | 1.0  (def)        |
| CIM-DSO      | dso-cim-org.xml                            | conceptueel | 1.2 | [Conceptueel informatiemodel (Overheids-)Organisaties](https://geonovum.github.io/dso-cim-org/)                               | werkversie        |
| CIM-DSO      | dso-cim-ow.xml                             | conceptueel | 1.2 | [Conceptueel informatiemodel Omgevingswet](https://docs.geostandaarden.nl/dso/def-im-dso-cim-ow-20260109/)                    | 3.0 (def)         |
| CIM-DSO      | dso-cim-pdc.xml                            | conceptueel | 1.2 | [Conceptueel informatiemodel Producten- en Dienstencatalogus](https://geonovum.github.io/dso-cim-pdc/)                        | werkversie        |
| CIM-DSO      | dso-cim-swf.xml                            | conceptueel | 1.2 | [Conceptueel informatiemodel Samenwerkfunctionaliteit](https://docs.geostandaarden.nl/dso/dso-cim-swf-20250429/)              | 29 april 2025     |
| CIM-DSO      | dso-cim-tr.xml                             | conceptueel | 1.2 | [Conceptueel informatiemodel Toepasbare regels](https://geonovum.github.io/dso-cim-tr/)                                       | werkversie        |
| Datatypes    | datatypen-ISO19107-2003.xml                | logisch     | 1.2 | [ISO 19107 datatypen](https://geonovum.github.io/iso-19107-datatypen/)                                                        | werkversie        |
| Datatypes    | datatypen-MIM.xml                          | logisch     | 1.2 | [MIM - Datatypen](https://geonovum.github.io/mim-datatypen/)                                                                  | werkversie        |
| Datatypes    | datatypen-overig.xml                       | logisch     | 1.2 | [Geonovum datatypen](https://github.com/Geonovum/geonovum-datatypen/)                                                         | werkversie        |
| IMEV         | IMEV.xml                                   | logisch     |     | [Informatiemodel Externe Veiligheid](https://docs.geostandaarden.nl/imev/vv-im-imev-20261111/)                                | 4.0.0 (vv)        |
| IMGeluid     | IMGeluid Algemeen.xml                      | logisch     | 1.2 | [Informatiemodel Geluid](https://docs.geostandaarden.nl/cvgg/def-im-img-20261015/)                                            | 4.0               |
| IMGeo        | IMGeo2.2-MIM-conceptueel.xml               | conceptueel |     |                                                                                                                               |                   |
| IMGeo        | IMGeo2.2-MIM-logisch.xml                   | logisch     |     |                                                                                                                               |                   |
| IMGeo        | MIM11.XML                                  | logisch     |     |                                                                                                                               |                   |
| IMGolf       | IMGolf.xml                                 | logisch     | 1.2 | [Voorbeeldmodel Informatiemodel Golfbaan](https://geonovum.github.io/imgolf-werkomgeving/)                                    | werkversie        |
| IMKA         | informatiemodel_klimaatadaptatie_hitte.xml | conceptueel |     | -                                                                                                                             |                   |
| IMKL         | IMKL-INSPIRE Consolidated UML Model.xml    | inspire     |     | Bevat KOP van INSPIRE model                                                                                                   |                   |
| IMKL         | IMKL-Inspire.xml                           |             |     |                                                                                                                               |                   |
| IMKL         | IMKL.xml                                   |             |     |                                                                                                                               |                   |
| IMKL-MIM     | IMKL-MIM-new.xml                           | logisch     | 1.2 | -                                                                                                                             |                   |
| IMLE         | IMLE-conceptueel.xml                       | conceptueel | 1.1 | [Informatiemodel en kwaliteitskader agrarische landschapselementen](https://docs.geostandaarden.nl/imle/cv-im-imle-20220531/) | consultatieversie |
| IMMobiliteit | IMMob - conceptueel.xml                    | conceptueel | 1.2 | [Informatiemodel Mobiliteit (IMMOB)](https://geonovum.github.io/IMMOB/)                                                       | werkversie        |
| IMOW         | IMOW-3.0.xml                               | logisch     |     | [Informatiemodel Omgevingswet 3.0]()                                                                                          |                   |
| IMOW         | IMOW-3.1.xml                               | logisch     |     | [Informatiemodel Omgevingswet 3.1]()                                                                                          |                   |
| IMOW         | IMOW-3.2.xml                               | logisch     |     | [Informatiemodel Omgevingswet 3.2]()                                                                                          |                   |
| IMOW         | releases/IMOW-3.0.1.xml                    | logisch     |     | [Release van Informatiemodel Omgevingswet 3.0.1]()                                                                            |                   |
| IMOW         | releases/IMOW-3.1.0.xml                    | logisch     |     | [Release van Informatiemodel Omgevingswet 3.1.0]()                                                                            |                   |
| IMOW         | releases/IMOW-3.1.1.xml                    | logisch     |     | [Release van Informatiemodel Omgevingswet 3.1.1]()                                                                            |                   |
| IMOW         | releases/IMOW-3.1.2.xml                    | logisch     |     | [Release van Informatiemodel Omgevingswet 3.1.2]()                                                                            |                   |
| IMOW         | releases/IMOW-3.2-rc.xml                   | logisch     |     | [Release van Informatiemodel Omgevingswet 3.2-rc]()                                                                           |                   |
| IMROI        | IMROI-conceptueel.xml                      | logisch     | 1.2 | [Repressieve Object Informatie](https://docs.geostandaarden.nl/imroi/cv-im-imroi-20240521/)                                   | consultatieversie |
| INSPIRE      | FoundationSchemas.xml                      | inspire     | -   | -                                                                                                                             |                   |
| INSPIRE      | Generic Conceptual Model.xml               | inspire     | -   | -                                                                                                                             |                   |
| INSPIRE      | Themes.xml                                 | inspire     | -   | -                                                                                                                             |                   |
| MIM          | MIM testmodellen.xml'                      |             |     |                                                                                                                               |                   |
| MIM          | MIM visualisatie metamodel.xml'            |             |     |                                                                                                                               |                   |
| MIM          | MIM-UMLprofiel.xml                         |             |     |                                                                                                                               |                   |
| MIM          | MIM2.0.xml                                 |             |     |                                                                                                                               |                   |
| MIM          | Model.xml                                  |             |     |                                                                                                                               |                   |
| NEN3610      | NEN3610.xml                                | conceptueel | 1.1 | ik denk de NEN 3610 standaard                                                                                                 | nen3610:          |
| VTH          | cim-vth-flo.xml                            | conceptueel | 1.2 | [Conceptueel Informatiemodel Toezicht en Handhaving](https://docs.geostandaarden.nl/vth/def-im-cim-vth-flo-20260724/)         | 1.0.1             |
| VTH          | lith.xml                                   | logisch     | 1.2 | [Logisch Informatiemodel Toezicht en Handhaving](https://geonovum.github.io/vth-lith/)                                        | werkversie        |
