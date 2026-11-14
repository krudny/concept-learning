# Third-party notices

## M-CBM

Parts of this project are adapted from [M-CBM](https://github.com/Antonio-Dee/M-CBM)
(De Santis et al., *Learning Concept Bottleneck Models from Mechanistic Explanations*, ICLR 2026):

| Our file | Adapted from |
|---|---|
| `src/concept_learning/data.py` | `mcbm/data/data_cub.py`, `mcbm/data/utils.py` |
| `src/concept_learning/scripts/extract_activations.py` | `mcbm/scripts/extract_activations.py` |
| `src/concept_learning/scripts/train_sae.py` | `mcbm/scripts/train_sae.py` |
| `src/concept_learning/topk.py` | `mcbm/scripts/name_concepts.py` (top-K selection, concept heatmaps) |
| `src/concept_learning/sae.py` | re-implements the SAE from [`sparse_autoencoder`](https://github.com/ai-safety-foundation/sparse_autoencoder) 1.10 (MIT), as used by M-CBM |

```
MIT License

Copyright (c) 2026 Antonio De Santis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
