---
marp: true
theme: concept-learning
lang: pl
size: 16:9
paginate: true
header: "Concept Learning"
title: "Czy możemy odkryć, czego nauczyła się sieć neuronowa?"
author: "Kamil Rudny, Szymon Szarek, Mateusz Grzybek"
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _footer: "Kamil Rudny, Szymon Szarek, Mateusz Grzybek<br>Akademia Górniczo-Hutnicza w Krakowie" -->

# Czy możemy odkryć, czego nauczyła się sieć neuronowa?

*Learning Concept Bottleneck Models from Mechanistic Explanations*
ICLR 2026 (Antonio De Santis et al., MIT CSAIL & Polimi)

<!--
Notatki:
- Wprowadzenie tematu: interpretowalność mechaniczna sieci (ICLR 2026, MIT & Polimi)
- Cel: odkrywanie ludzkich pojęć wewnątrz modeli wizyjnych
- Plan: 1. Omówienie artykułu (M-CBM), 2. Nasz plan laboratoryjny
-->

---
<!-- 1 -->
# Problem: sieć neuronowa nie wyjaśnia swoich decyzji

Sieć neuronowa rozpoznaje gatunek ptaka na zdjęciu z dużą dokładnością, ale nie potrafi wyjaśnić, dlaczego wybrała właśnie ten gatunek.

Decyzja wynika z działania milionów parametrów w kolejnych warstwach sieci. Pojedynczy neuron często reaguje na kilka niepowiązanych ze sobą wzorców, więc nie da się mu przypisać jednej cechy, którą człowiek mógłby nazwać.

Z zewnątrz widzimy tylko wynik. Nie wiemy, czy sieć patrzy na ptaka, czy na przypadkowy szczegół, na przykład tło zdjęcia.

<div class="flow">
  <div class="flow-box"><span class="flow-label">Wejście</span>Zdjęcie ptaka</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Sieć neuronowa</span>Miliony parametrów w ukrytych warstwach</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Wyjście</span>Hooded Warbler</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box flow-box-open"><span class="flow-label">Problem</span>Brak odpowiedzi, skąd wziął się wynik</div>
</div>

---

<!-- 2 -->
# Dlaczego wyjaśnialność ma znaczenie

**Zaufanie w zastosowaniach krytycznych.** Artykuł wymienia opiekę zdrowotną, autonomiczne samochody i obronność jako dziedziny, w których model musi być przejrzysty, a nie tylko dokładny.

**Wykrywanie fałszywych korelacji.** Sieć może dać poprawny wynik z niewłaściwego powodu, na przykład rozpoznać ptaka po tle. Bez wyjaśnienia nikt tego nie zauważy.

**Poprawianie błędów.** W artykule wyzerowanie jednego pojęcia zmieniło błędną diagnozę znamienia na poprawną. Znajomość zawodnej cechy pozwala ją skorygować.

**Odpowiedzialność za decyzję.** Osoba korzystająca z wyniku, na przykład lekarz, musi umieć go uzasadnić przed pacjentem.

---

<!-- 3 -->
# Dwa sposoby wyjaśniania decyzji sieci

Metody wyjaśniania dzielą się na dwie grupy, zależnie od tego, czy wyjaśniamy gotową sieć, czy budujemy sieć, która wyjaśnia się sama.

<div class="tree">
  <div class="tree-box tree-root">Wyjaśnianie decyzji sieci neuronowej</div>
  <div class="tree-branches">
    <div class="tree-branch">
      <div class="tree-arrow">↓</div>
      <div class="tree-box"><span class="flow-label">Post-hoc</span>Po fakcie</div>
    </div>
    <div class="tree-branch">
      <div class="tree-arrow">↓</div>
      <div class="tree-box"><span class="flow-label">Ante-hoc</span>Z założenia</div>
    </div>
  </div>
</div>

---

<!-- 4 -->
# Post-hoc, czyli wyjaśnianie po fakcie

**Jak działa?** Sieć jest już wytrenowana i zostaje bez zmian. Mapa atrybucji (ang. Saliency) sprawdza, jak zmiana pikseli wpływa na wynik wybranej klasy, i zaznacza je na zdjęciu jako mapę ciepła.

