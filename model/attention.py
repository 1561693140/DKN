import torch
import torch.nn as nn
import torch.nn.functional as F


class Attention(torch.nn.Module):
    """
    Attention Net.
    Input embedding vectors (produced by KCNN) of a candidate news and all of user's clicked news,
    produce final user embedding vectors with respect to the candidate news.
    """
    def __init__(self, config):
        super(Attention, self).__init__()
        self.config = config
        # TODO parameters
        self.dnn = nn.Sequential(
            nn.Linear(
                len(self.config.window_sizes) * 2 *
                self.config.filter_out_channels, 32), nn.Linear(32, 1))

    def forward(self, candidate_news_vector, clicked_news_vector):
        """
        Args:
          candidate_news_vector: batch_size, (len(window_sizes) * filter_out_channels)
          clicked_news_vector: num_clicked_news_a_user, batch_size, (len(window_sizes) * filter_out_channels)
        Returns:
          batch_size, (len(window_sizes) * filter_out_channels)
        """
        # batch_size, num_clicked_news_a_user
        clicked_news_weights = F.softmax(torch.stack([
            self.dnn(torch.cat(
                (x, candidate_news_vector), dim=1)).squeeze(dim=1)
            for x in clicked_news_vector
        ],
                                                     dim=1),
                                         dim=1)
        # batch_size, (len(window_sizes) * filter_out_channels)
        user_vector = torch.bmm(clicked_news_weights.unsqueeze(1),
                                clicked_news_vector.transpose(0, 1)).squeeze(1)
        return user_vector
