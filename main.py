from model.dkn import DKN
from torch.utils.data import DataLoader, Dataset, random_split
from torch.utils.tensorboard import SummaryWriter
import torch
import torch.nn as nn
import time
import numpy as np
import pickle
from config import Config


class DKNDataset(Dataset):
    def __init__(self, filepath):
        super(Dataset, self).__init__()
        with open(filepath, 'rb') as f:
            self.data = pickle.load(f)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def main():
    print(f"Context: {Config.use_context}, Attention: {Config.use_attention}")
    writer = SummaryWriter(
        comment=f"Context-{Config.use_context}_Attention-{Config.use_attention}")
    dataset = DKNDataset('data/merged/train.pkl')
    train_size = int(Config.train_split * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(dataset,
                                               (train_size, test_size))
    print(
        f"Load dataset with train size {len(train_dataset)} and test size {len(test_dataset)}."
    )

    train_dataloader = iter(
        DataLoader(train_dataset,
                   batch_size=Config.batch_size,
                   shuffle=True,
                   num_workers=Config.num_workers,
                   drop_last=True))

    # Load trained embedding file
    # num_entity_tokens, entity_embedding_dim
    entity_embedding = np.load('data/merged/entity_embedding.npy')
    context_embedding = np.load('data/merged/entity_embedding.npy')  # TODO

    dkn = DKN(Config, entity_embedding, context_embedding).to(device)
    print(dkn)

    val_loss, val_acc = check_loss_and_acc(dkn, test_dataset)
    writer.add_scalar('Loss/test', val_loss, 1)
    writer.add_scalar('Accuracy/test', val_acc, 1)
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
            y_pred = dkn(minibatch["candidate_news"],
                         minibatch["clicked_news"])
            y = minibatch["clicked"].float().to(device)
            loss = criterion(y_pred, y)
            loss_full.append(loss.item())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            writer.add_scalar('Loss/train', loss.item(), i)

            if i % Config.num_batches_batch_loss == 0:
                print(
                    f"Time {time_since(start_time)}, batches {i}, current loss {loss.item():.6f}, average loss: {np.mean(loss_full):.6f}"
                )

            if i % Config.num_batches_val_loss_and_acc == 0:
                val_loss, val_acc = check_loss_and_acc(dkn, test_dataset)
                writer.add_scalar('Loss/test', val_loss, i)
                writer.add_scalar('Accuracy/test', val_acc, i)
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

    val_loss, val_acc = check_loss_and_acc(dkn, test_dataset)
    writer.add_scalar('Loss/test', val_loss, Config.num_batches)
    writer.add_scalar('Accuracy/test', val_acc, Config.num_batches)
    print(
        f"Final result on test dataset, validation loss: {val_loss:.6f}, validation accuracy: {val_acc:.6f}"
    )
    val_loss, val_acc = check_loss_and_acc(dkn, train_dataset)
    print(
        f"Final result on train dataset, validation loss: {val_loss:.6f}, validation accuracy: {val_acc:.6f}"
    )
    val_loss, val_acc = check_loss_and_acc(dkn, dataset)
    print(
        f"Final result on full dataset, validation loss: {val_loss:.6f}, validation accuracy: {val_acc:.6f}"
    )
    writer.close()


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
        y_pred = model(minibatch["candidate_news"], minibatch["clicked_news"])
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