**Co daje?** Zaznacza obszary zdjęcia, które najmocniej podniosły wynik klasy. Wskazuje, na co sieć zwróciła największą uwagę. 

**Ograniczenie.** Mapa nie mówi, czy zaznaczony obszar oznacza dziób, kolor czy teksturę. Nie wiemy, jakie pojęcie sieć rozpoznała.

<div class="flow">
  <div class="flow-box"><span class="flow-label">Wejście</span>Zdjęcie ptaka</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Sieć</span>Wytrenowana, bez zmian</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Wyjście</span>Hooded Warbler</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box flow-box-open"><span class="flow-label">Wyjaśnienie</span>Mapa ciepła na pikselach</div>
</div>

---

<!-- 5 -->
# Ante-hoc, czyli CBM z nazwanych pojęć

**Jak działa?** CBM dzieli model na dwie części. Warstwa pojęć (ang. Concept Bottleneck Layer) przewiduje z obrazu, które z nazwanych pojęć występują. Rzadki klasyfikator liniowy wybiera klasę wyłącznie na podstawie wartości tych pojęć. Cała informacja o obrazie musi przejść przez wąskie gardło, czyli listę pojęć.

**Co daje?** Decyzję można odczytać wprost, bo wkład pojęcia w klasę to jego wartość pomnożona przez wagę.

<div class="flow">
  <div class="flow-box"><span class="flow-label">Wejście</span>Zdjęcie ptaka</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box flow-box-wide"><span class="flow-label">Warstwa pojęć</span>żółty ptak z czarną maską wokół oczu<br>czarna maska wokół żółtej twarzy<br>oliwkowozielony grzbiet</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Klasyfikator liniowy</span>Wybór klasy z pojęć</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Wyjście</span>Hooded Warbler</div>
</div>

---

<!-- _class: two-columns -->
<!-- 6 -->
# Co jest nie tak z CBM?

<div>

## Problem 1. Pojęcia wybrane z góry

Dotychczasowe metody biorą pojęcia od ekspertów, z grafów wiedzy (baz powiązanych pojęć) albo z odpowiedzi dużych modeli językowych (LLM). Takie pojęcia mogą nie pomagać w rozpoznaniu klasy albo nie dać się nauczyć z obrazów. Dla zbioru zmian skórnych LLM zaproponował pojęcia "warm to the touch" i "medical report", których nie widać na zdjęciu.

</div>
<div>

## Problem 2. Wyciek informacji

Wyciek oznacza, że CBM jest dokładny dzięki ukrytym wzorcom w wartościach pojęć, a nie dzięki ich znaczeniu. Pojęcie oznaczone tylko na obrazach jednej klasy działa jak etykieta tej klasy. VLG-CBM, z losowymi frazami typu "bird pizza" zamiast nazw pojęć, dorównuje dokładnością oryginalnej sieci przy średnio około 1,5 pojęcia na decyzję. Model wygląda na czytelny, ale w praktyce dalej jest czarną skrzynką.

</div>

---

<!-- 7 -->
# Pomysł autorów, czyli Mechanistic CBM (M-CBM)

Zamiast wybierać pojęcia z góry, autorzy biorą te, których wytrenowana sieć już używa. Spodziewają się, że łatwiej je nauczyć i że lepiej przewidują klasę.

Metoda ma cztery kroki.

<div class="flow">
  <div class="flow-box"><span class="flow-label">Krok 1</span>Autoenkoder rzadki (SAE) rozkłada reprezentację na kandydatów na pojęcia</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Krok 2</span>Model GPT-4.1 nazywa każdy neuron na podstawie zdjęć</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Krok 3</span>GPT-4.1 oznacza zdjęcia treningowe</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Krok 4</span>Trening warstwy pojęć i klasyfikatora</div> <!-- Skróciłem te punkty, bo te wpisy są dokładniej rozwinięte na następnych slajdach-->
</div>

---

<!-- 8 -->
# Krok 1. Wydobycie pojęć z sieci

Każde zdjęcie treningowe przechodzi przez wytrenowaną sieć, która zamienia je na wektor liczb. W ResNet-18 ma on 512 liczb. Pojedyncza liczba nie odpowiada jednej cesze, bo cechy w wektorze są pomieszane.

