---
marp: true
theme: concept-learning
lang: pl
size: 16:9
paginate: true
header: "Concept Learning"
title: "Concept Learning"
author: "Kamil Rudny, Szymon Szarek, Mateusz Grzybek"
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _footer: "Kamil Rudny, Szymon Szarek, Mateusz Grzybek<br>Akademia Górniczo-Hutnicza w Krakowie" -->

# Czy możemy odkryć, czego nauczyła się sieć neuronowa?

Learning Concept Bottleneck Models from Mechanistic Explanations, ICLR 2026

---

# Problem

Pokazujemy przykład ptaka rozpoznanego przez sieć, która nie potrafi wyjaśnić swojej decyzji.

---

# Wcześniejsze rozwiązanie: CBM

Wyjaśniamy, że CBM najpierw sprawdza obecność cech (żółta głowa, czarna maska), a potem wybiera gatunek tylko na ich podstawie.

---

# Co jest nie tak z CBM

Pokazujemy dwa problemy: cechy wybrane z góry nie pasują do zdjęć, a losowe słowa dają podobny wynik, czyli program oszukuje.

---

# Pomysł autorów

Przedstawiamy ideę, żeby zamiast zgadywać cechy wydobyć je z samej sieci, i pokazujemy cztery kroki na jednym schemacie.

---

# Kroki 1 i 2: rozłożyć i nazwać

Tłumaczymy na przykładzie mieszania farb, jak SAE rozkłada notatki sieci na przełączniki i jak GPT nadaje im nazwy na podstawie 10 zdjęć.

---

# Kroki 3 i 4: sprawdzić i zbudować

Pokazujemy, jak GPT potwierdza nazwy na około 1000 zdjęć i jak powstaje czytelny program, który wybiera gatunek z około pięciu cech.

---

# Wyniki i ograniczenia

Podajemy wyniki 76,7%, 73,7% i 69,1% na zbiorze ptaków, przykład znamienia poprawionego jedną cechą oraz główne ograniczenia metody.

---

# Co chcemy sprawdzić

Formułujemy trzy pytania projektu: czy przełączniki mają sens, która metoda daje najczytelniejsze cechy i czy wyłączenie cechy zmienia decyzję.

---

# Dane i modele

Podajemy wybrany zbiór danych CUB-200-2011, model ResNet18 i orientacyjny czas treningu.

---

# Plan w trzech poziomach

Opisujemy jednym zdaniem każdy poziom: minimum, wersję właściwą i wersję ambitną.

---

# Jak ocenimy wyniki

Wymieniamy sposoby oceny: przegląd najmocniej aktywujących zdjęć, porównanie PCA, autoencodera i SAE oraz test wyłączania cech.

---

# Harmonogram i ryzyka (??)

Pokazujemy terminy kolejnych labów i główne ryzyka: koszt GPT, słabe przełączniki oraz brak GPU.