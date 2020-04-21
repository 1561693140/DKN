import os
from model.dkn import DKN
from torch.utils.data import DataLoader
import torch
import torch.nn as nn
import time
import numpy as np
from config import Config
from dataset import DKNDataset


def main():
    train_dataset = DKNDataset(Config,
                               os.path.join('processed_data', 'train.txt'))
    test_dataset = DKNDataset(Config, os.path.join('processed_data',
                                                   'test.txt'))
    print(
        f"Load dataset with train size {len(train_dataset)} and test size {len(test_dataset)}."
    )

    train_dataloader = iter(
        DataLoader(
            train_dataset,
            batch_size=Config.batch_size,
            shuffle=True,
            num_workers=Config.num_workers,
            drop_last=True))

    # Load trained embedding file
    embeddings = {
        # num_word_tokens, word_embedding_dim
        "word": np.load(os.path.join('processed_data', 'word.npy')),
        # num_entity_tokens, entity_embedding_dim
        "entity": np.load(os.path.join('processed_data', 'entity.npy')),
        # num_entity_tokens, entity_embedding_dim
        "context": np.load(os.path.join('processed_data', 'context.npy'))
    }

    dkn = DKN(Config, embeddings).to(device)
    print(dkn)

    val_loss, val_acc = check_loss_and_acc(dkn, test_dataset)
    print(
        f"Initial result on test dataset, validation loss: {val_loss:.6f}, validation accuracy: {val_acc:.6f}"
    )
    
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(dkn.parameters(), lr=Config.learning_rate)
    start_time = time.time()
    loss_full = []
    exhaustion_count = 0

    for i in range(1, Config.num_batches + 1):
        try:
            minibatch = next(train_dataloader)
            y_pred = dkn(minibatch["candidatae_news"],
                         minibatch["clicked_news"])
            y = minibatch["clicked"].float().to(device)
            loss = criterion(y_pred, y)
            loss_full.append(loss.item())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if i % Config.num_batches_batch_loss == 0:
                print(
                    f"Time {time_since(start_time)}, batches {i}, current loss {loss.item():.6f}, average loss: {np.mean(loss_full):.6f}"
                )

            if i % Config.num_batches_val_loss_and_acc == 0:
                val_loss, val_acc = check_loss_and_acc(dkn, test_dataset)
                print(
                    f"Time {time_since(start_time)}, batches {i}, validation loss: {val_loss:.6f}, validation accuracy: {val_acc:.6f}"
                )

        except StopIteration:
            exhaustion_count += 1
            print(
                f"Training data exhausted for {exhaustion_count} times after {i} batches, reuse the dataset."
            )
            train_dataloader = iter(
                DataLoader(train_dataset,
                           batch_size=Config.batch_size,
                           shuffle=True,
                           num_workers=Config.num_workers,
                           drop_last=True))


@torch.no_grad()
def check_loss_and_acc(model, dataset):
    """
    Check loss and accuracy of trained model on given dataset.
    """
    dataloader = DataLoader(dataset,
                            batch_size=Config.batch_size,
                            shuffle=True,
                            num_workers=Config.num_workers,
                            drop_last=True)

    criterion = nn.BCELoss()
    loss_full = []
    total = 0
    correct = 0
    for minibatch in dataloader:
        y_pred = model(minibatch["candidatae_news"], minibatch["clicked_news"])
        y = minibatch["clicked"].float().to(device)
        loss = criterion(y_pred, y)
        loss_full.append(loss.item())
        y_pred_np = y_pred.cpu().numpy() > 0.5
        y_np = y.cpu().numpy() > 0.5
        total += y_pred_np.shape[0]
        correct += sum(y_pred_np == y_np)

    return np.mean(loss_full), correct / total


def time_since(since):
    """
    Format elapsed time string.
    """
    now = time.time()
    elapsed_time = now - since
    return time.strftime("%H:%M:%S", time.gmtime(elapsed_time))


if __name__ == '__main__':
    # setting device on GPU if available, else CPU
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print('Using device:', device)
    main()
