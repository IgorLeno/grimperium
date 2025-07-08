
# **Esquema do Banco de Dados: thermo\_pm7.csv**

## **1. Introdução**

Este documento define a estrutura de colunas para o arquivo `thermo_pm7.csv`. O esquema espelha o `thermo_cbs.csv` para garantir consistência e facilitar o merge dos dados para o treinamento do modelo Δ-ML.

## **2. Definição das Colunas**

| Nome da Coluna          | Tipo de Dado | Descrição Detalhada                                                                                                                  | Exemplo de Valor                |
| :---------------------- | :----------- | :----------------------------------------------------------------------------------------------------------------------------------- | :------------------------------ |
| `smiles`                | string       | A notação SMILES canônica da molécula, usada como identificador único.                                                               | `CCO`                           |
| `xyz`                   | string       | As coordenadas cartesianas (em formato string XYZ) do confôrmero de menor energia **após a otimização final com PM7**.                | `"9\n\nC -1.2...\n..."`       |
| `multiplicity`          | integer      | A multiplicidade de spin da molécula (geralmente 1 para as moléculas alvo).                                                          | `1`                             |
| `charge`                | integer      | A carga molecular total.                                                                                                             | `0`                             |
| `nheavy`                | integer      | O número de átomos pesados (não-hidrogênio).                                                                                         | `2`                             |
| `H298_pm7`              | float        | **[Valor Principal]** A entalpia de formação padrão a 298.15K (em **kcal/mol**) calculada com PM7.                                     | `-56.12`                        |
| `S298_pm7`              | float        | A entropia padrão molar a 298.15K (em **cal/mol·K**) calculada com PM7/MOPAC. Preencher com `NaN` se não disponível.                     | `67.5`                          |
| `H0_pm7`                | float        | A entalpia de formação padrão a 0K (em **kcal/mol**) calculada com PM7. Preencher com `NaN` se não disponível.                          | `-51.34`                        |
| `Cp_300_pm7` (exemplo)  | float        | A capacidade calorífica a pressão constante (em **cal/mol·K**) a uma dada temperatura. Preencher com `NaN` se não disponível.          | `15.8`                          |
| *...outras colunas...*  | float        | Outras colunas do `thermo_cbs.csv` podem ser replicadas e preenchidas com `NaN` para manter a consistência do esquema.                 | `NaN`                           |

## **3. Notas Importantes**

*   **Consistência de Unidades:** É crucial que as unidades sejam idênticas às do `thermo_cbs.csv`.
    *   Entalpia (H): **kcal/mol**
    *   Entropia (S): **cal/mol·K**
    *   Capacidade Calorífica (Cp): **cal/mol·K**
*   **Fonte da Geometria:** A coluna `xyz` deve conter a geometria final otimizada pelo método PM7, pois é a geometria para a qual o valor `H298_pm7` é válido.
