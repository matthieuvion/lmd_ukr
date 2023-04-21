### Dataset - Le Monde Guerre en Ukraine
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)


Out of curiosity, a `Dataset` of articles and comments from Le Monde, 1 year coverage of the War in Ukraine (Feb 24 2022 -> 2023). <br/> *Important* : the data is collected and shared by me for educational & research purposes only ; premium articles (suscriber only) have been truncated to first 2500 characters.
</br>
</br>

### Dataset
---

> Download [/dataset](https://github.com/matthieuvion/lmd_ukr/tree/main/dataset) (40mb) <br>
> 236 k comments and associated articles (2 k unique), title & article desc <br>
![dataset structure](https://github.com/matthieuvion/lmd_ukr/blob/master/dataset/cols_overview.png "dataset structure")



#### Limitations (comments):
- no distinction between comments and replies-to-comment
- no timestamp, only associated article (last) publication date



### Workflow, things you might re-use
---

#### 1. Data Collection
**Custom API** <br>
\- To be seen as a good, but not top (i.e. scalable etc.) one-shot-project" API, shared "as is" <br>
\- Le Monde does not offer a public API --as the New York Times ;) <br>
\- Personal credentials (suscriber) are required, because comments are suscribers-only <br>
\- Built using `httpx` for requests & `selectolax` for parsing <br>
\- API & use examples with caching available repo ; added some documentation in-code (rate limits etc.) <br>

#### 2. Dataset prep
\- Parsed data populated into an sqlite db with two tables articles and comments with shared key `article_id` <br>
\- This was optional, but wanted to refresh my skills and it allows to remove duplicates when building our db <br>
\- Formating / cleaning using `Polars`, wanted to benchmark v. `Pandas` (cf. [notebook](https://github.com/matthieuvion/lmd_ukr/blob/main/lmd_ukr/build_parquet_dataset.ipynb)) <br>
\- Final file is a joined articles-comments (tidy) parquet file. <br>



### Data Usage
---

I created and shared this dataset for educational purposes only. Just wanted to have a French dataset, --if possible from my favorite newspaper on a topic I'm following daily; instead of exploring the same boring english datasets we're used to.
It could be used for various natural language processing tasks.

- Topic modeling
- Troll detection (not enough fields though in my opinion)
- Generate summaries or headlines for articles (and compare to "desc" for instance)
- trending & various generative tasks of your choice
- (...)
