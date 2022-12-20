# KBRedundancies

The Goal of this project is to identify how many semantic redundancies are in modern KBs, and try to semantically compress the facts in the KBs.

## 1. Definition of "Redundancies"

This project focuses on semantic redundancies in the factual knowledge.
Let <img src="https://latex.codecogs.com/svg.latex?\mathcal{F}" /> be the set of facts in a knowledge base <img src="https://latex.codecogs.com/svg.latex?\mathcal{B}" />, <img src="https://latex.codecogs.com/svg.latex?\mathcal{N}" /> and <img src="https://latex.codecogs.com/svg.latex?\mathcal{R}" /> be a partition of <img src="https://latex.codecogs.com/svg.latex?\mathcal{F}" />, <img src="https://latex.codecogs.com/svg.latex?\models" /> be logic entailment, <img src="https://latex.codecogs.com/svg.latex?r" /> be a first-order Horn rule.
<img src="https://latex.codecogs.com/svg.latex?\mathcal{R}" /> is redundant if <img src="https://latex.codecogs.com/svg.latex?\mathcal{N}\land{r}\models\mathcal{R}" />, or written as <img src="https://latex.codecogs.com/svg.latex?\mathcal{N}\models_r\mathcal{R}" />.
Similarly, if a set of Horn rules, denoted by <img src="https://latex.codecogs.com/svg.latex?\mathcal{H}" />, is applied on a KB, <img src="https://latex.codecogs.com/svg.latex?\mathcal{R}" /> is redundant if <img src="https://latex.codecogs.com/svg.latex?\mathcal{N}\models_\mathcal{H}\mathcal{R}" />.

The selection of the Horn rules is restricted by the size of the rules and number of counterexamples (denoted by <img src="https://latex.codecogs.com/svg.latex?\mathcal{C}" />) that comes along with the entailment.
That is, the total size, denoted by <img src="https://latex.codecogs.com/svg.latex?\|\mathcal{H}\|+|\mathcal{N}|+|\mathcal{C}|" /> (<img src="https://latex.codecogs.com/svg.latex?\textstyle\|\mathcal{H}\|=\sum_{r\in\mathcal{H}}|r|" />, <img src="https://latex.codecogs.com/svg.latex?|r|" /> is the size of rule <img src="https://latex.codecogs.com/svg.latex?r" />), should be as small as possible.
At least, it cannot be larger than <img src="https://latex.codecogs.com/svg.latex?|\mathcal{B}|" />.

## 2. Target KBs

The following types of KBs will be observed in this project:

1. Community Contributed Knowledge Sources:
   - KBs in this type are constructed by contributors in certain community, such as Wikipedia, through tools that are dedicated for the community and converted to some structured form
   - Targets: **FreeBase**, **WikiData**, **MusicBrainz**
2. Open-domain Extraction from Community Contributions:
   - KBs in this type are built by automatic extraction and integration of various community databases, such as WikiData, and are linked to the Linked Open Data (LOD) cloud.
   - Targets: **Yago**, **DBpedia**, **CNDBpedia**
3. Information Extraction from Raw Text:
   - KBs in this type are extracted via NLP techniques from raw text, such as the online websites.
   - Targets: **KnowItAll**, **NELL**, **ConceptNet**
4. Lexical Thesaurus
   - KBs in this type are constructed, by experts of by knowledge integration techniques, for managing lexical knowledge.
   - Targets: **WordNet**, **BabelNet**, **UMLS**
5. (\*) Logic Based
   - KBs in the type are usually represented in formal logic and are complicated. So they are optional in this project.
   - Targets: **Cyc**, **OpenCyc**

### 2.1 Release Versions

All KB versions should be the latest release before **[2022/05/01](https://)**.
The following releases should also be taken into account:

1. Yago: latest version of 1/2s/3

### 2.2 Language Versions

All of the target KBs should contain the English language version. The following language versions should also be taken into account:

1. WikiData: Chinese, French, Germany, Russian
2. WordNet: Chinese, French, Germany, Russian
3. BabelNet: Chinese, French, Germany, Russian

## 3. Methodology

The target KBs are very large even if only the facts are considered. Therefore, we try certain patterns by hand first and filter out the entailed facts. If there is no more handcrafted rules that are useful for semantic compression, we try SInC, the semantic compressor, on the remaining part of a KB.

The code for SInC is [here](https://github.com/TramsWang/SInC)

## 4. Repo Organization

This repo is organized as follows:

```
┳ README.md
┣ .gitignore
┣ common                    [Common utilities for KB operations]
┃ ┣ NumeratedKBFormat.md   [KB format specification]
┃ ┣ numeratedkb.py         [KB Operation Tools]
┃ ┗ kbstate.py             [Script for KB statistics]
┣ 1-CommunityContributed    [Results for type-1 KBs]
┣ 2-Open-domainExtraction   [Results for type-2 KBs]
┣ 3-InformationExtraction   [Results for type-3 KBs]
┣ 4-LexicalThesaurus        [Results for type-4 KBs]
┗ 5-LogicBased              [Results for type-5 KBs]
```

## 5. Dependencies
This repo is dependent on the NumerationKb formatter class implemented in [SInC](https://github.com/TramsWang/SInC).
Therefore, the code in SInC (version 2.1) should be installed in local maven repo.