Autoenkoder rzadki (SAE) rozkłada ten wektor na wiele prostych składników. SAE uczy się jednocześnie odtwarzać wektor i aktywować dla jednego zdjęcia tylko kilka neuronów — każdy taki neuron to kandydat na pojęcie.

<!-- Na zbiorze CUB SAE ma 512 neuronów, a dla jednego zdjęcia włącza się średnio 7,66 z nich. Neurony, które nie włączają się nigdy lub prawie nigdy, autorzy usuwają, o ile jakość spada najwyżej o około 1%.  usunięte - Powtórzenie treści z diagramu--> 

<div class="flow">
  <div class="flow-box"><span class="flow-label">Wejście</span>Zdjęcie ptaka (zbiór CUB-200)</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Sieć</span>Wektor 512 liczb</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">SAE</span>Rozkład na neurony</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Wynik</span>Włączone średnio 7,66 z 512 neuronów</div>
</div>

<br>
<small>SAE - Sparse Autoencoder - Autoenkoder rzadki</small>

---

<!-- 9 -->
# Krok 2. Nazwanie pojęć

Dla każdego neuronu SAE autorzy wybierają 10 zdjęć, które włączają go najmocniej, i nakładają na nie mapy ciepła. Dodają 10 zdjęć, które go nie włączają. Połowa jest losowa, druga połowa podobna do aktywnych, by wymusić wskazanie drobnej cechy przez model.

GPT-4.1 dostaje te zdjęcia i pytanie "What is this neuron looking for?". Odpowiada krótką nazwą, na przykład "black mask around yellow face". Nie może użyć nazwy klasy. Jeśli to zrobi, pytanie jest ponawiane.

Na końcu autorzy łączą nazwy o podobieństwie powyżej 0,98 w jedno pojęcie. Zostaje 278 pojęć dla CUB, 73 dla ISIC2018 i 2648 dla ImageNet. Nazwanie jednego pojęcia kosztuje około 0,02 USD.

<div class="flow">
  <div class="flow-box"><span class="flow-label">Neuron SAE</span>Kandydat na pojęcie</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Zdjęcia</span>10 aktywnych i 10 nieaktywnych</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">GPT-4.1</span>Co szuka ten neuron?</div>
  <div class="flow-arrow">→</div>
  <div class="flow-box"><span class="flow-label">Wynik</span>Krótka nazwa pojęcia</div>
</div>

---

<!-- 10 -->
# Krok 3. Oznaczenie zdjęć

Nazwa neuronu to tylko hipoteza o tym, na co on reaguje. Dlatego autorzy nie używają neuronów SAE wprost jako pojęć. GPT-4.1 oznacza zdjęcia treningowe, a nowa warstwa pojęć uczy się na tych etykietach.

Połowa zdjęć wybieranych dla każdego pojęcia mocno włącza neuron (powyżej 95. percentyla aktywacji), a połowa to zdjęcia nieaktywne. Obie grupy obejmują równomiernie wszystkie klasy, żeby pojęcie nie związało się z jedną klasą.

Siatka jest tańsza, ale mniej dokładna. Na CUB trafność oznaczeń wynosi 69,46% przy siatce i 74,00% przy etykietowaniu pojedynczych zdjęć, co wymaga jednak 25 razy więcej zapytań.

<div class="stat-grid">
  <div class="stat-box"><span class="stat-num">1000</span><span class="stat-label">zdjęć na jedno pojęcie</span></div>
  <div class="stat-box"><span class="stat-num">5 × 5</span><span class="stat-label">25 zdjęć w jednym zapytaniu do GPT-4.1</span></div>
  <div class="stat-box"><span class="stat-num">1 / 0 / -1</span><span class="stat-label">jest, brak, brak etykiety</span></div>
</div>

---

<!-- 11 -->
# Krok 4. Trening modelu z wąskim gardłem

Model ma trzy części. Zamrożona sieć zamienia zdjęcie na wektor liczb. Warstwa pojęć (CBL) przewiduje z niego, czy występuje każde pojęcie, i uczy się na etykietach z kroku 3, pomijając pary bez etykiety. Rzadki klasyfikator liniowy wybiera klasę wyłącznie na podstawie wartości pojęć.

