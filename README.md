PROJEKT 3: Projekt: Can We Discover What a Neural Network Has Learned?
Inspiracja:
M-CBM: Learning Concept Bottleneck Models from Mechanistic Explanations, ICLR 2026. Praca pokazuje, jak z wewnętrznych reprezentacji wytrenowanej sieci neuronowej odkrywać potencjalnie interpretowalne cechy i pojęcia, m.in. z użyciem Sparse Autoencodera.
Dane:
Zbiór obrazowy do klasyfikacji, np. CUB-200-2011, ISIC 2018 albo CIFAR-10. Najlepiej taki, w którym można sensownie interpretować cechy wizualne obiektów.
Zadaniem jest:
Wytrenowanie klasyfikatora obrazów, np. ResNet lub ViT, a następnie analiza jego wewnętrznych reprezentacji. Studenci powinni wyodrębnić embeddingi z wybranej warstwy sieci i zastosować do nich Sparse Autoencoder w celu znalezienia rzadkich, potencjalnie interpretowalnych cech. Następnie należy zidentyfikować obrazy najmocniej aktywujące poszczególne cechy i ocenić, czy odpowiadają one rozpoznawalnym pojęciom wizualnym. Projekt powinien także porównać interpretowalność reprezentacji uzyskanych za pomocą PCA, klasycznego autoencodera i Sparse Autoencodera oraz zbadać, czy manipulacja wybranymi cechami wpływa na decyzję klasyfikatora.
Projekt można naturalnie podzielić na trzy poziomy.
Minimum: wytrenować classifier + SAE i wizualizować Top-K obrazy dla latentów.
Wersja właściwa: ocenić, czy odkrywane latenty są interpretowalne i porównać PCA/AE/SAE.
Ambitna: nazwać automatycznie odkryte concepts za pomocą VLM/LLM i zbudować prosty classifier:

## Instalacja

Wymagany [uv](https://docs.astral.sh/uv/). Wybierz wariant PyTorcha:

```bash
uv sync --extra cu128   # maszyna z GPU NVIDIA (CUDA 12.8, w tym RTX 50xx)
uv sync --extra cpu     # laptop bez GPU
```

Każde kolejne `uv run` musi dostać ten sam `--extra`, np. `uv run --extra cu128 python -m ...`.

Zbiór danych (~1,1 GB, trafia do `datasets/CUB_200_2011`, inną lokalizację można ustawić zmienną `DATASET_FOLDER`):

```bash
uv run --extra cu128 python -m concept_learning.scripts.download_cub
```

## Pipeline (poziom minimum)

Wszystkie wyniki trafiają do `outputs/<etap>/<nazwa_runu_z_datą>/`. Hiperparametry są w `configs/cub.json`.

Jednostki ukryte SAE (w opisie zadania „latenty”) nazywamy w projekcie i w kodzie **neuronami SAE** (`neuron`).

1. Fine-tuning ResNet-18 (wagi ImageNet) na CUB. Zapisuje `model.pt`, krzywe uczenia i accuracy na teście:

   ```bash
   uv run --extra cu128 python -m concept_learning.scripts.train_classifier --config configs/cub.json
   ```

2. Embeddingi 512-wymiarowe z `avgpool` dla train / val / test:

   ```bash
   uv run --extra cu128 python -m concept_learning.scripts.extract_activations --config configs/cub.json --checkpoint outputs/classifier/<RUN>/model.pt
   ```

   Zamiast własnego modelu można użyć modelu autorów M-CBM: `--backbone resnet18_cub_pytorchcv` (bez `--checkpoint`).

3. Sparse Autoencoder na embeddingach, z przycinaniem rzadko aktywnych neuronów SAE:

   ```bash
   uv run --extra cu128 python -m concept_learning.scripts.train_sae --config configs/cub.json --activation-dir outputs/activations/<RUN>
   ```

   Domyślny współczynnik L1 (`sae_l1_coefficient = 0.008`) jest dobrany przeglądem pod własny ResNet-18, którego embeddingi mają ok. 2,3× większą normę niż u modelu autorów. Dla modelu autorów artykuł używa `0.002`. Po zmianie klasyfikatora warto najpierw przejrzeć kilka wartości (`sae_l1_sweep`, albo `--l1 0.002 0.004 ...`) i wpisać do configu tę, która daje rzadkość bliską artykułowi (L0 ≈ 7,66) bez dużego spadku recovered loss / accuracy:

   ```bash
   uv run --extra cu128 python -m concept_learning.scripts.sweep_sae --config configs/cub.json --activation-dir outputs/activations/<RUN>
   ```

   Wyniki trafiają do `outputs/sae_sweep/<RUN>/`: `summary.csv`, wykres `sweep.png` i pełny run SAE dla każdej wartości (`l1_<wartość>/`), który można też otworzyć w notebooku, ustawiając `SAE_DIR` na jego ścieżkę.

4. Wizualizacja Top-K: `notebooks/topk_neurons.ipynb` (domyślnie bierze najnowszy run z `outputs/sae/`):

   ```bash
   uv run --extra cu128 jupyter lab notebooks/topk_neurons.ipynb
   ```

   Notebook commitujemy razem z wynikami, żeby galeria była widoczna na GitHubie.

Testy (syntetyczny mini-zbiór, ok. 20 s na CPU): `uv run --extra cpu pytest`.

Część kodu jest zaadaptowana z repozytorium [M-CBM](https://github.com/Antonio-Dee/M-CBM), zob. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).



