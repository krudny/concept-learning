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