Kara w klasyfikatorze zeruje większość wag, więc każda klasa zależy od kilku pojęć. Wkład pojęcia w decyzję to jego wartość pomnożona przez wagę. Poniżej wkłady dla Hooded Warbler.

<div class="bars">
  <div class="bar-row"><span class="bar-label">żółty ptak z czarną maską wokół oczu</span><span class="bar-track"><span class="bar-fill" style="width: 100%"></span></span><span class="bar-value">+4,80</span></div>
  <div class="bar-row"><span class="bar-label">czarna maska wokół żółtej twarzy</span><span class="bar-track"><span class="bar-fill" style="width: 90%"></span></span><span class="bar-value">+4,34</span></div>
  <div class="bar-row"><span class="bar-label">jaskrawożółte upierzenie z czarną czapką</span><span class="bar-track"><span class="bar-fill" style="width: 27%"></span></span><span class="bar-value">+1,28</span></div>
  <div class="bar-row"><span class="bar-label">żółty wierzch, ciemne ciało i dziób</span><span class="bar-track"><span class="bar-fill" style="width: 8%"></span></span><span class="bar-value">+0,38</span></div>
  <div class="bar-row"><span class="bar-label">oliwkowozielony grzbiet</span><span class="bar-track"><span class="bar-fill" style="width: 3%"></span></span><span class="bar-value">+0,12</span></div>
  <div class="bar-row"><span class="bar-label">pozostałe 273 pojęcia razem</span><span class="bar-track"><span class="bar-fill bar-fill-muted" style="width: 1%"></span></span><span class="bar-value">+0,05</span></div>
</div>

---

<!-- 12 -->
# NCC, czyli uczciwe porównanie modeli

Im więcej pojęć klasyfikator może użyć, tym wyższą ma dokładność, ale rośnie też wyciek, a wyjaśnienia robią się długie. Modele trzeba więc porównywać przy takiej samej liczbie pojęć w decyzji.

Wcześniejsza miara NEC (Number of Effective Concepts) liczy średnią liczbę niezerowych wag na klasę. Przy małej liczbie klas ogranicza ona cały słownik pojęć, bo przy 3 klasach i NEC=5 model może mieć najwyżej 15 pojęć.

NCC (Number of Contributing Concepts) liczy dla każdej decyzji, ile pojęć pokrywa 95% sumy wkładów, i uśrednia wynik. NCC=5 oznacza, że średnio 5 pojęć tłumaczy co najmniej 95% decyzji. Model może mieć wiele pojęć, ale pojedynczą decyzję tłumaczy kilkoma.

---

<!-- 13 -->
# Wyniki i ograniczenia metody M-CBM

- **Trafność CUB-200** ($NCC=5$): **76.7%** (Black-Box) vs **73.7%** (**M-CBM**) vs **69.1%** (VLG-CBM).
- **Interwencja**: modyfikacja pojedynczej cechy odwraca błędną diagnozę czerniaka (ISIC 2018).
- **Ograniczenia**: koszt i czas zapytań API VLM (~0.16$ / cechę), trudności ze skalowaniem przy tysiącach pojęć.

<div class="img-center">

![width:800px](img/slajd09_isic.png)

</div>

<!--
Notatki:
- Wyniki na ptakach (CUB-200): M-CBM (73.7%) deklasuje VLG-CBM (69.1%) i goni Black-Box (76.7%)
- Interwencja: zmiana 1 cechy koryguje błędną diagnozę czerniaka (ISIC)
- Ograniczenia: koszt i czas API modeli VLM (~0.16$/cechę)
-->

---

<!-- 14 -->
# Co chcemy sprawdzić w projekcie?

<div class="grid-3">

<div class="card">
<span class="badge">Pytanie 1</span>
<h3>Czytelność cech</h3>
<p>Czy cechy wyuczone przez SAE odpowiadają spójnym pojęciom wizualnym (inspekcja Top-K aktywacji)?</p>
</div>

<div class="card">
<span class="badge">Pytanie 2</span>
<h3>Porównanie metod</h3>
<p>Która metoda daje najczytelniejszą reprezentację: <b>PCA</b>, gęsty <b>Autoenkoder</b> czy <b>SAE</b>?</p>
</div>

