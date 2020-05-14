# DKN

An implementation of [DKN](https://dl.acm.org/doi/abs/10.1145/3178876.3186175) (_Deep Knowledge-Aware Network for News Recommendation_) in PyTorch.

## Get started

Basic setup.

```bash
git clone https://github.com/yusanshi/DKN
cd DKN
pip3 install -r requirements.txt
```

Download the dataset.

```bash
mkdir data && cd data

# By downloading the dataset, you agree to the [Microsoft Research License Terms](https://go.microsoft.com/fwlink/?LinkID=206977). For more detail about the dataset, see https://msnews.github.io/.
wget https://mind201910small.blob.core.windows.net/release/MINDsmall_train.zip https://mind201910small.blob.core.windows.net/release/MINDsmall_dev.zip
sudo apt install unzip
unzip MINDsmall_train.zip -d train
unzip MINDsmall_dev.zip -d validate
rm MINDsmall_*.zip

# Merge train and validate dataset (currently the dataset is small so we do so to enlarge it)
mkdir merged
sort -u train/behaviors.tsv validate/behaviors.tsv > merged/behaviors.tsv
sort -u train/news.tsv validate/news.tsv > merged/news.tsv
sort -u train/entity_embedding.vec validate/entity_embedding.vec > merged/entity_embedding.vec

# Preprocess data in `merged` into appropriate format
python3 data_preprocess.py
cd ..
```

Run.

```bash
python3 main.py

# or use `run.sh` to compare the result with or without context embedding, attention mechanism.

chmod +x run.sh
./run.sh
```

You can visualize the result with TensorBoard.

```bash
tensorboard --logdir=runs
```

Training loss.

Example output.

```

```

## Credits

- Dataset by **MI**crosoft **N**ews **D**ataset (MIND).