<div class="card">
<span class="badge">Pytanie 3</span>
<h3>Wpływ ablacji</h3>
<p>Czy wyzerowanie danej cechy (interwencja) w przewidywalny sposób zmienia decyzję klasyfikatora?</p>
</div>

</div>

<!--
Notatki:
- Pytanie 1: inspekcja wizualna - czy cechy z SAE są czytelne dla oka ludzkiego?
- Pytanie 2: porównanie metod redukcji - PCA vs gęsty Autoenkoder vs rzadki SAE
- Pytanie 3: interwencja / ablacja - czy wyzerowanie cechy logicznie zmienia wynik?
-->

---

<!-- _class: two-columns -->

# Dane i modele bazowe

<div>

- **Zbiór CUB-200-2011**:
  200 gatunków ptaków, wyraziste cechy wizualne (dziób, ubarwienie, skrzydła).
- **Model bazowy (Backbone)**:
  ResNet-18, ekstrakcja wektora 512 cech z warstwy `avgpool`.
- **Środowisko obliczeniowe**:
  PyTorch + biblioteka SAE, czas treningu SAE: **~10–20 min na GPU**.

</div>
<div class="col-right">

![width:600px](img/slajd10_cub_grid.png)

</div>

<!--
Notatki:
- Zbiór: CUB-200-2011 (200 gatunków ptaków, bogate cechy anatomiczne)
- Backbone: ResNet-18, ekstrakcja 512 cech z warstwy avgpool
- Czas treningu: SAE na zamrożonych embeddingach uczy się szybko (~10-20 min na GPU)
-->

---

# Plan realizacji w trzech poziomach

<div class="grid-3">

<div class="card">
<span class="badge">Poziom 1: MVP</span>
<h3>Minimum</h3>
<ul>
  <li>Trening ResNet-18 i ekstrakcja cech.</li>
  <li>Trening Sparse Autoencodera (SAE).</li>
  <li>Wizualizacja Top-K aktywacji dla cech.</li>
</ul>
</div>

<div class="card">
<span class="badge">Poziom 2: Standard</span>
<h3>Wersja właściwa</h3>
<ul>
  <li>Porównanie: <b>PCA vs AE vs SAE</b>.</li>
  <li>Ocena rzadkości i błędu rekonstrukcji.</li>
  <li>Testy ablacji (wyłączanie cech).</li>
</ul>
</div>

<div class="card">
<span class="badge">Poziom 3: Ambitny</span>
<h3>Wersja rozszerzona</h3>
<ul>
  <li>Etykietowanie cech modelem VLM.</li>
  <li>Rzadki klasyfikator liniowy na cechach.</li>
  <li>Weryfikacja wycieku informacji (*leakage*).</li>
</ul>
</div>

</div>

<!--
Notatki:
- Poziom 1 (MVP): pipeline bazowy (ResNet-18 + SAE + skrypt wizualizacji Top-K)
- Poziom 2 (Właściwy): porównanie jakości reprezentacji (PCA vs AE vs SAE) + ablacja
- Poziom 3 (Ambitny): automatyczne nazwy z VLM + klasyfikator + test leakage
-->

---

# Jak ocenimy wyniki? (Ewaluacja)

| Wymiar ewaluacji | Metoda / Metryka | Cel weryfikacji |
|---|---|---|
| **Interpretowalność** | Inspekcja Top-K obrazów | Spójność wizualna aktywacji cechy |
| **Monosemantyczność** | Porównanie PCA, AE i SAE | Skuteczność rozplątania superpozycji |
| **Wierność rekonstrukcji** | Błąd MSE + Spadek Accuracy | Zachowanie wiedzy modelu ResNet-18 |
| **Ablacja (Interwencja)** | Zmiana predykcji klasyfikatora | Wpływ wyłączenia cechy na pewność decyzji |

<!--
Notatki:
- Jakościowa: inspekcja wzrokowa Top-K (czy cecha reaguje zawsze na ten sam detal)
- Porównawcza: monosemantyczność w SAE vs gęsty autoenkoder i PCA
- Błąd rekonstrukcji: MSE i wpływ kompresji na accuracy klasyfikatora
- Ablacja: pomiar spadku pewności modelu po wyzerowaniu kluczowej cechy
-->